"""
Category Coverage Evaluator for Vidhik Phase 5.2
Calculates fact coverage across all individual legal categories:
  - CASE_NUMBER
  - PARTIES
  - CHARGE
  - STATUTORY_SECTION
  - PROCEDURAL_ACTION
  - JUDICIAL_FINDING
  - DISPOSITION
  - RELIEF
  - BAIL_STATUS
  - AMOUNT
  - COURT
  - OFFICER
  - DATE
"""

from typing import Dict, Any
import pandas as pd


def compute_category_coverage(eval_df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes per-category recall table from fact evaluation results.

    Args:
        eval_df: DataFrame with evaluated facts (fact_id, category, retrieval_status, etc.)

    Returns:
        DataFrame with category-level counts and recall percentages.
    """
    categories = sorted(eval_df["category"].unique())
    rows = []

    for cat in categories:
        sub = eval_df[eval_df["category"] == cat]
        total = len(sub)
        supp = (sub["retrieval_status"] == "RETRIEVED_SUPPORTED").sum()
        part = (sub["retrieval_status"] == "RETRIEVED_PARTIAL").sum()
        not_ret = (sub["retrieval_status"] == "NOT_RETRIEVED").sum()
        recall = round(float(supp) / total, 4) if total > 0 else 0.0

        rows.append({
            "category": cat,
            "total_facts": total,
            "retrieved_supported": int(supp),
            "retrieved_partial": int(part),
            "not_retrieved": int(not_ret),
            "recall": recall,
            "recall_pct": f"{recall * 100:.1f}%"
        })

    return pd.DataFrame(rows)


def compute_document_coverage(eval_df: pd.DataFrame) -> pd.DataFrame:
    """Computes document-by-document fact recall."""
    doc_ids = sorted(eval_df["doc_id"].unique())
    rows = []

    for doc_id in doc_ids:
        sub = eval_df[eval_df["doc_id"] == doc_id]
        total = len(sub)
        supp = (sub["retrieval_status"] == "RETRIEVED_SUPPORTED").sum()
        part = (sub["retrieval_status"] == "RETRIEVED_PARTIAL").sum()
        not_ret = (sub["retrieval_status"] == "NOT_RETRIEVED").sum()
        recall = round(float(supp) / total, 4) if total > 0 else 0.0

        rows.append({
            "doc_id": doc_id,
            "total_facts": total,
            "retrieved_supported": int(supp),
            "retrieved_partial": int(part),
            "not_retrieved": int(not_ret),
            "recall": recall,
            "recall_pct": f"{recall * 100:.1f}%"
        })

    return pd.DataFrame(rows)
