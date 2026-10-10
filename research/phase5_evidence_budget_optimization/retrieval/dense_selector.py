"""
Dense BGE-M3 Evidence Selector for Vidhik Phase 5.2
Implements Condition E4: Dense BGE-M3 within-document evidence ranking.
Uses 1024-dim normalized embeddings and cosine similarity.
Zero leakage: Queries are strictly task/metadata-derived, never gold facts.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR / "rag_experiments" / "src"))
from embeddings import BGEM3Embedder


class DenseSelector:
    """Selects evidence windows ranked by dense BGE-M3 semantic similarity."""

    def __init__(
        self,
        embeddings_arr: Optional[np.ndarray] = None,
        candidate_windows_df: Optional[pd.DataFrame] = None,
        embedder: Optional[BGEM3Embedder] = None,
        strategy_name: str = "DENSE_BGE_M3"
    ):
        self.embeddings_arr = embeddings_arr
        self.candidate_windows_df = candidate_windows_df
        self.embedder = embedder
        self.strategy_name = strategy_name
        self.query_embedding_cache = {}

    def get_query_embedding(self, query: str) -> np.ndarray:
        """Gets or computes normalized embedding for query."""
        if query in self.query_embedding_cache:
            return self.query_embedding_cache[query]
        if self.embedder is None:
            self.embedder = BGEM3Embedder()
        vec = self.embedder.embed_texts([query])[0]
        # Normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        self.query_embedding_cache[query] = vec
        return vec

    def rank_document_windows(
        self,
        candidate_windows_df: pd.DataFrame,
        embeddings_arr: np.ndarray,
        query: str,
        doc_id: str
    ) -> List[Dict[str, Any]]:
        """
        Ranks all candidate windows of a document using dense BGE-M3 cosine similarity.
        """
        # Find indices of candidate windows for doc_id
        doc_indices = candidate_windows_df.index[
            candidate_windows_df["document_id"] == doc_id
        ].tolist()

        if not doc_indices:
            return []

        doc_df = candidate_windows_df.loc[doc_indices].copy()
        doc_embeddings = embeddings_arr[doc_indices]  # Shape: (N, 1024)

        q_vec = self.get_query_embedding(query)  # Shape: (1024,)

        # Cosine similarity is dot product of normalized vectors
        scores = np.dot(doc_embeddings, q_vec).tolist()

        indexed_scores = list(enumerate(scores))
        # Deterministic sorting: score descending, then original index ascending
        ranked_indices = sorted(indexed_scores, key=lambda x: (-x[1], x[0]))

        ranked_records = []
        for rank, (sub_idx, score) in enumerate(ranked_indices, start=1):
            row = doc_df.iloc[sub_idx]
            orig_idx = doc_indices[sub_idx]
            sids = row["sentence_ids"]
            if hasattr(sids, "tolist"):
                sids = sids.tolist()
            elif isinstance(sids, (list, tuple)):
                sids = list(sids)
            else:
                sids = [str(sids)]

            ranked_records.append({
                "document_id": doc_id,
                "evidence_id": row["evidence_id"],
                "sentence_id": row["primary_sentence_id"],
                "sentence_ids": sids,
                "paragraph_id": row["paragraph_id"],
                "page_id": int(row["page_number"]),
                "page_number": int(row["page_number"]),
                "source_pdf_identifier": f"{doc_id}.pdf",
                "source_sha256": row["source_sha256"],
                "evidence_text": row["evidence_text"],
                "window_boundaries": f"{sids[0]}..{sids[-1]}" if len(sids) > 1 else sids[0],
                "retrieval_score": round(float(score), 6),
                "retrieval_strategy": self.strategy_name,
                "rank": rank,
                "candidate_index": orig_idx,
                "selection_reason": f"BGE-M3 dense score={score:.4f}, rank={rank}, page={row['page_number']}"
            })

        return ranked_records

    def select(
        self,
        candidate_windows_df: pd.DataFrame,
        embeddings_arr: np.ndarray,
        query: str,
        budget: int,
        doc_id: str
    ) -> List[Dict[str, Any]]:
        """Selects top `budget` windows ranked by BGE-M3."""
        ranked = self.rank_document_windows(candidate_windows_df, embeddings_arr, query, doc_id)
        selected = ranked[:budget]
        for r in selected:
            r["budget"] = budget
        return selected
