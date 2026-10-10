"""
Hybrid BM25 + Dense RRF Evidence Selector for Vidhik Phase 5.2
Implements Condition E5: Hybrid RRF within-document evidence ranking.
Uses Phase 3 validated fusion parameters:
  k = 60, dense_weight = 0.60, bm25_weight = 0.40
Zero leakage: Queries are strictly task/metadata-derived, never gold facts.
"""

from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd

from retrieval.bm25_selector import BM25Selector
from retrieval.dense_selector import DenseSelector


class HybridRRFSelector:
    """Selects evidence windows using Reciprocal Rank Fusion of BM25 and BGE-M3."""

    def __init__(
        self,
        bm25_selector: BM25Selector,
        dense_selector: DenseSelector,
        k: int = 60,
        dense_weight: float = 0.60,
        bm25_weight: float = 0.40,
        strategy_name: str = "HYBRID_RRF"
    ):
        self.bm25_selector = bm25_selector
        self.dense_selector = dense_selector
        self.k = k
        self.dense_weight = dense_weight
        self.bm25_weight = bm25_weight
        self.strategy_name = strategy_name

    def rank_document_windows(
        self,
        candidate_windows_df: pd.DataFrame,
        embeddings_arr: np.ndarray,
        query: str,
        doc_id: str
    ) -> List[Dict[str, Any]]:
        """
        Ranks all candidate windows of a document using Hybrid RRF.
        """
        bm25_ranked = self.bm25_selector.rank_document_windows(
            candidate_windows_df, query, doc_id
        )
        dense_ranked = self.dense_selector.rank_document_windows(
            candidate_windows_df, embeddings_arr, query, doc_id
        )

        if not bm25_ranked and not dense_ranked:
            return []

        # Map evidence_id to ranks
        bm25_map = {r["evidence_id"]: r for r in bm25_ranked}
        dense_map = {r["evidence_id"]: r for r in dense_ranked}

        all_ev_ids = list(dict.fromkeys([r["evidence_id"] for r in dense_ranked] + [r["evidence_id"] for r in bm25_ranked]))

        rrf_scores = []
        for ev_id in all_ev_ids:
            bm25_item = bm25_map.get(ev_id)
            dense_item = dense_map.get(ev_id)

            b_rank = bm25_item["rank"] if bm25_item else (len(all_ev_ids) + 1)
            d_rank = dense_item["rank"] if dense_item else (len(all_ev_ids) + 1)

            rrf = (
                self.dense_weight * (1.0 / (self.k + d_rank)) +
                self.bm25_weight * (1.0 / (self.k + b_rank))
            )

            base_item = dense_item or bm25_item
            rrf_scores.append({
                "evidence_id": ev_id,
                "item": base_item,
                "rrf_score": rrf,
                "dense_rank": d_rank,
                "bm25_rank": b_rank,
                "page_number": base_item["page_number"]
            })

        # Deterministic sorting: rrf_score descending, then page/evidence_id
        rrf_scores = sorted(
            rrf_scores,
            key=lambda x: (-x["rrf_score"], x["page_number"], x["evidence_id"])
        )

        ranked_records = []
        for rank, entry in enumerate(rrf_scores, start=1):
            base = dict(entry["item"])
            base["retrieval_score"] = round(float(entry["rrf_score"]), 6)
            base["retrieval_strategy"] = self.strategy_name
            base["rank"] = rank
            base["selection_reason"] = (
                f"Hybrid RRF score={entry['rrf_score']:.6f} "
                f"(dense_rank={entry['dense_rank']}, bm25_rank={entry['bm25_rank']}), "
                f"page={base['page_number']}"
            )
            ranked_records.append(base)

        return ranked_records

    def select(
        self,
        candidate_windows_df: pd.DataFrame,
        embeddings_arr: np.ndarray,
        query: str,
        budget: int,
        doc_id: str
    ) -> List[Dict[str, Any]]:
        """Selects top `budget` windows ranked by Hybrid RRF."""
        ranked = self.rank_document_windows(
            candidate_windows_df, embeddings_arr, query, doc_id
        )
        selected = ranked[:budget]
        for r in selected:
            r["budget"] = budget
        return selected
