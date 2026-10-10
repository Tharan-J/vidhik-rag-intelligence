"""
BM25 Sparse Evidence Selector for Vidhik Phase 5.2
Implements Condition E3: BM25 within-document evidence ranking.
Uses rank_bm25 with Indian legal-aware tokenization from Phase 3.
Zero leakage: Queries are strictly task/metadata-derived, never gold facts.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from rank_bm25 import BM25Okapi

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR / "rag_experiments" / "src"))
from bm25_retriever import tokenize_legal_text


class BM25Selector:
    """Selects evidence windows ranked by BM25 relevance to legal task query."""

    def __init__(
        self,
        k1: float = 1.5,
        b: float = 0.75,
        epsilon: float = 0.25,
        strategy_name: str = "BM25"
    ):
        self.k1 = k1
        self.b = b
        self.epsilon = epsilon
        self.strategy_name = strategy_name

    def rank_document_windows(
        self,
        candidate_windows_df: pd.DataFrame,
        query: str,
        doc_id: str
    ) -> List[Dict[str, Any]]:
        """
        Ranks all candidate windows of a document using BM25.
        
        Args:
            candidate_windows_df: DataFrame of candidate windows for the document.
            query: Task query string.
            doc_id: Document ID.
            
        Returns:
            List of ranked window dicts with BM25 scores and ranks.
        """
        doc_df = candidate_windows_df[candidate_windows_df["document_id"] == doc_id].copy()
        if doc_df.empty:
            return []

        doc_df = doc_df.sort_values(
            by=["page_number", "paragraph_id", "primary_sentence_id"]
        ).reset_index(drop=True)

        corpus_tokens = [tokenize_legal_text(t) for t in doc_df["evidence_text"]]
        bm25 = BM25Okapi(corpus_tokens, k1=self.k1, b=self.b, epsilon=self.epsilon)

        query_tokens = tokenize_legal_text(query)
        if not query_tokens:
            scores = [0.0] * len(doc_df)
        else:
            scores = bm25.get_scores(query_tokens).tolist()

        # Deterministic sorting: score descending, then original index ascending
        indexed_scores = list(enumerate(scores))
        ranked_indices = sorted(indexed_scores, key=lambda x: (-x[1], x[0]))

        ranked_records = []
        for rank, (idx, score) in enumerate(ranked_indices, start=1):
            row = doc_df.iloc[idx]
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
                "selection_reason": f"BM25 score={score:.4f}, rank={rank}, page={row['page_number']}"
            })

        return ranked_records

    def select(
        self,
        candidate_windows_df: pd.DataFrame,
        query: str,
        budget: int,
        doc_id: str
    ) -> List[Dict[str, Any]]:
        """Selects top `budget` windows ranked by BM25."""
        ranked = self.rank_document_windows(candidate_windows_df, query, doc_id)
        selected = ranked[:budget]
        for r in selected:
            r["budget"] = budget
        return selected
