"""
Hybrid Retrieval Engine for Vidhik
==================================
The primary high-level interface combining:
1. BGE-M3 dense semantic retrieval (Qdrant Cloud)
2. BM25 sparse lexical retrieval (Persistent local index)
3. Reciprocal Rank Fusion (RRF with k=60)
4. Comprehensive provenance preservation for downstream Evidence / RAG stages.

Loads models and indexes ONCE at initialization and serves repeated queries efficiently.
"""

import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from .models import HybridRetrievalResult, RetrievalResult
from .config import RetrievalConfig, load_retrieval_config
from .dense import DenseRetriever
from .bm25 import BM25Retriever
from .fusion import reciprocal_rank_fusion

logger = logging.getLogger("VidhikRetrieval.Engine")


class HybridRetrievalEngine:
    """
    Production-grade Hybrid Retrieval Engine for Indian Legal Corpus.
    """

    def __init__(
        self,
        config: Optional[RetrievalConfig] = None,
        config_path: Optional[Path] = None,
        dense_retriever: Optional[DenseRetriever] = None,
        bm25_retriever: Optional[BM25Retriever] = None,
    ):
        """
        Initialize the hybrid retrieval engine.
        Loads BGE-M3 embedding engine, connects to Qdrant Cloud,
        and loads the persistent BM25 index into memory.
        """
        self.config = config or load_retrieval_config(config_path)
        self._setup_logging()

        logger.info("Initializing Vidhik Hybrid Retrieval Engine...")
        start_time = time.time()

        # 1. Initialize Dense Retriever (BGE-M3 + Qdrant Cloud)
        if dense_retriever is not None:
            self.dense_retriever = dense_retriever
        else:
            logger.info("Initializing Dense Retriever (BGE-M3 1024-d + Qdrant Cloud)...")
            self.dense_retriever = DenseRetriever(
                config=self.config.dense,
                embedding_config=self.config.embedding,
            )

        # 2. Initialize BM25 Retriever (Persistent index)
        if bm25_retriever is not None:
            self.bm25_retriever = bm25_retriever
        else:
            logger.info("Initializing BM25 Lexical Retriever from persistent index...")
            self.bm25_retriever = BM25Retriever(
                config=self.config.bm25,
            )

        init_duration = time.time() - start_time
        logger.info(
            f"Hybrid Retrieval Engine initialized successfully in {init_duration:.2f}s "
            f"(BM25 corpus: {self.bm25_retriever.corpus_size:,} chunks)."
        )

    def _setup_logging(self):
        """Configure engine logging according to configuration."""
        self.config.log_dir.mkdir(parents=True, exist_ok=True)
        log_file = self.config.log_dir / self.config.log_file

        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)

        engine_logger = logging.getLogger("VidhikRetrieval")
        engine_logger.setLevel(getattr(logging, self.config.level.upper(), logging.INFO))
        if not engine_logger.handlers:
            engine_logger.addHandler(file_handler)

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        dense_top_k: Optional[int] = None,
        bm25_top_k: Optional[int] = None,
        rrf_k: Optional[int] = None,
    ) -> List[HybridRetrievalResult]:
        """
        Execute full hybrid retrieval pipeline for a user query:
        1. Dense retrieval via BGE-M3 + Qdrant Cloud.
        2. Lexical retrieval via BM25 persistent index.
        3. Hydrate complete provenance payloads for lexical-only hits from Qdrant.
        4. Reciprocal Rank Fusion (RRF) deduplication and ranking.
        5. Return top_k ranked candidates with complete provenance metadata.
        """
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query must be a non-empty string.")

        clean_query = query.strip()
        final_k = top_k if top_k is not None else self.config.final_top_k
        d_k = dense_top_k if dense_top_k is not None else self.config.dense.top_k
        b_k = bm25_top_k if bm25_top_k is not None else self.config.bm25.top_k
        k_const = rrf_k if rrf_k is not None else self.config.fusion.k

        total_start = time.time()
        logger.info(f"Received query: '{clean_query}' (dense_k={d_k}, bm25_k={b_k}, final_k={final_k})")

        # Step 1: Dense Retrieval
        dense_start = time.time()
        dense_results: List[RetrievalResult] = []
        is_degraded = False
        degraded_reason = None
        try:
            dense_results = self.dense_retriever.search(query=clean_query, top_k=d_k)
            dense_duration = time.time() - dense_start
            logger.info(f"Dense retrieval completed in {dense_duration:.3f}s ({len(dense_results)} hits).")
        except Exception as e:
            is_degraded = True
            degraded_reason = "embedding_gateway_unavailable"
            logger.warning(
                f"Dense retrieval unavailable ({e}); gracefully degrading to BM25 lexical retrieval."
            )

        # Step 2: BM25 Lexical Retrieval
        bm25_start = time.time()
        bm25_results: List[RetrievalResult] = []
        try:
            bm25_results = self.bm25_retriever.search(query=clean_query, top_k=b_k)
            bm25_duration = time.time() - bm25_start
            logger.info(f"BM25 retrieval completed in {bm25_duration:.3f}s ({len(bm25_results)} hits).")
        except Exception as e:
            logger.error(f"BM25 retrieval failed: {e}", exc_info=True)
            if not dense_results:
                raise

        if not dense_results and not bm25_results:
            logger.warning(f"No candidates retrieved for query: '{clean_query}'")
            return []

        # Step 3: Provenance Hydration for BM25 candidates
        # Dense results already have complete payloads from Qdrant.
        # For BM25 candidates not present in dense results, hydrate payloads from Qdrant by point ID.
        dense_point_ids = {item.qdrant_point_id for item in dense_results if item.qdrant_point_id}
        missing_point_ids = [
            item.qdrant_point_id
            for item in bm25_results
            if item.qdrant_point_id and item.qdrant_point_id not in dense_point_ids
        ]

        payload_cache: Dict[str, Dict[str, Any]] = {}
        if missing_point_ids:
            try:
                payload_cache = self.dense_retriever.retrieve_payloads_by_point_ids(missing_point_ids)
                logger.debug(f"Hydrated {len(payload_cache)} BM25 candidate payloads from Qdrant.")
            except Exception as e:
                logger.warning(f"Payload hydration for BM25 candidates encountered an issue: {e}")

        # Step 4: Reciprocal Rank Fusion (RRF)
        fusion_start = time.time()
        fused_candidates = reciprocal_rank_fusion(
            dense_results=dense_results,
            bm25_results=bm25_results,
            k=k_const,
            top_k=final_k,
            payload_cache=payload_cache,
        )
        fusion_duration = time.time() - fusion_start

        # Stamp retrieval mode and degraded status on results
        mode_label = "bm25_degraded" if is_degraded else "hybrid"
        for item in fused_candidates:
            item.retrieval_mode = mode_label
            item.degraded = is_degraded
            item.degraded_reason = degraded_reason

        total_duration = time.time() - total_start
        logger.info(
            f"RRF fusion completed in {fusion_duration:.3f}s (mode: {mode_label}). "
            f"Returning {len(fused_candidates)} final results (total time: {total_duration:.3f}s)."
        )

        return fused_candidates

    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check of all retrieval subsystems."""
        qdrant_status = self.dense_retriever.verify_connection()
        bm25_status = {
            "is_loaded": self.bm25_retriever.is_loaded,
            "corpus_chunks": self.bm25_retriever.corpus_size,
            "index_file": str(self.config.bm25.index_file),
            "mapping_file": str(self.config.bm25.mapping_file),
        }
        return {
            "status": "healthy",
            "qdrant": qdrant_status,
            "bm25": bm25_status,
            "dense_dimension": self.config.embedding.dense_dim,
            "rrf_k": self.config.fusion.k,
            "final_top_k": self.config.final_top_k,
        }
