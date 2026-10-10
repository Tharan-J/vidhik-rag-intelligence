"""
Pydantic Schemas for Vidhik Legal RAG API
=========================================
Strict, typed request and response definitions for the FastAPI application layer.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator


class LegalQueryRequest(BaseModel):
    """
    Incoming request payload for legal question answering.
    """
    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The legal research question in plain language or legal terminology.",
        json_schema_extra={"example": "What is the limitation period for filing an appeal?"},
    )
    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        le=100,
        description="Optional override for the number of hybrid retrieval candidates to fetch.",
        json_schema_extra={"example": 20},
    )
    max_evidence: Optional[int] = Field(
        default=None,
        ge=1,
        le=20,
        description="Optional override for the maximum evidence chunks to supply to the generator.",
        json_schema_extra={"example": 5},
    )

    @field_validator("query")
    @classmethod
    def validate_non_blank_query(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Query string must not be empty or whitespace only.")
        return clean


class CitationAuthorityResponse(BaseModel):
    """
    Judicial authority resolving an evidence citation back to its official record.
    """
    evidence_id: str = Field(..., description="Evidence ID referenced (e.g. 'E1')")
    court: str = Field(..., description="Court name (e.g. 'Supreme Court of India')")
    court_level: str = Field(..., description="Hierarchy level ('Supreme Court', 'High Court', 'District Court')")
    case_title: str = Field(..., description="Official case title or cause title")
    case_number: str = Field(..., description="Case identifier or citation number")
    decision_date: str = Field(..., description="Date of judgment or order")
    page_number: str = Field(..., description="Page number or range in the certified judgment")
    paragraph_id: str = Field(..., description="Paragraph identifier")
    document_id: str = Field(..., description="Unique document ID in the corpus")
    chunk_id: str = Field(..., description="Unique chunk ID")
    verification_status: str = Field(default="UNVERIFIED", description="Verification status against physical PDF")
    verified_page: Optional[int] = Field(default=None, description="Actual verified page in physical PDF")
    verified_paragraph: Optional[str] = Field(default=None, description="Actual verified paragraph ID")
    is_source_verified: bool = Field(default=False, description="True if verbatim or normalized match verified in source PDF")


class ClaimResponse(BaseModel):
    """
    Substantive legal assertion paired with supporting evidence IDs and authorities.
    """
    claim: str = Field(..., description="Legal or factual proposition asserted by the model.")
    evidence_ids: List[str] = Field(..., description="List of evidence IDs cited (e.g. ['E1', 'E2']).")
    authorities: List[CitationAuthorityResponse] = Field(
        default_factory=list,
        description="Resolved court authorities backing this specific claim.",
    )
    is_grounded: bool = Field(
        default=True,
        description="True if the claim references at least one valid evidence chunk.",
    )
    claim_type: str = Field(
        default="judicial_finding",
        description="Type of assertion: 'judicial_finding', 'statutory_provision', 'party_submission', 'procedural_history', 'legal_interpretation'.",
    )
    support_level: str = Field(
        default="directly_supports",
        description="Semantic support level: 'directly_supports', 'relevant_context', 'contradicts_or_qualifies', 'unrelated', 'unverified'.",
    )
    qualification: Optional[str] = Field(
        default=None,
        description="Optional qualification or limitation if the proposition is partial or conditional.",
    )
    citation_verified: bool = Field(
        default=False,
        description="True if cited passage was physically verified in authentic court PDF.",
    )
    verification_status: str = Field(
        default="UNVERIFIED",
        description="Source verification status (e.g. 'VERIFIED_EXACT', 'VERIFIED_NORMALIZED', 'COORDINATE_MISMATCH').",
    )
    verification_details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Diagnostic details from source verifier.",
    )


class EvidenceItemResponse(BaseModel):
    """
    Preserved evidence item with complete provenance metadata.
    """
    evidence_id: str = Field(..., description="Citation identifier (e.g. 'E1').")
    court: str = Field(..., description="Court name.")
    court_level: str = Field(..., description="Hierarchy level of the court.")
    case_title: str = Field(..., description="Title of the case.")
    case_number: str = Field(..., description="Case or citation number.")
    decision_date: str = Field(..., description="Date of judgment.")
    page_start: int = Field(default=1, description="Starting page in document.")
    page_end: int = Field(default=1, description="Ending page in document.")
    page_number: Optional[str] = Field(default=None, description="Formatted page range (e.g. '30-31').")
    paragraph_start: Optional[str] = Field(default="", description="Starting paragraph ID.")
    paragraph_end: Optional[str] = Field(default="", description="Ending paragraph ID.")
    paragraph_id: Optional[str] = Field(default="", description="Formatted paragraph range.")
    sentence_id: Optional[str] = Field(default="", description="Sentence span identifier.")
    source_file: str = Field(default="", description="Source document filename.")
    document_id: str = Field(default="", description="Unique document ID in the corpus.")
    chunk_id: str = Field(..., description="Unique chunk identifier.")
    qdrant_point_id: str = Field(..., description="Qdrant point ID in vector store.")
    text: str = Field(..., description="Chunk text content.")
    rrf_score: Optional[float] = Field(default=None, description="Reciprocal Rank Fusion score.")
    rrf_rank: Optional[int] = Field(default=None, description="Rank in hybrid retrieval fusion.")


class ContraryEvidenceResponse(BaseModel):
    """
    Preserved contradictory, qualifying, or dissenting authority.
    """
    evidence_id: str = Field(..., description="Evidence ID of the contrary or qualifying passage.")
    nature: str = Field(..., description="'contradiction', 'qualification', or 'distinction'.")
    explanation: str = Field(..., description="Explanation of the competing proposition or limitation.")


class LegalQueryResponse(BaseModel):
    """
    Standard structured response for Vidhik Legal RAG queries.
    """
    query: str = Field(..., description="The query processed.")
    answer: str = Field(..., description="Comprehensive legal answer grounded exclusively in retrieved evidence.")
    claims: List[ClaimResponse] = Field(..., description="Individual legal claims linked to evidence.")
    evidence: List[EvidenceItemResponse] = Field(..., description="Retrieved and selected evidence chunks.")
    contrary_evidence: List[ContraryEvidenceResponse] = Field(
        default_factory=list,
        description="Preserved contrary or qualifying authorities affecting the proposition.",
    )
    limitations: str = Field(..., description="Disclosed evidentiary limitations or missing legal aspects.")
    confidence: str = Field(
        ...,
        description="Calibrated confidence level: 'supported', 'partially_supported', or 'insufficient_evidence'.",
    )
    retrieval_count: int = Field(..., description="Total candidates retrieved before evidence selection.")
    evidence_count: int = Field(..., description="Total evidence chunks provided to generator.")
    execution_time_seconds: float = Field(..., description="Total pipeline latency in seconds.")


class HealthResponse(BaseModel):
    """
    Lightweight health check response.
    """
    status: str = Field(default="healthy", description="Service health indicator.")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp.")
    service: str = Field(default="vidhik-api", description="Service name.")
    version: str = Field(default="1.0.0", description="API version.")


class ComponentStatus(BaseModel):
    """
    Health/readiness details for an individual backend subsystem.
    """
    status: str = Field(..., description="'ok', 'degraded', or 'unavailable'.")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Subsystem-specific status metadata.")


class SystemStatusResponse(BaseModel):
    """
    Runtime readiness information across all dependencies.
    """
    status: str = Field(..., description="'ready', 'degraded', or 'unavailable'.")
    components: Dict[str, ComponentStatus] = Field(..., description="Subsystem readiness map.")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp.")
    service: str = Field(default="vidhik-api", description="Service name.")
    version: str = Field(default="1.0.0", description="API version.")


class ErrorDetail(BaseModel):
    code: str = Field(..., description="Machine-readable error code.")
    message: str = Field(..., description="Human-readable error description.")
    details: Optional[Any] = Field(default=None, description="Optional diagnostic details.")


class ErrorResponse(BaseModel):
    error: ErrorDetail = Field(..., description="Structured error envelope.")


class LegalTranslationRequest(BaseModel):
    """
    Request payload for translating evidence-grounded legal answers.
    """
    english_answer: str = Field(
        ...,
        min_length=1,
        description="The evidence-grounded English legal answer to be translated.",
    )
    target_language: str = Field(
        ...,
        description="Target Indian language code: 'ta' (Tamil), 'hi' (Hindi), 'kn' (Kannada), or 'mr' (Marathi).",
    )
    matter_id: Optional[str] = Field(
        default="GLOBAL",
        description="Matter workspace identifier for matter-isolated operations.",
    )
    evidence: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list,
        description="Preserved evidence records associated with the answer.",
    )
    claims: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list,
        description="Preserved claim classifications and metadata.",
    )


class LegalTranslationResponse(BaseModel):
    """
    Response payload for verified multilingual legal representation.
    """
    matter_id: str = Field(..., description="Matter identifier.")
    target_language: str = Field(..., description="Target language code.")
    language_name: str = Field(..., description="Target language display name.")
    original_english_answer: str = Field(..., description="Unchanged source English legal answer.")
    translated_answer: str = Field(..., description="Restored and verified Indic translation.")
    raw_translated_text: Optional[str] = Field(default=None, description="Pre-restoration model output.")
    protected_entities_count: int = Field(..., description="Number of legal entities identified and protected.")
    preserved_entities: List[Dict[str, Any]] = Field(..., description="Protected entities inventory.")
    restoration_audit: List[Dict[str, Any]] = Field(..., description="Per-entity restoration audit trail.")
    unresolved_placeholders: List[str] = Field(default_factory=list, description="Any unresolved placeholders.")
    verification: Dict[str, Any] = Field(..., description="Multi-criteria verification report.")
    is_valid: bool = Field(..., description="Overall verification decision.")
    evidence: List[Dict[str, Any]] = Field(default_factory=list, description="Unchanged supporting evidence.")
    claims: List[Dict[str, Any]] = Field(default_factory=list, description="Unchanged claim classifications.")
    latency_seconds: float = Field(..., description="Translation pipeline latency in seconds.")
    output_hash: str = Field(..., description="Cryptographic SHA-256 hash of the translation.")

