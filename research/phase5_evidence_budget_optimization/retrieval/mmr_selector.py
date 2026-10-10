r"""
Diversity and MMR Evidence Selector for Vidhik Phase 5.2
Implements Condition E6: Hybrid RRF + Maximal Marginal Relevance (MMR)
with legal-aware provenance/page diversity.

Formula:
  MMR(d) = \lambda * Relevance(d) - (1 - \lambda) * MaxSimilarity(d, S) - \beta * RegionPenalty(d, S)

Where:
  \lambda \in {0.7, 0.8, 0.9}
  Relevance(d) = Normalized Hybrid RRF score
  MaxSimilarity(d, S) = max_{s in S} cosine_similarity(emb(d), emb(s))
  RegionPenalty(d, S) = Intra-paragraph or intra-page saturation penalty
Zero leakage: No gold facts are used during selection.
"""

from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd

from retrieval.hybrid_rrf_selector import HybridRRFSelector


class MMRSelector:
    """Selects diverse, highly relevant evidence windows using MMR and provenance awareness."""

    def __init__(
        self,
        hybrid_selector: HybridRRFSelector,
        lambda_param: float = 0.8,
        region_penalty_weight: float = 0.15,
        strategy_name: str = "HYBRID_MMR"
    ):
        self.hybrid_selector = hybrid_selector
        self.lambda_param = lambda_param
        self.region_penalty_weight = region_penalty_weight
        self.strategy_name = strategy_name

    def select(
        self,
        candidate_windows_df: pd.DataFrame,
        embeddings_arr: np.ndarray,
        query: str,
        budget: int,
        doc_id: str,
        lambda_param: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Selects top `budget` windows using MMR over the candidate pool.
        """
        lam = self.lambda_param if lambda_param is None else lambda_param

        # 1. Generate full candidate pool ranked by Hybrid RRF
        ranked_candidates = self.hybrid_selector.rank_document_windows(
            candidate_windows_df, embeddings_arr, query, doc_id
        )

        if not ranked_candidates:
            return []

        # If budget >= total candidates, return all sorted by RRF
        if budget >= len(ranked_candidates):
            selected = [dict(c) for c in ranked_candidates]
            for r, c in enumerate(selected, start=1):
                c["rank"] = r
                c["budget"] = budget
                c["retrieval_strategy"] = f"{self.strategy_name}_LAMBDA_{lam:.1f}"
            return selected

        # Map evidence_id to candidate index in embeddings_arr
        ev_id_to_idx = {}
        for c in ranked_candidates:
            ev_id = c["evidence_id"]
            orig_match = candidate_windows_df[
                (candidate_windows_df["document_id"] == doc_id) &
                (candidate_windows_df["evidence_id"] == ev_id)
            ]
            if not orig_match.empty:
                ev_id_to_idx[ev_id] = orig_match.index[0]

        # Extract embeddings for candidates
        cand_embeddings = {}
        for c in ranked_candidates:
            ev_id = c["evidence_id"]
            idx = ev_id_to_idx[ev_id]
            cand_embeddings[ev_id] = embeddings_arr[idx]

        # Normalize RRF relevance scores to [0, 1]
        rrf_scores = [c["retrieval_score"] for c in ranked_candidates]
        min_rrf, max_rrf = min(rrf_scores), max(rrf_scores)
        rrf_range = (max_rrf - min_rrf) if max_rrf > min_rrf else 1.0

        for c in ranked_candidates:
            c["norm_relevance"] = (c["retrieval_score"] - min_rrf) / rrf_range

        # Determine all available pages in candidate pool
        all_pages = set(c["page_number"] for c in ranked_candidates)

        selected_candidates: List[Dict[str, Any]] = []
        selected_ev_ids = set()
        selected_paragraphs = set()
        selected_pages = set()

        # Step 1: Select the top candidate (highest relevance)
        first_cand = dict(ranked_candidates[0])
        first_cand["mmr_score"] = 1.0
        first_cand["rank"] = 1
        first_cand["budget"] = budget
        first_cand["retrieval_strategy"] = f"{self.strategy_name}_LAMBDA_{lam:.1f}"
        first_cand["selection_reason"] = (
            f"MMR rank=1 top relevance (rrf={first_cand['retrieval_score']:.6f}, "
            f"page={first_cand['page_number']})"
        )

        selected_candidates.append(first_cand)
        selected_ev_ids.add(first_cand["evidence_id"])
        selected_paragraphs.add(first_cand["paragraph_id"])
        selected_pages.add(first_cand["page_number"])

        # Subsequent steps: Greedily select next best candidate
        while len(selected_candidates) < budget:
            best_cand = None
            best_mmr = -float("inf")
            best_sim = 0.0
            best_reg_pen = 0.0

            unselected = [c for c in ranked_candidates if c["evidence_id"] not in selected_ev_ids]
            if not unselected:
                break

            for cand in unselected:
                c_id = cand["evidence_id"]
                c_vec = cand_embeddings[c_id]
                rel = cand["norm_relevance"]

                # Maximum similarity to already selected candidates
                max_sim = max(
                    float(np.dot(c_vec, cand_embeddings[s["evidence_id"]]))
                    for s in selected_candidates
                )

                # Provenance / Regional diversity penalty
                region_pen = 0.0
                if cand["paragraph_id"] in selected_paragraphs:
                    region_pen += 0.8  # Penalty for same paragraph
                if cand["page_number"] in selected_pages and (all_pages - selected_pages):
                    region_pen += 0.3  # Penalty if other unvisited pages exist

                mmr = (
                    lam * rel
                    - (1.0 - lam) * max_sim
                    - self.region_penalty_weight * region_pen
                )

                if mmr > best_mmr:
                    best_mmr = mmr
                    best_cand = cand
                    best_sim = max_sim
                    best_reg_pen = region_pen

            if best_cand is None:
                break

            next_cand = dict(best_cand)
            rank = len(selected_candidates) + 1
            next_cand["mmr_score"] = round(float(best_mmr), 6)
            next_cand["retrieval_score"] = round(float(best_mmr), 6)
            next_cand["rank"] = rank
            next_cand["budget"] = budget
            next_cand["retrieval_strategy"] = f"{self.strategy_name}_LAMBDA_{lam:.1f}"
            next_cand["selection_reason"] = (
                f"MMR rank={rank} (mmr={best_mmr:.4f}, rel={next_cand['norm_relevance']:.4f}, "
                f"max_sim={best_sim:.4f}, reg_pen={best_reg_pen:.2f}, page={next_cand['page_number']})"
            )

            selected_candidates.append(next_cand)
            selected_ev_ids.add(next_cand["evidence_id"])
            selected_paragraphs.add(next_cand["paragraph_id"])
            selected_pages.add(next_cand["page_number"])

        return selected_candidates
