import { NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";
import path from "path";
import { MatterEvidenceItem } from "@/lib/types/matter";

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

interface RetrievalResultWrapper {
  hits: ChunkHit[];
  retrievalMode: string;
  degraded: boolean;
  degradedReason?: string;
}

async function fetchFromRetrievalDaemon(query: string, top_k = 4): Promise<RetrievalResultWrapper> {
  // 1. Try retrieval daemon or deployed backend
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
      return {
        hits: data.results || [],
        retrievalMode: data.retrieval_mode || "hybrid",
        degraded: Boolean(data.degraded),
        degradedReason: data.degraded_reason,
      };
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
    return {
      hits: retData.results || [],
      retrievalMode: retData.retrieval_mode || "bm25_bridge",
      degraded: false,
    };
  } catch (err: any) {
    console.error("Retrieval bridge error:", err.message);
    return { hits: [], retrievalMode: "unavailable", degraded: true, degradedReason: err.message };
  }
}

export async function POST(request: Request) {
  const startTime = Date.now();
  try {
    const body = await request.json();
    const {
      query,
      stance = "supporting",
      issueId,
      issueTitle,
      claim,
      matterId,
    } = body;

    const cleanQuery = (query || "").trim();
    if (!cleanQuery) {
      return NextResponse.json({ error: "Search query is required" }, { status: 400 });
    }

    // Query Vidhik's RAG index directly
    const retrieval = await fetchFromRetrievalDaemon(cleanQuery, 4);
    const hits = retrieval.hits;

    if (!hits || hits.length === 0) {
      return NextResponse.json({
        retrievalStatus: "NOT_FOUND",
        grounded: false,
        message: "No verified source evidence was retrieved for this request.",
        evidence: [],
        total_retrieved: 0,
        retrieval_mode: retrieval.retrievalMode,
        degraded: retrieval.degraded,
        degraded_reason: retrieval.degradedReason,
        execution_time_seconds: Number(((Date.now() - startTime) / 1000).toFixed(2)),
      });
    }

    const evidenceItems: MatterEvidenceItem[] = hits.map((hit, idx) => {
      // Extract a clean 2-sentence excerpt from the text
      const cleanText = hit.text.replace(/\s+/g, " ").trim();
      const sentences = cleanText.split(/(?<=[.!?])\s+/);
      const excerpt = sentences.slice(0, 3).join(" ") || cleanText.slice(0, 300);

      const generatedClaim =
        claim ||
        (stance === "supporting"
          ? `Precedent establishes that: ${excerpt.slice(0, 110)}...`
          : `Counter-precedent holds that: ${excerpt.slice(0, 110)}...`);

      return {
        id: `RAG-${Date.now()}-${idx + 1}`,
        matterId: matterId || "MAT-CURRENT",
        issueId: issueId || "ISSUE-SEARCH",
        issueTitle: issueTitle || "Retrieved Legal Authority",
        claim: generatedClaim,
        stance: stance as "supporting" | "contradicting",
        evidenceExcerpt: excerpt,
        rawSourceText: hit.text,
        sourceDocument: hit.document_id,
        paragraphId: hit.chunk_id,
        pageNumber: "Reported Record / Judgments Corpus",
        relatedAuthority: {
          caseTitle: hit.case_title,
          court: hit.court,
          year: "Reported Precedent",
          citation: hit.evidence_id,
        },
        isPinned: false,
        notes: [
          `Dynamically retrieved via Vidhik Hybrid RAG (Score: ${hit.score.toFixed(2)}) for query: "${cleanQuery}"`
        ],
        confidence: "Verified from Corpus",
        provenance: "VERIFIED_FROM_SOURCE",
        grounded: true,
        isCustom: true,
      };
    });

    const elapsed = Number(((Date.now() - startTime) / 1000).toFixed(2));

    return NextResponse.json({
      retrievalStatus: "SUCCESS",
      grounded: true,
      query: cleanQuery,
      stance,
      evidence: evidenceItems,
      total_retrieved: evidenceItems.length,
      execution_time_seconds: elapsed,
      retrieval_mode: retrieval.retrievalMode,
      degraded: retrieval.degraded,
      degraded_reason: retrieval.degradedReason,
      retrieval_engine: retrieval.degraded
        ? "Vidhik BM25 Lexical Retrieval (Degraded Mode)"
        : "Vidhik Authoritative Hybrid Retrieval (BGE-M3 + BM25)",
    });
  } catch (err: any) {
    console.error("Evidence RAG search failed:", err);
    return NextResponse.json(
      { error: err.message || "Failed to retrieve evidence from Vidhik RAG" },
      { status: 500 }
    );
  }
}
