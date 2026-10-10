"""
Sequential Evidence Selector for Vidhik Phase 5.2
Implements:
- E0: Historical Baseline (head(4))
- E2: Fixed Sequential Budget (head(B) for B in {2, 4, 6, 8, 10, 15})
"""

from typing import List, Dict, Any
import pandas as pd


class SequentialSelector:
    """Selects evidence windows in sequential document reading order."""

    def __init__(self, strategy_name: str = "SEQUENTIAL"):
        self.strategy_name = strategy_name

    def select(
        self,
        candidate_windows_df: pd.DataFrame,
        budget: int,
        doc_id: str
    ) -> List[Dict[str, Any]]:
        """
        Selects top `budget` windows in sequential document order.
        
        Args:
            candidate_windows_df: DataFrame of candidate windows for the document.
            budget: Number of windows to select (B).
            doc_id: Document ID.
            
        Returns:
            List of selected window dicts with full provenance metadata.
        """
        doc_df = candidate_windows_df[candidate_windows_df["document_id"] == doc_id].copy()
        
        # Sort strictly in document sequential order
        doc_df = doc_df.sort_values(
            by=["page_number", "paragraph_id", "primary_sentence_id"]
        ).reset_index(drop=True)
        
        # Take head(budget)
        selected_df = doc_df.head(budget)
        
        selected_records = []
        for rank, (_, row) in enumerate(selected_df.iterrows(), start=1):
            sids = row["sentence_ids"]
            if hasattr(sids, "tolist"):
                sids = sids.tolist()
            elif isinstance(sids, (list, tuple)):
                sids = list(sids)
            else:
                sids = [str(sids)]
                
            selected_records.append({
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
                "retrieval_score": round(1.0 / rank, 6),
                "retrieval_strategy": self.strategy_name,
                "budget": budget,
                "rank": rank,
                "selection_reason": f"Sequential document reading order position rank={rank}, page={row['page_number']}"
            })
            
        return selected_records
