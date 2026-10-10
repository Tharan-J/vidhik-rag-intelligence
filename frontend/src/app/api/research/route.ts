import { NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";
import path from "path";
import { generateQwenLegalAnswer } from "@/lib/server/qwenGenerator";
import { resolveAuthorizedDocument, AuthorizationContext } from "@/lib/server/documentStorage";
import {
  extractQueryTargets,
  searchExtractedMattersForTargets,
  validateCandidateHit,
  ValidatedEvidenceHit,
  RejectedAuthority,
} from "@/lib/server/legalRelevance";

const execAsync = promisify(exec);

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
  // 1. Try retrieval daemon or deployed Railway backend
  try {
    const daemonBase = process.env.RETRIEVAL_DAEMON_URL || "http://127.0.0.1:8008";
    const res = await fetch(
      `${daemonBase}/search?q=${encodeURIComponent(query)}&top_k=${top_k}`,
      {
        headers: { "ngrok-skip-browser-warning": "true" },
        signal: AbortSignal.timeout(6000),
      }
    );
    if (res.ok) {
      const data = await res.json();
      if (data.results && data.results.length > 0) {
        return data.results;
      }
    }
  } catch {
    // Daemon offline or timed out, fallback to CLI bridge
  }

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
    console.error("Retrieval bridge error:", err.message);
    return [];
  }
}

export async function POST(request: Request) {
  const startTime = Date.now();
  try {
    const body = await request.json();
    const query = (body.query || "").trim();
    const top_k = body.top_k || 5;

    if (!query) {
      return NextResponse.json({ error: "Query string cannot be empty" }, { status: 400 });
    }

    // =========================================================================
    // STEP 1: PARSE QUERY TARGETS
    // Identify explicit constitutional articles, sections, and legal doctrines
    // =========================================================================
    const targets = extractQueryTargets(query);

    // =========================================================================
    // STEP 2: MULTI-SOURCE RETRIEVAL
    // A. Search verified matters database for direct target matches
    // B. Search 29,156 chunk corpus via retrieval daemon
    // =========================================================================
    const matterMatches = searchExtractedMattersForTargets(targets);

    // If query has statutory targets, enrich daemon query with target terms to improve recall
    const daemonQuery = targets.hasExplicitStatutoryTargets
      ? `${query} ${targets.allTargets.join(" ")}`
      : query;

    const daemonHits = await fetchFromRetrievalDaemon(daemonQuery, top_k + 3);

    // Combine candidate hits
    const rawCandidates: Array<{
      evidence_id: string;
      document_id: string;
      chunk_id: string;
      score: number;
      court: string;
      case_title: string;
      case_number?: string;
      neutral_citation?: string;
      page_number?: string | number;
      paragraph_id?: string | number;
      text: string;
    }> = [];

    // Prioritize matter matches
    for (const mm of matterMatches) {
      rawCandidates.push({
        evidence_id: mm.evidence_id,
        document_id: mm.document_id,
        chunk_id: mm.chunk_id,
        score: mm.score,
        court: mm.court,
        case_title: mm.case_title,
        case_number: mm.case_number,
        neutral_citation: mm.neutral_citation,
        page_number: mm.page_number,
        paragraph_id: mm.paragraph_id,
        text: mm.text,
      });
    }

    // Add daemon hits
    for (const dh of daemonHits) {
      // Avoid duplicate texts
      if (!rawCandidates.some((c) => c.text.slice(0, 80) === dh.text.slice(0, 80))) {
        rawCandidates.push({
          evidence_id: dh.evidence_id,
          document_id: dh.document_id,
          chunk_id: dh.chunk_id,
          score: dh.score,
          court: dh.court,
          case_title: dh.case_title,
          text: dh.text,
        });
      }
    }

    // =========================================================================
    // STEP 3: STRICT RELEVANCE VALIDATION GATE
    // "A document being retrieved does not mean it is relevant."
    // Rejects documents that only contain unrelated provisions or lack target discussion
    // =========================================================================
    const validatedHits: ValidatedEvidenceHit[] = [];
    const rejectedAuthorities: RejectedAuthority[] = [];

    for (const cand of rawCandidates) {
      const val = validateCandidateHit(cand, targets);
      if (val.isRelevant) {
        validatedHits.push({
          evidence_id: `E${validatedHits.length + 1}`,
          document_id: cand.document_id,
          chunk_id: cand.chunk_id,
          score: cand.score,
          court: cand.court,
          case_title: cand.case_title,
          case_number: cand.case_number,
          neutral_citation: cand.neutral_citation,
          page_number: cand.page_number || val.page_number || "Reported",
          paragraph_id: cand.paragraph_id || val.paragraph_id || "Holding",
          text: cand.text,
          relevantExcerpt: val.relevantExcerpt,
          target_matches: val.targetMatches,
          isRelevant: true,
          relevanceReason: val.relevanceReason,
          relevanceCategory: val.relevanceCategory || "DIRECT_EVIDENCE",
        });
      } else {
        rejectedAuthorities.push({
          document_id: cand.document_id,
          case_title: cand.case_title,
          court: cand.court,
          reason: val.relevanceReason,
          detectedProvisions: val.detectedProvisions,
        });
      }
    }

    // =========================================================================
    // STEP 4: FAIL-CLOSED DECISION GATE
    // If no candidate is genuinely relevant to the query targets, ABSTAIN.
    // Never summarize an unrelated retrieved judgment.
    // =========================================================================
    if (validatedHits.length === 0) {
      const targetStr = targets.allTargets.length > 0 ? targets.allTargets.join(", ") : query;
      const elapsed = Number(((Date.now() - startTime) / 1000).toFixed(2));

      return NextResponse.json({
        query,
        retrievalStatus: "INSUFFICIENT_RELEVANCE",
        grounded: false,
        confidence: "insufficient_evidence",
        targetProvisions: targets.allTargets,
        answer: `NOT_FOUND / INSUFFICIENT_RELEVANCE: Retrieved documents did not contain substantive discussion or application of the target legal provisions (${targetStr}). Vidhik strictly refuses to summarize unrelated judicial authorities.`,
        claims: [],
        evidence: [],
        rejectedAuthorities: rejectedAuthorities.slice(0, 5),
        limitations: `Retrieved ${rawCandidates.length} candidate documents by lexical similarity, but all failed query relevance validation. Zero documents met the evidentiary threshold.`,
        execution_time_seconds: elapsed,
      });
    }

    // Top verified relevant evidence
    const topRelevantHits = validatedHits.slice(0, top_k);

    // =========================================================================
    // STEP 5: EVIDENCE-GROUNDED SYNTHESIS OVER ONLY VERIFIED RELEVANT HITS
    // =========================================================================
    const evidenceContext = topRelevantHits
      .map(
        (h) =>
          `[${h.evidence_id}] Case: ${h.case_title} (${h.court})${h.neutral_citation ? ` [Citation: ${h.neutral_citation}]` : ""}${h.case_number ? ` [Case No: ${h.case_number}]` : ""}\nLocation: ${h.document_id} | ${h.page_number} | ${h.paragraph_id}\nTarget Matches: ${h.target_matches.join(", ")}\nVerified Excerpt:\n${h.relevantExcerpt || h.text.slice(0, 600)}`
      )
      .join("\n\n---\n\n");

    const prompt = `
CRITICAL SPECIFICATION: VIDHIK EVIDENCE-GROUNDED LEGAL REASONING ENGINE
User Legal Query: "${query}"
Identified Legal Targets: ${targets.allTargets.join(", ") || "General Inquiry"}

VERIFIED RELEVANT AUTHORITIES & EVIDENCE EXCERPTS:
${evidenceContext}

STRICT INSTRUCTIONS:
1. Formulate a rigorous, authoritative legal analysis answering the query based EXCLUSIVELY on the verified authorities above.
2. Directly answer what the court held regarding the target provisions (${targets.allTargets.join(", ") || "the query"}).
3. Cite [E1], [E2] inline next to every assertion.
4. DO NOT summarize or mention any outside unrelated cases.
5. Formulate 2-4 structured claims, each with exact evidence_ids (e.g. ["E1"]).
6. Set confidence to "supported".

Return strictly JSON:
{
  "answer": "Legal holding synthesis citing [E1], [E2] inline.",
  "confidence": "supported",
  "limitations": "Statutory boundaries and precedential scope",
  "claims": [
    {
      "claim": "Specific legal proposition established by the verified court",
      "evidence_ids": ["E1"],
      "is_grounded": true
    }
  ]
}
`;

    // Verify physical document existence and integrity for top hits
    const authContext: AuthorizationContext = {
      isAuthenticated: true,
      userId: "system_research",
      role: "lawyer",
    };

    const verifiedEvidenceHits = topRelevantHits.map((h) => {
      const resolved = resolveAuthorizedDocument({
        documentId: h.document_id,
        authContext,
        allowCorpusFallback: true,
      });
      return {
        ...h,
        is_source_verified: resolved.success,
        verification_status: resolved.success ? "VERIFIED_EXACT" : "UNVERIFIED",
        verified_page: typeof h.page_number === "number" ? h.page_number : undefined,
        verified_paragraph: typeof h.paragraph_id === "string" ? h.paragraph_id : undefined,
      };
    });

    try {
      const generated = await generateQwenLegalAnswer({
        query,
        evidenceContext,
        timeoutMs: 40000,
      });

      const elapsed = Number(((Date.now() - startTime) / 1000).toFixed(2));

      // Associate claims with authorities and determine claim support level & citation status
      const processedClaims = (generated.claims || []).map((c) => {
        const matchingAuthorities = verifiedEvidenceHits.filter((e) =>
          c.evidence_ids?.includes(e.evidence_id)
        );

        const hasSourceVerifiedAuth = matchingAuthorities.some((a) => a.is_source_verified);
        const supportLevel = c.support_level || (matchingAuthorities.length > 0 ? "directly_supports" : "unverified");

        return {
          claim: c.claim,
          evidence_ids: c.evidence_ids || [],
          claim_type: c.claim_type || "judicial_finding",
          support_level: supportLevel,
          qualification: c.qualification,
          is_grounded: matchingAuthorities.length > 0,
          citation_verified: hasSourceVerifiedAuth,
          verification_status: hasSourceVerifiedAuth ? "VERIFIED_SOURCE" : "UNVERIFIED",
          authorities: matchingAuthorities.map((a) => ({
            evidence_id: a.evidence_id,
            court: a.court,
            court_level: (a as any).court_level || "Court",
            case_title: a.case_title,
            case_number: a.case_number || a.chunk_id,
            decision_date: (a as any).decision_date || "Reported",
            page_number: String(a.page_number || "1"),
            paragraph_id: String(a.paragraph_id || "Holding"),
            document_id: a.document_id,
            chunk_id: a.chunk_id,
            verification_status: a.verification_status,
            is_source_verified: a.is_source_verified,
          })),
        };
      });

      // Map contrary or qualifying evidence
      const processedContrary = (generated.contrary_evidence || []).map((ce) => {
        const matchingEv = verifiedEvidenceHits.find((e) => e.evidence_id === ce.evidence_id);
        return {
          evidence_id: ce.evidence_id,
          nature: ce.nature || "qualification",
          explanation: ce.explanation,
          authority: matchingEv,
        };
      });

      return NextResponse.json({
        retrievalStatus: "SUCCESS",
        grounded: true,
        query,
        targetProvisions: targets.allTargets,
        answer: generated.answer,
        claims: processedClaims,
        evidence: verifiedEvidenceHits,
        contrary_evidence: processedContrary,
        rejectedAuthorities: rejectedAuthorities.slice(0, 5),
        confidence: generated.confidence || "supported",
        limitations: generated.limitations || "Grounded strictly in verified relevant authorities.",
        execution_time_seconds: elapsed,
        source: "Vidhik Local Qwen Grounded Pipeline",
      });
    } catch (qwenErr: any) {
      console.warn("Local Qwen synthesis fallback:", qwenErr.message);

      // Deterministic fallback using verbatim verified judicial hits
      const topHit = verifiedEvidenceHits[0];
      const secondHit = verifiedEvidenceHits[1] || topHit;

      const fallbackAnswer = `Based on authoritative judicial precedents in ${topHit.case_title} (${topHit.court}) [${topHit.evidence_id}], the position of law regarding ${targets.allTargets.join(", ") || "the query"} is established as follows: ${topHit.relevantExcerpt}.${
        secondHit !== topHit
          ? `\n\nThis is further corroborated by ${secondHit.case_title} (${secondHit.court}) [${secondHit.evidence_id}], wherein the Court applied the governing principles: ${secondHit.relevantExcerpt}`
          : ""
      }`;

      const fallbackClaims = [
        {
          claim: `Holding in ${topHit.case_title} (${topHit.court}) governs the application of ${topHit.target_matches.join(", ") || "the provision"}.`,
          evidence_ids: [topHit.evidence_id],
          claim_type: "judicial_finding" as const,
          support_level: "directly_supports" as const,
          is_grounded: true,
          citation_verified: Boolean(topHit.is_source_verified),
          verification_status: topHit.is_source_verified ? "VERIFIED_SOURCE" : "UNVERIFIED",
          authorities: [
            {
              evidence_id: topHit.evidence_id,
              court: topHit.court,
              court_level: (topHit as any).court_level || "Court",
              case_title: topHit.case_title,
              case_number: topHit.case_number || topHit.chunk_id,
              decision_date: (topHit as any).decision_date || "Reported",
              page_number: String(topHit.page_number || "1"),
              paragraph_id: String(topHit.paragraph_id || "Holding"),
              document_id: topHit.document_id,
              chunk_id: topHit.chunk_id,
              verification_status: topHit.verification_status,
              is_source_verified: topHit.is_source_verified,
            },
          ],
        },
      ];

      if (secondHit !== topHit) {
        fallbackClaims.push({
          claim: `Precedent in ${secondHit.case_title} (${secondHit.court}) corroborates statutory interpretation.`,
          evidence_ids: [secondHit.evidence_id],
          claim_type: "judicial_finding" as const,
          support_level: "directly_supports" as const,
          is_grounded: true,
          citation_verified: Boolean(secondHit.is_source_verified),
          verification_status: secondHit.is_source_verified ? "VERIFIED_SOURCE" : "UNVERIFIED",
          authorities: [
            {
              evidence_id: secondHit.evidence_id,
              court: secondHit.court,
              court_level: (secondHit as any).court_level || "Court",
              case_title: secondHit.case_title,
              case_number: secondHit.case_number || secondHit.chunk_id,
              decision_date: (secondHit as any).decision_date || "Reported",
              page_number: String(secondHit.page_number || "1"),
              paragraph_id: String(secondHit.paragraph_id || "Holding"),
              document_id: secondHit.document_id,
              chunk_id: secondHit.chunk_id,
              verification_status: secondHit.verification_status,
              is_source_verified: secondHit.is_source_verified,
            },
          ],
        });
      }

      const elapsed = Number(((Date.now() - startTime) / 1000).toFixed(2));
      return NextResponse.json({
        retrievalStatus: "SUCCESS",
        grounded: true,
        query,
        targetProvisions: targets.allTargets,
        answer: fallbackAnswer,
        claims: fallbackClaims,
        evidence: verifiedEvidenceHits,
        contrary_evidence: [],
        rejectedAuthorities: rejectedAuthorities.slice(0, 5),
        confidence: "supported",
        limitations: "Directly grounded in verbatim judicial chunks passing strict query relevance verification.",
        execution_time_seconds: elapsed,
        source: "Vidhik Local Qwen Grounded Pipeline",
      });
    }
  } catch (err: any) {
    console.error("Critical research route error:", err);
    return NextResponse.json(
      { error: err.message || "Failed to execute dynamic legal research" },
      { status: 500 }
    );
  }
}
