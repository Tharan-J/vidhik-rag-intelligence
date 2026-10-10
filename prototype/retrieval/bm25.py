"""
BM25 Sparse Lexical Retrieval Subsystem
=======================================
Loads the persisted corpus-level BM25 index and mapping DataFrame:
- indexes/bm25/bm25_index.pkl
- indexes/bm25/bm25_mapping.parquet
Maintains the loaded index in memory across queries (loaded once at startup).
Preserves legal tokens and maps BM25 internal corpus positions directly to deterministic Qdrant point IDs.
Returns ranked candidates as RetrievalResult instances.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from ingestion.bm25_store import BM25Store, tokenize_legal_text
from .models import RetrievalResult
from .config import BM25RetrievalConfig, load_retrieval_config

logger = logging.getLogger("VidhikRetrieval.BM25")


class BM25Retriever:
    """
    Production-grade BM25 lexical retriever loading persisted corpus-level statistics.
    """

    def __init__(
        self,
        config: Optional[BM25RetrievalConfig] = None,
        store: Optional[BM25Store] = None,
    ):
        if config is None:
            full_cfg = load_retrieval_config()
            self.config = full_cfg.bm25
        else:
            self.config = config

        self.store = store
        if self.store is None:
            self.store = BM25Store(
                index_dir=self.config.index_dir,
                index_file=self.config.index_file,
                mapping_file=self.config.mapping_file,
                k1=self.config.k1,
                b=self.config.b,
                epsilon=self.config.epsilon,
            )
            self._load_index()

    def _load_index(self):
        """Load persistent BM25 index and mapping into memory."""
        idx_path = self.config.index_dir / self.config.index_file
        map_path = self.config.index_dir / self.config.mapping_file

        if not idx_path.exists():
            raise FileNotFoundError(f"BM25 index file not found at: {idx_path}")
        if not map_path.exists():
            raise FileNotFoundError(f"BM25 mapping file not found at: {map_path}")

        logger.info(f"Loading persistent BM25 index from {idx_path}...")
        self.store.load()
        logger.info(f"BM25 index ready with {len(self.store.mapping_records)} indexed chunks.")

    @property
    def corpus_size(self) -> int:
        """Total chunks in the BM25 index."""
        return len(self.store.mapping_records) if self.store else 0

    @property
    def is_loaded(self) -> bool:
        """Check if index is actively loaded in memory."""
        return self.store is not None and self.store.bm25 is not None

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
    ) -> List[RetrievalResult]:
        """
        Execute BM25 lexical search over legal tokens.
        Returns top_k RetrievalResult instances mapped to Qdrant point IDs.
        """
        if not self.is_loaded:
            raise RuntimeError("BM25 index is not loaded.")

        if not query or not query.strip():
            raise ValueError("Query string cannot be empty.")

        limit = top_k if top_k is not None else self.config.top_k
        if limit <= 0:
            return []

        hits = self.store.search(query=query.strip(), top_k=limit)

        results: List[RetrievalResult] = []
        for h in hits:
            qdrant_pt_id = h.get("qdrant_point_id", "")
            chunk_id = h.get("chunk_id", "")
            doc_id = h.get("document_id", "")
            score = float(h.get("score", 0.0))
            rank = int(h.get("bm25_rank", len(results) + 1))
            text = h.get("text", "")

            res = RetrievalResult(
                chunk_id=chunk_id,
                document_id=doc_id,
                score=score,
                retrieval_method="bm25",
                text=text,
                qdrant_point_id=qdrant_pt_id,
                rank=rank,
                source="BM25",
                metadata={
                    "document_id": doc_id,
                    "chunk_id": chunk_id,
                    "qdrant_point_id": qdrant_pt_id,
                    "bm25_score": score,
                    "bm25_rank": rank,
                },
            )
            results.append(res)

        logger.debug(f"BM25 search retrieved {len(results)} hits for query.")
        return results
