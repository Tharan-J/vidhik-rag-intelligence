"""
Evidence Selection and Structured Representation Subsystem
===========================================================
Converts ranked hybrid retrieval candidates (HybridRetrievalResult) into a clean,
deduplicated, deterministically numbered legal evidence set (E1, E2, E3, ...)
ready for prompt assembly and citation tracking.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from retrieval.models import HybridRetrievalResult

logger = logging.getLogger("VidhikRAG.Evidence")


@dataclass
class EvidenceItem:
    """
    A single legal evidence unit selected from hybrid retrieval candidates.
    Preserves all provenance attributes and provides a standardized citation ID (e.g. E1).
    """
    evidence_id: str  # "E1", "E2", ...
    document_id: str
    chunk_id: str
    qdrant_point_id: str
    court_level: str
    court: str
    case_title: str
    case_number: str
    decision_date: str
    page_number: str
    paragraph_id: str
    sentence_id: str
    text: str
    rrf_score: float
    rrf_rank: int
    year: Optional[int] = None
    dense_rank: Optional[int] = None
    bm25_rank: Optional[int] = None
    page_start: int = 1
    page_end: int = 1
    paragraph_start: str = ""
    paragraph_end: str = ""
    source_file: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def format_for_prompt(self, index_label: Optional[str] = None) -> str:
        """
        Format the evidence unit for inclusion in Qwen's context prompt.
        Uses stable bracketed headers (e.g. [EVIDENCE 1] or [E1]).
        """
        label = index_label or self.evidence_id
        return (
            f"[{label}]\n"
            f"Court: {self.court} ({self.court_level})\n"
            f"Case: {self.case_title}\n"
            f"Case Number: {self.case_number}\n"
            f"Decision Date: {self.decision_date}\n"
            f"Page: {self.page_number}\n"
            f"Paragraph: {self.paragraph_id}\n"
            f"Source Document: {self.document_id}\n\n"
            f"Text:\n{self.text.strip()}\n"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert evidence item to dictionary representation."""
        return {
            "evidence_id": self.evidence_id,
            "id": self.evidence_id,
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "qdrant_point_id": self.qdrant_point_id,
            "court_level": self.court_level,
            "court": self.court,
            "case_title": self.case_title,
            "case_number": self.case_number,
            "decision_date": self.decision_date,
            "year": self.year,
            "page_start": self.page_start,
            "page_end": self.page_end,
            "page": self.page_number,
            "page_number": self.page_number,
            "paragraph_start": self.paragraph_start,
            "paragraph_end": self.paragraph_end,
            "paragraph": self.paragraph_id,
            "paragraph_id": self.paragraph_id,
            "sentence_id": self.sentence_id,
            "source_file": self.source_file,
            "text": self.text,
            "rrf_score": self.rrf_score,
            "rrf_rank": self.rrf_rank,
            "dense_rank": self.dense_rank,
            "bm25_rank": self.bm25_rank,
            "metadata": self.metadata,
        }


class EvidenceSelector:
    """
    Selects, filters, and formats candidate chunks into a clean evidence set.
    """

    def __init__(
        self,
        max_evidence: int = 8,
        min_rrf_score: float = 0.005,
        deduplicate_by_chunk_id: bool = True,
    ):
        self.max_evidence = max_evidence
        self.min_rrf_score = min_rrf_score
        self.deduplicate_by_chunk_id = deduplicate_by_chunk_id

    def select(
        self,
        candidates: List[HybridRetrievalResult],
        max_evidence: Optional[int] = None,
    ) -> List[EvidenceItem]:
        """
        Filter and deduplicate retrieval candidates into ordered EvidenceItem instances.
        Deterministic ordering matching RRF rank is preserved.
        """
        limit = max_evidence if max_evidence is not None else self.max_evidence
        seen_keys = set()
        selected: List[EvidenceItem] = []

        for item in candidates:
            if item.rrf_score < self.min_rrf_score:
                continue

            # Deduplication key
            if self.deduplicate_by_chunk_id:
                dedup_key = item.qdrant_point_id or f"{item.document_id}_{item.chunk_id}"
                if dedup_key in seen_keys:
                    continue
                seen_keys.add(dedup_key)

            evidence_num = len(selected) + 1
            ev_id = f"E{evidence_num}"

            evidence_item = EvidenceItem(
                evidence_id=ev_id,
                document_id=item.document_id,
                chunk_id=item.chunk_id,
                qdrant_point_id=item.qdrant_point_id,
                court_level=item.court_level,
                court=item.court,
                case_title=item.case_title,
                case_number=item.case_number,
                decision_date=item.decision_date,
                year=item.year,
                page_start=getattr(item, "page_start", 1),
                page_end=getattr(item, "page_end", 1),
                page_number=item.page_number,
                paragraph_start=getattr(item, "paragraph_start", ""),
                paragraph_end=getattr(item, "paragraph_end", ""),
                paragraph_id=item.paragraph_id,
                sentence_id=item.sentence_id,
                source_file=getattr(item, "source_file", ""),
                text=item.text,
                rrf_score=item.rrf_score,
                rrf_rank=item.rrf_rank,
                dense_rank=item.dense_rank,
                bm25_rank=item.bm25_rank,
                metadata=dict(item.metadata),
            )
            selected.append(evidence_item)

            if len(selected) >= limit:
                break

        logger.debug(f"Selected {len(selected)} evidence items from {len(candidates)} candidates.")
        return selected
