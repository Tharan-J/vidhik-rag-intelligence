/**
 * Server-Side AI Request Classifier & Router
 * ===========================================
 * Strictly directs lawyer requests to the appropriate engine:
 * 1. Matter / Document Workspace Assistance -> Gemini 3.5 Flash Lite
 * 2. Substantive Legal Research & Authorities -> Existing Vidhik RAG Pipeline
 * 3. Multilingual Legal Translation -> Existing IndicTrans2 Pipeline
 */

export type AIRequestCategory =
  | "matter_workspace"
  | "legal_research"
  | "translation";

export interface ClassificationResult {
  category: AIRequestCategory;
  engine: "gemini-3.5-flash-lite" | "vidhik-rag-bge-m3-bm25-qdrant" | "indictrans2";
  confidence: number;
  reason: string;
}

/**
 * Deterministic semantic classifier distinguishing workspace questions from
 * authoritative legal research queries and translation requests.
 */
export function classifyLawyerRequest(query: string): ClassificationResult {
  const q = query.toLowerCase().trim();

  // 1. Translation triggers
  const translationTriggers = [
    "translate",
    "translation",
    "in tamil",
    "in hindi",
    "in kannada",
    "in marathi",
    "indictrans",
    "tamil translation",
    "hindi translation",
  ];
  if (translationTriggers.some((t) => q.includes(t))) {
    return {
      category: "translation",
      engine: "indictrans2",
      confidence: 0.98,
      reason:
        "Query requests multilingual translation. Routed strictly to Vidhik's IndicTrans2 entity-protected pipeline.",
    };
  }

  // 2. Substantive Legal Research triggers
  const legalResearchTriggers = [
    "judgment",
    "judgments",
    "authority",
    "authorities",
    "precedent",
    "precedents",
    "supreme court",
    "high court",
    "article 141",
    "article 136",
    "ratio decidendi",
    "case law",
    "limitation period",
    "section 5",
    "section 29",
    "section 116a",
    "section 34",
    "maintainable",
    "statutory bar",
    "condonation",
    "finding of law",
    "legal principle",
    "holding",
    "cite",
    "citation",
    "does the limitation objection apply",
    "find cases",
  ];

  const isLegalResearch = legalResearchTriggers.some((trigger) => q.includes(trigger));

  // 3. Matter / Workspace Assistance triggers
  const matterWorkspaceTriggers = [
    "summarize this matter",
    "summary of the matter",
    "what are the key dates",
    "list the parties",
    "when is the next hearing",
    "organize notes",
    "documents added",
    "what documents",
    "what is the case number",
    "extract dates",
    "timeline of this case",
    "who is the respondent",
    "who is the petitioner",
    "what changed",
    "structure these notes",
  ];

  const isWorkspaceQuery = matterWorkspaceTriggers.some((trigger) => q.includes(trigger));

  // If explicitly about workspace or documents in this matter without asking for external law
  if (isWorkspaceQuery && !q.includes("supreme court") && !q.includes("precedent") && !q.includes("find authorities")) {
    return {
      category: "matter_workspace",
      engine: "gemini-3.5-flash-lite",
      confidence: 0.95,
      reason:
        "Matter organization / workspace question. Processed via auxiliary Gemini 3.5 Flash Lite.",
    };
  }

  // Any substantive legal query, case lookup, or citation search must use existing RAG
  if (isLegalResearch) {
    return {
      category: "legal_research",
      engine: "vidhik-rag-bge-m3-bm25-qdrant",
      confidence: 0.96,
      reason:
        "Substantive legal research query. Routed to Vidhik's hybrid BGE-M3 + BM25 + Qdrant + local Qwen RAG pipeline.",
    };
  }

  // Default to matter workspace if general context assistance
  return {
    category: "matter_workspace",
    engine: "gemini-3.5-flash-lite",
    confidence: 0.85,
    reason:
      "General matter workspace interaction handled via Gemini auxiliary layer.",
  };
}
