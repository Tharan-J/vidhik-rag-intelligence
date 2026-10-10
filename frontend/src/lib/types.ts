/**
 * Vidhik Legal Research System - TypeScript Types
 * Matches the FastAPI Backend response schema from prototype/api/schemas.py
 */

export type ClaimSupportLevel =
  | "directly_supports"
  | "relevant_context"
  | "contradicts_or_qualifies"
  | "unrelated"
  | "unverified";

export type ClaimType =
  | "judicial_finding"
  | "statutory_provision"
  | "party_submission"
  | "procedural_history"
  | "legal_interpretation";

export interface CitationAuthority {
  evidence_id: string;
  court: string;
  court_level: string;
  case_title: string;
  case_number: string;
  decision_date: string;
  page_number: string;
  paragraph_id: string;
  document_id: string;
  chunk_id: string;
  verification_status?: string;
  verified_page?: number;
  verified_paragraph?: string;
  is_source_verified?: boolean;
}

export interface Claim {
  claim: string;
  evidence_ids: string[];
  authorities: CitationAuthority[];
  is_grounded: boolean;
  claim_type?: ClaimType;
  support_level?: ClaimSupportLevel;
  qualification?: string;
  citation_verified?: boolean;
  verification_status?: string;
  verification_details?: Record<string, any>;
}

export interface ContraryEvidenceItem {
  evidence_id: string;
  nature: "contradiction" | "qualification" | "distinction" | string;
  explanation: string;
  authority?: CitationAuthority | EvidenceItem;
}

export interface EvidenceItem {
  evidence_id: string;
  court: string;
  court_level: string;
  case_title: string;
  case_number: string;
  decision_date: string;
  page_start: number;
  page_end: number;
  page_number?: string;
  paragraph_start?: string;
  paragraph_end?: string;
  paragraph_id?: string;
  sentence_id?: string;
  source_file: string;
  chunk_id: string;
  qdrant_point_id: string;
  text: string;
  rrf_score?: number;
  rrf_rank?: number;
  score?: number;
  document_id?: string;
  relevanceCategory?: "DIRECT_EVIDENCE" | "SUPPORTING_CONTEXT" | "CONTRARY_OR_QUALIFYING" | "IRRELEVANT" | "INSUFFICIENT";
  relevanceReason?: string;
  target_matches?: string[];
  relevantExcerpt?: string;
  verification_status?: string;
  verified_page?: number;
  verified_paragraph?: string;
  is_source_verified?: boolean;
}

export type ConfidenceLevel = "supported" | "partially_supported" | "insufficient_evidence";

export interface LegalQueryResponse {
  query: string;
  answer: string;
  claims: Claim[];
  evidence: EvidenceItem[];
  contrary_evidence?: ContraryEvidenceItem[];
  limitations: string;
  confidence: ConfidenceLevel;
  retrievalStatus?: "SUCCESS" | "NOT_FOUND" | "INSUFFICIENT_RELEVANCE";
  grounded?: boolean;
  targetProvisions?: string[];
  rejectedAuthorities?: Array<{
    document_id?: string;
    case_title?: string;
    title?: string;
    court?: string;
    reason?: string;
    detectedProvisions?: string[];
  }>;
  retrieval_count: number;
  evidence_count: number;
  execution_time_seconds: number;
  source?: string;
}

export interface ComponentStatus {
  status: "ok" | "degraded" | "unavailable";
  details?: Record<string, any>;
}

export interface SystemStatusResponse {
  status: "ready" | "degraded" | "unavailable";
  components: {
    qdrant?: ComponentStatus;
    bm25?: ComponentStatus;
    embedding_engine?: ComponentStatus;
    generator?: ComponentStatus;
  };
  timestamp: string;
  service: string;
  version: string;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  service: string;
  version: string;
}

export interface LegalQueryRequest {
  query: string;
  top_k?: number;
  max_evidence?: number;
}
