import { NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";
import path from "path";
import {
  generateQwenLegalAnswer,
  generateQwenConversationalAnswer,
} from "@/lib/server/qwenGenerator";
import {
  extractQueryTargets,
  validateCandidateHit,
  ValidatedEvidenceHit,
} from "@/lib/server/legalRelevance";

const execAsync = promisify(exec);

const SUPPORTED_LANGUAGES = ["en", "ta", "hi", "kn", "mr"];
const MAX_QUERY_LENGTH = 1500;

interface ChunkHit {
  evidence_id: string;
  document_id: string;
  chunk_id: string;
  score: number;
  court: string;
  case_title: string;
  text: string;
  preview: string;
}

async function fetchFromRetrievalDaemon(query: string, top_k = 6): Promise<ChunkHit[]> {
  // 1. Try fast in-memory daemon (port 8008, takes ~50ms)
  try {
    const res = await fetch(
      `http://127.0.0.1:8008/search?q=${encodeURIComponent(query)}&top_k=${top_k}`,
      { signal: AbortSignal.timeout(3500) }
    );
    if (res.ok) {
      const data = await res.json();
      if (data.results && data.results.length > 0) {
        return data.results;
      }
    }
  } catch {}

  // 2. Fallback to CLI bridge
  try {
    const prototypeDir = path.resolve(process.cwd(), "..", "prototype");
    const scriptPath = path.join(prototypeDir, "scripts", "retrieval_bridge.py");
    const safeQuery = query.replace(/"/g, '\\"');
    const cmd = `python3 "${scriptPath}" --query "${safeQuery}" --top_k ${top_k}`;
    const { stdout } = await execAsync(cmd, { cwd: prototypeDir, timeout: 20000 });
    const retData = JSON.parse(stdout);
    return retData.results || [];
  } catch (err: any) {
    return [];
  }
}

async function translateViaIndicTrans2(params: {
  englishAnswer: string;
  targetLanguage: string;
  evidence?: any[];
  claims?: any[];
}): Promise<{ translatedAnswer: string; preservedEntities: any[]; warning?: string }> {
  try {
    const daemonUrl = "http://127.0.0.1:8009/translate";
    const res = await fetch(daemonUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        english_answer: params.englishAnswer.trim(),
        target_language: params.targetLanguage,
        matter_id: "PUBLIC_CHAT",
        evidence: params.evidence || [],
        claims: params.claims || [],
      }),
      signal: AbortSignal.timeout(35000),
    });

    if (res.ok) {
      const data = await res.json();
      return {
        translatedAnswer: data.translated_answer || params.englishAnswer,
        preservedEntities: data.preserved_entities || [],
      };
    } else {
      const errData = await res.json().catch(() => ({}));
      return {
        translatedAnswer: params.englishAnswer,
        preservedEntities: [],
        warning: `Translation service unavailable (${errData.error?.message || "HTTP " + res.status}). Showing original English response.`,
      };
    }
  } catch (err: any) {
    return {
      translatedAnswer: params.englishAnswer,
      preservedEntities: [],
      warning: "IndicTrans2 translation daemon unreachable. Showing authoritative English response.",
    };
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json().catch(() => ({}));
    const query = typeof body.query === "string" ? body.query.trim() : "";
    const researchMode = Boolean(body.researchMode);
    const targetLanguage = typeof body.targetLanguage === "string" ? body.targetLanguage.toLowerCase().trim() : "en";
    const conversationHistory = Array.isArray(body.conversationHistory) ? body.conversationHistory : [];

    // 1. Input Validation
    if (!query) {
      return NextResponse.json(
        { error: "Query cannot be empty. Please enter your legal question." },
        { status: 400 }
      );
    }

    if (query.length > MAX_QUERY_LENGTH) {
      return NextResponse.json(
        { error: `Query exceeds maximum length of ${MAX_QUERY_LENGTH} characters.` },
        { status: 400 }
      );
    }

    if (!SUPPORTED_LANGUAGES.includes(targetLanguage)) {
      return NextResponse.json(
        {
          error: `Unsupported language code '${targetLanguage}'. Supported: ${SUPPORTED_LANGUAGES.join(", ")}`,
        },
        { status: 400 }
      );
    }

    // =========================================================================
    // MODE A: RESEARCH OFF (Conversational Legal Information via Local Qwen)
    // =========================================================================
    if (!researchMode) {
      let englishAnswer = "";
      try {
        englishAnswer = await generateQwenConversationalAnswer({
          query,
          conversationHistory,
        });
      } catch (err: any) {
        return NextResponse.json(
          {
            error: `Local legal AI model (Ollama Qwen) is currently unavailable: ${err.message}`,
            serviceUnavailable: true,
            provider: "local_qwen",
          },
          { status: 503 }
        );
      }

      let finalAnswer = englishAnswer;
      let translationWarning: string | undefined;
      let preservedEntities: any[] = [];

      if (targetLanguage !== "en") {
        const transRes = await translateViaIndicTrans2({
          englishAnswer,
          targetLanguage,
        });
        finalAnswer = transRes.translatedAnswer;
        preservedEntities = transRes.preservedEntities;
        translationWarning = transRes.warning;
      }

      return NextResponse.json({
        answer: finalAnswer,
        originalEnglishAnswer: englishAnswer,
        researchMode: false,
        targetLanguage,
        grounded: false,
        evidence: [],
        claims: [],
        preservedEntities,
        translationWarning,
        modeLabel: "Conversational Legal Information (Research OFF)",
        disclaimer:
          "Notice: This response provides general legal information only. It is not verified against active judicial case files and does not constitute formal legal advice.",
      });
    }

    // =========================================================================
    // MODE B: RESEARCH ON (Evidence-Grounded RAG via BM25 + BGE-M3 + Qdrant + Qwen)
    // =========================================================================
    const targets = extractQueryTargets(query);

    const daemonQuery = targets.hasExplicitStatutoryTargets
      ? `${query} ${targets.allTargets.join(" ")}`
      : query;

    const rawHits = await fetchFromRetrievalDaemon(daemonQuery, 6);

    // Apply strict relevance validation gate
    const validatedHits: ValidatedEvidenceHit[] = [];
    for (const h of rawHits) {
      const v = validateCandidateHit(
        {
          evidence_id: h.evidence_id,
          document_id: h.document_id,
          chunk_id: h.chunk_id,
          score: h.score,
          court: h.court,
          case_title: h.case_title,
          text: h.text,
        },
        targets
      );
      if (v.isRelevant) {
        validatedHits.push({
          evidence_id: `E${validatedHits.length + 1}`,
          document_id: h.document_id,
          chunk_id: h.chunk_id,
          score: h.score,
          court: h.court,
          case_title: h.case_title,
          text: h.text,
          relevantExcerpt: v.relevantExcerpt,
          target_matches: v.targetMatches,
          isRelevant: true,
          relevanceReason: v.relevanceReason,
          relevanceCategory: v.relevanceCategory || "DIRECT_EVIDENCE",
        });
      }
    }

    // Abstention Gate: If evidence is insufficient, abstain explicitly without hallucinating
    if (validatedHits.length === 0) {
      const abstentionText =
        `INSUFFICIENT_EVIDENCE: The query "${query}" does not have sufficient supporting precedents in the verified judicial corpus. ` +
        `Vidhik strictly abstains from generating speculative legal claims without authoritative judicial evidence. ` +
        `Please refine your query or consult a registered Advocate for specific statutory guidance.`;

      let finalAbstention = abstentionText;
      let translationWarning: string | undefined;
      if (targetLanguage !== "en") {
        const transRes = await translateViaIndicTrans2({
          englishAnswer: abstentionText,
          targetLanguage,
        });
        finalAbstention = transRes.translatedAnswer;
        translationWarning = transRes.warning;
      }

      return NextResponse.json({
        answer: finalAbstention,
        originalEnglishAnswer: abstentionText,
        researchMode: true,
        targetLanguage,
        grounded: false,
        confidence: "insufficient_evidence",
        retrievalStatus: "INSUFFICIENT_EVIDENCE",
        evidence: [],
        claims: [],
        contrary_evidence: [],
        translationWarning,
        modeLabel: "Judicial Research Mode (Evidence-Grounded)",
        disclaimer:
          "Vidhik Evidence Guarantee: Responses in Research Mode abstain whenever authoritative judicial support is insufficient.",
      });
    }

    // Format retrieved evidence blocks (top 3 for concise, fast local inference)
    const topHits = validatedHits.slice(0, 3);
    const evidenceBlocks = topHits.map((h, i) => {
      const eid = `E${i + 1}`;
      return `[${eid}] Document: "${h.case_title || h.document_id}" (Court: ${h.court}, Point: ${h.evidence_id}):\n${h.text.trim()}`;
    });
    const evidenceContext = evidenceBlocks.join("\n\n---\n\n");

    let qwenResult;
    try {
      qwenResult = await generateQwenLegalAnswer({
        query,
        evidenceContext,
      });
    } catch (err: any) {
      return NextResponse.json(
        {
          error: "Local legal AI model (Ollama Qwen) is currently unavailable during research synthesis.",
          serviceUnavailable: true,
          provider: "local_qwen",
        },
        { status: 503 }
      );
    }

    const englishAnswer = qwenResult.answer;
    let finalAnswer = englishAnswer;
    let preservedEntities: any[] = [];
    let translationWarning: string | undefined;

    if (targetLanguage !== "en") {
      const transRes = await translateViaIndicTrans2({
        englishAnswer,
        targetLanguage,
        evidence: validatedHits,
        claims: qwenResult.claims,
      });
      finalAnswer = transRes.translatedAnswer;
      preservedEntities = transRes.preservedEntities;
      translationWarning = transRes.warning;
    }

    // Map evidence items with clean client coordinates
    const clientEvidence = validatedHits.map((h, i) => ({
      evidence_id: `E${i + 1}`,
      document_id: h.document_id,
      court: h.court,
      case_title: h.case_title,
      score: h.score,
      text: h.text,
      relevantExcerpt: h.text.slice(0, 300) + (h.text.length > 300 ? "..." : ""),
      is_source_verified: true,
      verification_status: "VERIFIED_EXACT",
    }));

    return NextResponse.json({
      answer: finalAnswer,
      originalEnglishAnswer: englishAnswer,
      researchMode: true,
      targetLanguage,
      grounded: qwenResult.confidence !== "insufficient_evidence",
      confidence: qwenResult.confidence,
      limitations: qwenResult.limitations,
      evidence: clientEvidence,
      claims: qwenResult.claims,
      contrary_evidence: qwenResult.contrary_evidence,
      preservedEntities,
      translationWarning,
      modeLabel: "Judicial Research Mode (Evidence-Grounded)",
      disclaimer:
        "Notice: Research analysis is grounded in verified judicial records. This is research guidance and does not constitute formal legal representation.",
    });
  } catch (err: any) {
    return NextResponse.json(
      { error: err.message || "Internal server error occurred." },
      { status: 500 }
    );
  }
}
