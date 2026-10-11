"""
Vidhik Retrieval Result Models & Provenance Data Structures
===========================================================
Defines typed models for individual retrieval branch results (dense, BM25)
and fused hybrid retrieval candidates preserving complete provenance metadata.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List


@dataclass
class RetrievalResult:
    """
    Standard result returned by an individual retrieval branch (dense or BM25).
    """
    chunk_id: str
    document_id: str
    score: float
    retrieval_method: str  # "dense" or "bm25"
    text: str
    qdrant_point_id: str = ""
    rank: int = 1
    source: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "score": self.score,
            "retrieval_method": self.retrieval_method,
            "text": self.text,
            "qdrant_point_id": self.qdrant_point_id,
            "rank": self.rank,
            "source": self.source,
            "metadata": self.metadata,
        }


@dataclass
class HybridRetrievalResult:
    """
    Final hybrid candidate after Reciprocal Rank Fusion (RRF).
    Preserves all provenance attributes required by the downstream Evidence / RAG stage.
    """
    chunk_id: str
    document_id: str
    qdrant_point_id: str
    text: str
    rrf_score: float
    rrf_rank: int

    # RRF source details
    dense_score: Optional[float] = None
    dense_rank: Optional[int] = None
    bm25_score: Optional[float] = None
    bm25_rank: Optional[int] = None

    # Provenance metadata
    court_level: str = "Unknown"
    court: str = "Unknown"
    case_title: str = "Unknown"
    case_number: str = "Unknown"
    decision_date: str = "Unknown"
    year: Optional[int] = None
    judges: Optional[str] = None
    document_type: Optional[str] = None
    language: str = "en"
    source_file: str = ""
    document_sha256: str = ""

    # Structural provenance
    page_start: int = 1
    page_end: int = 1
    paragraph_start: str = ""
    paragraph_end: str = ""
    sentence_start: str = ""
    sentence_end: str = ""
    token_count: int = 0
    sentence_ids: List[str] = field(default_factory=list)
    paragraph_ids: List[str] = field(default_factory=list)

    # Full raw payload preservation
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Retrieval mode indicators
    retrieval_mode: str = "hybrid"
    degraded: bool = False
    degraded_reason: Optional[str] = None

    @property
    def chunk_text(self) -> str:
        """Alias for text content."""
        return self.text

    @property
    def source(self) -> str:
        """Convenience display source."""
        return f"{self.court_level} - {self.court}"

    @property
    def page_number(self) -> str:
        """Single or range page string."""
        if self.page_start == self.page_end:
            return str(self.page_start)
        return f"{self.page_start}-{self.page_end}"

    @property
    def paragraph_id(self) -> str:
        """Single or range paragraph string."""
        if not self.paragraph_start:
            return ""
        if self.paragraph_start == self.paragraph_end or not self.paragraph_end:
            return str(self.paragraph_start)
        return f"{self.paragraph_start} to {self.paragraph_end}"

    @property
    def sentence_id(self) -> str:
        """Single or range sentence string."""
        if not self.sentence_start:
            return ""
        if self.sentence_start == self.sentence_end or not self.sentence_end:
            return str(self.sentence_start)
        return f"{self.sentence_start} to {self.sentence_end}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to a serializable dictionary."""
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "qdrant_point_id": self.qdrant_point_id,
            "text": self.text,
            "chunk_text": self.chunk_text,
            "rrf_score": self.rrf_score,
            "rrf_rank": self.rrf_rank,
            "dense_score": self.dense_score,
            "dense_rank": self.dense_rank,
            "bm25_score": self.bm25_score,
            "bm25_rank": self.bm25_rank,
            "court_level": self.court_level,
            "court": self.court,
            "case_title": self.case_title,
            "case_number": self.case_number,
            "decision_date": self.decision_date,
            "year": self.year,
            "judges": self.judges,
            "document_type": self.document_type,
            "language": self.language,
            "source_file": self.source_file,
            "document_sha256": self.document_sha256,
            "page_start": self.page_start,
            "page_end": self.page_end,
            "page_number": self.page_number,
            "paragraph_start": self.paragraph_start,
            "paragraph_end": self.paragraph_end,
            "paragraph_id": self.paragraph_id,
            "sentence_start": self.sentence_start,
            "sentence_end": self.sentence_end,
            "sentence_id": self.sentence_id,
            "token_count": self.token_count,
            "sentence_ids": self.sentence_ids,
            "paragraph_ids": self.paragraph_ids,
            "retrieval_mode": self.retrieval_mode,
            "degraded": self.degraded,
            "degraded_reason": self.degraded_reason,
            "metadata": self.metadata,
        }
