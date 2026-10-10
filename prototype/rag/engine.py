"""
High-Level Legal RAG Engine for Vidhik
======================================
Coordinates the complete end-to-end legal generation pipeline:
1. Hybrid retrieval (BGE-M3 Dense + BM25 Lexical + RRF).
2. Evidence filtering and deduplication.
3. Token-budgeted context assembly.
4. Evidence-constrained Qwen generation.
5. Structured JSON schema validation.
6. Claim-to-source provenance chain resolution.
"""

import time
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from retrieval.engine import HybridRetrievalEngine
from .config import RAGConfig, load_rag_config
from .evidence import EvidenceItem, EvidenceSelector
from .context import ContextBuilder, ContextBundle
from .prompt import build_prompts
from .generator import QwenGenerator, RawGenerationOutput
from .provenance import ClaimWithProvenance, ProvenanceResolver

logger = logging.getLogger("VidhikRAG.Engine")


@dataclass
class LegalRAGResponse:
    """
    Standard production response model for Vidhik Legal RAG.
    Contains grounded legal answer, attributed claims, supporting evidence,
    contrary/qualifying evidence, explicit limitations, and calibrated confidence level.
    """
    query: str
    answer: str
    claims: List[ClaimWithProvenance]
    evidence: List[Dict[str, Any]]
    limitations: str
    confidence: str  # "supported" | "partially_supported" | "insufficient_evidence"
    contrary_evidence: List[Dict[str, Any]] = field(default_factory=list)
    retrieval_count: int = 0
    evidence_count: int = 0
    execution_time_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert complete response to dictionary."""
        return {
            "query": self.query,
            "answer": self.answer,
            "claims": [c.to_dict() for c in self.claims],
            "evidence": self.evidence,
            "contrary_evidence": self.contrary_evidence,
            "limitations": self.limitations,
            "confidence": self.confidence,
            "retrieval_count": self.retrieval_count,
            "evidence_count": self.evidence_count,
            "execution_time_seconds": round(self.execution_time_seconds, 3),
        }


class LegalRAGEngine:
    """
    The unified Vidhik Legal RAG Engine.
    """

    def __init__(
        self,
        config: Optional[RAGConfig] = None,
        retrieval_engine: Optional[HybridRetrievalEngine] = None,
        generator: Optional[QwenGenerator] = None,
    ):
        self.config = config or load_rag_config()
        self._setup_logging()

        logger.info("Initializing Vidhik Legal RAG Engine...")
        start_t = time.time()

        # 1. Initialize or inject Retrieval Engine
        self.retrieval_engine = retrieval_engine or HybridRetrievalEngine()

        # 2. Evidence Selector & Context Builder
        self.evidence_selector = EvidenceSelector(
            max_evidence=self.config.evidence.max_evidence_chunks,
            min_rrf_score=self.config.evidence.min_rrf_score_threshold,
            deduplicate_by_chunk_id=self.config.evidence.deduplicate_by_chunk_id,
        )
        self.context_builder = ContextBuilder(
            config=self.config.context,
        )

        # 3. Generator
        self.generator = generator or QwenGenerator(
            config=self.config.generator,
        )

        logger.info(f"Legal RAG Engine initialized successfully in {time.time() - start_t:.2f}s.")

    def _setup_logging(self):
        """Configure engine logging."""
        self.config.log_dir.mkdir(parents=True, exist_ok=True)
        log_file = self.config.log_dir / self.config.log_file

        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)

        rag_logger = logging.getLogger("VidhikRAG")
        rag_logger.setLevel(getattr(logging, self.config.level.upper(), logging.INFO))
        if not rag_logger.handlers:
            rag_logger.addHandler(file_handler)

    def answer(
        self,
        query: str,
        top_k: Optional[int] = None,
        max_evidence: Optional[int] = None,
    ) -> LegalRAGResponse:
        """
        End-to-end evidence-grounded legal question answering.
        """
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query must be a non-empty string.")

        clean_query = query.strip()
        t0 = time.time()
        logger.info(f"Processing RAG query: '{clean_query}'")

        # Step 1: Hybrid Retrieval
        retrieval_k = top_k if top_k is not None else self.config.retrieval.top_k
        candidates = self.retrieval_engine.search(query=clean_query, top_k=retrieval_k)
        retrieval_count = len(candidates)
        logger.info(f"Retrieved {retrieval_count} candidates from hybrid search.")

        # Step 2: Evidence Selection
        evidence_limit = max_evidence if max_evidence is not None else self.config.evidence.max_evidence_chunks
        evidence_items = self.evidence_selector.select(candidates, max_evidence=evidence_limit)
        evidence_count = len(evidence_items)
        logger.info(f"Selected {evidence_count} evidence items for context assembly.")

        # Legal Safety Check: Insufficient Evidence Handling
        if evidence_count < self.config.grounding.insufficient_evidence_threshold:
            logger.warning(
                f"Insufficient evidence for query: '{clean_query}'. "
                f"Returning calibrated non-hallucinatory response."
            )
            return LegalRAGResponse(
                query=clean_query,
                answer="The retrieved legal corpus did not contain sufficient authoritative evidence to answer this question reliably.",
                claims=[],
                evidence=[],
                limitations="No relevant court holdings, statutes, or precedent were retrieved matching the query criteria.",
                confidence="insufficient_evidence",
                retrieval_count=retrieval_count,
                evidence_count=0,
                execution_time_seconds=time.time() - t0,
            )

        # Step 3: Context Assembly
        context_bundle = self.context_builder.build(
            query=clean_query,
            evidence_items=evidence_items,
        )
        active_evidence = context_bundle.included_evidence

        # Step 4: Prompt Construction
        system_prompt, user_prompt = build_prompts(context_bundle)

        # Step 5: Generation via Evidence-Constrained Qwen
        try:
            gen_output: RawGenerationOutput = self.generator.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
        except Exception as e:
            logger.error(f"Generation failure: {e}", exc_info=True)
            return LegalRAGResponse(
                query=clean_query,
                answer="An error occurred while generating the legal answer.",
                claims=[],
                evidence=[ev.to_dict() for ev in active_evidence],
                limitations=f"Generator service error: {str(e)}",
                confidence="insufficient_evidence",
                retrieval_count=retrieval_count,
                evidence_count=len(active_evidence),
                execution_time_seconds=time.time() - t0,
            )

        # Step 6: Provenance Resolution
        resolved_claims = ProvenanceResolver.resolve(
            raw_claims=gen_output.claims,
            evidence_items=active_evidence,
            verify_citations=True,
        )

        total_time = time.time() - t0
        logger.info(
            f"RAG response assembled in {total_time:.3f}s "
            f"(confidence={gen_output.confidence}, claims={len(resolved_claims)})."
        )

        return LegalRAGResponse(
            query=clean_query,
            answer=gen_output.answer,
            claims=resolved_claims,
            evidence=[ev.to_dict() for ev in active_evidence],
            limitations=gen_output.limitations,
            confidence=gen_output.confidence,
            contrary_evidence=gen_output.contrary_evidence,
            retrieval_count=retrieval_count,
            evidence_count=len(active_evidence),
            execution_time_seconds=total_time,
        )
