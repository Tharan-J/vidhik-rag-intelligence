"""
Corpus-Level BM25 Lexical Retrieval Engine & Index Store
========================================================
Maintains a standalone, persistent sparse lexical index using rank_bm25 (BM25Okapi).
Computes authentic corpus-level term statistics (document frequencies, IDF, average document length).
Preserves legal identifiers (Section, 438, CrPC, Article, 21, IPC, BNSS, AIR, SCC, OnLine, SC, citations).
Retains direct mapping from BM25 index positions to deterministic Qdrant point IDs (UUIDv5).
Provides Reciprocal Rank Fusion (RRF) for downstream hybrid dense + lexical retrieval.
"""

import os
import re
import pickle
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from rank_bm25 import BM25Okapi

from .chunk import LegalChunk
from .qdrant_store import generate_deterministic_point_id

logger = logging.getLogger("VidhikIngestion.BM25")


def tokenize_legal_text(text: str) -> List[str]:
    """
    Tokenize legal text preserving citations, sections, and legal abbreviations.
    Conservative preprocessing: preserves numbers, legal terms, statutes, and citations.
    """
    if not text:
        return []

    # Expand slash forms like u/s, cr/pc, 174/10 while keeping original component words
    text_expanded = re.sub(r"(\b\w+)/(\w+\b)", r"\1 \2 \1/\2", text)

    # Tokenize words, numbers, sections, abbreviations with dots/slashes
    raw_tokens = re.findall(r"[a-zA-Z0-9]+(?:[./-][a-zA-Z0-9]+)*|\b[a-zA-Z0-9]+\b", text_expanded.lower())

    # Strip extraneous punctuation edges while preserving alphanumeric content
    clean_tokens = []
    for t in raw_tokens:
        cleaned = t.strip(".-/")
        if cleaned:
            clean_tokens.append(cleaned)

    return clean_tokens


class BM25Store:
    def __init__(
        self,
        index_dir: Optional[Path] = None,
        index_file: str = "bm25_index.pkl",
        mapping_file: str = "bm25_mapping.parquet",
        k1: float = 1.5,
        b: float = 0.75,
        epsilon: float = 0.25,
    ):
        self.index_dir = Path(index_dir) if index_dir else None
        self.index_file = index_file
        self.mapping_file = mapping_file
        self.k1 = k1
        self.b = b
        self.epsilon = epsilon

        self.bm25: Optional[BM25Okapi] = None
        self.corpus_tokens: List[List[str]] = []
        # Mapping records: list of dicts with keys:
        # bm25_index_position, qdrant_point_id, document_id, chunk_id, text
        self.mapping_records: List[Dict[str, Any]] = []

    def add_chunks(self, chunks: List[LegalChunk]):
        """Accumulate chunks across documents for corpus-level BM25 construction."""
        for chunk in chunks:
            pos = len(self.mapping_records)
            qdrant_pt_id = generate_deterministic_point_id(chunk.document_id, chunk.chunk_id)
            tokens = tokenize_legal_text(chunk.text)

            self.corpus_tokens.append(tokens)
            self.mapping_records.append({
                "bm25_index_position": pos,
                "qdrant_point_id": qdrant_pt_id,
                "document_id": chunk.document_id,
                "chunk_id": chunk.chunk_id,
                "text": chunk.text,
            })

    def build_index(self, chunks: Optional[List[LegalChunk]] = None):
        """
        Build the corpus-level BM25Okapi index over all accumulated chunks.
        Computes global IDF, doc lengths, and average document length.
        """
        if chunks:
            self.corpus_tokens.clear()
            self.mapping_records.clear()
            self.add_chunks(chunks)

        if not self.corpus_tokens:
            raise ValueError("Cannot build BM25 index: no chunk tokens available.")

        logger.info(f"Building corpus-level BM25 index over {len(self.corpus_tokens)} chunks (k1={self.k1}, b={self.b})...")
        self.bm25 = BM25Okapi(
            self.corpus_tokens,
            k1=self.k1,
            b=self.b,
            epsilon=self.epsilon
        )
        logger.info(f"Corpus-level BM25 index built successfully over {len(self.corpus_tokens)} chunks.")

    def save(self, index_dir: Optional[Path] = None):
        """Persist BM25 index and mapping DataFrame to disk."""
        target_dir = Path(index_dir) if index_dir else self.index_dir
        if not target_dir:
            raise ValueError("index_dir must be specified to save BM25 index.")

        target_dir.mkdir(parents=True, exist_ok=True)
        idx_path = target_dir / self.index_file
        map_path = target_dir / self.mapping_file

        if self.bm25 is None or not self.mapping_records:
            raise ValueError("Cannot save uninitialized BM25 index.")

        logger.info(f"Persisting BM25 model to {idx_path}...")
        with open(idx_path, "wb") as f:
            pickle.dump({
                "bm25": self.bm25,
                "corpus_tokens": self.corpus_tokens,
                "k1": self.k1,
                "b": self.b,
                "epsilon": self.epsilon,
            }, f, protocol=pickle.HIGHEST_PROTOCOL)

        logger.info(f"Persisting BM25 mapping to {map_path}...")
        df_map = pd.DataFrame(self.mapping_records)
        df_map.to_parquet(map_path, index=False)
        logger.info(f"BM25 index and mapping successfully persisted ({len(self.mapping_records)} entries).")

    def load(self, index_dir: Optional[Path] = None):
        """Load persistent BM25 index and mapping from disk."""
        target_dir = Path(index_dir) if index_dir else self.index_dir
        if not target_dir:
            raise ValueError("index_dir must be specified to load BM25 index.")

        idx_path = target_dir / self.index_file
        map_path = target_dir / self.mapping_file

        if not map_path.exists():
            raise FileNotFoundError(f"BM25 mapping file missing at {map_path}")

        logger.info(f"Loading BM25 mapping from {map_path}...")
        df_map = pd.read_parquet(map_path)
        self.mapping_records = df_map.to_dict(orient="records")

        if idx_path.exists():
            logger.info(f"Loading cached BM25 model pickle from {idx_path}...")
            with open(idx_path, "rb") as f:
                data = pickle.load(f)
                self.bm25 = data["bm25"]
                self.corpus_tokens = data.get("corpus_tokens", [])
                self.k1 = data.get("k1", self.k1)
                self.b = data.get("b", self.b)
                self.epsilon = data.get("epsilon", self.epsilon)
        else:
            logger.info(f"BM25 pickle index not present at {idx_path}. Reconstructing BM25Okapi model from mapping ({len(self.mapping_records)} chunks)...")
            self.corpus_tokens = [
                tokenize_legal_text(str(r.get("text", "")))
                for r in self.mapping_records
            ]
            self.bm25 = BM25Okapi(
                self.corpus_tokens,
                k1=self.k1,
                b=self.b,
                epsilon=self.epsilon,
            )
            logger.info("BM25Okapi model reconstructed in memory successfully.")

        logger.info(f"BM25 index and mapping loaded successfully ({len(self.mapping_records)} chunks).")

    def search(self, query: str, top_k: int = 50) -> List[Dict[str, Any]]:
        """
        Perform BM25 lexical retrieval for a query.
        Returns top_k hits mapped to Qdrant point IDs.
        """
        if self.bm25 is None or not self.mapping_records:
            raise RuntimeError("BM25 index is not loaded or built.")

        query_tokens = tokenize_legal_text(query)
        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        hits = []
        for rank, idx in enumerate(ranked_indices, start=1):
            score = float(scores[idx])
            rec = self.mapping_records[idx]
            hits.append({
                "qdrant_point_id": rec["qdrant_point_id"],
                "document_id": rec["document_id"],
                "chunk_id": rec["chunk_id"],
                "bm25_rank": rank,
                "score": score,
                "text": rec.get("text", ""),
            })

        return hits


def fuse_results(
    dense_results: List[Dict[str, Any]],
    bm25_results: List[Dict[str, Any]],
    k: int = 60,
    dense_weight: float = 0.60,
    bm25_weight: float = 0.40,
    top_k: int = 50,
) -> List[Dict[str, Any]]:
    """
    Standard Reciprocal Rank Fusion (RRF) between dense Qdrant results and BM25 lexical results.
    
    Formula:
        RRF(d) = dense_weight * (1 / (k + rank_dense(d))) + bm25_weight * (1 / (k + rank_bm25(d)))
    
    Both dense_results and bm25_results must contain 'qdrant_point_id'.
    """
    scores: Dict[str, float] = {}
    dense_ranks: Dict[str, int] = {}
    bm25_ranks: Dict[str, int] = {}
    item_metadata: Dict[str, Dict[str, Any]] = {}

    for rank, item in enumerate(dense_results, start=1):
        pt_id = item["qdrant_point_id"]
        dense_ranks[pt_id] = rank
        item_metadata[pt_id] = item
        scores[pt_id] = scores.get(pt_id, 0.0) + dense_weight * (1.0 / (k + rank))

    for rank, item in enumerate(bm25_results, start=1):
        pt_id = item["qdrant_point_id"]
        bm25_ranks[pt_id] = rank
        if pt_id not in item_metadata:
            item_metadata[pt_id] = item
        scores[pt_id] = scores.get(pt_id, 0.0) + bm25_weight * (1.0 / (k + rank))

    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:top_k]

    fused = []
    for rank, pt_id in enumerate(sorted_ids, start=1):
        meta = item_metadata[pt_id]
        fused.append({
            "fused_rank": rank,
            "rrf_score": scores[pt_id],
            "qdrant_point_id": pt_id,
            "document_id": meta.get("document_id"),
            "chunk_id": meta.get("chunk_id"),
            "dense_rank": dense_ranks.get(pt_id),
            "bm25_rank": bm25_ranks.get(pt_id),
            "text": meta.get("text"),
        })

    return fused
