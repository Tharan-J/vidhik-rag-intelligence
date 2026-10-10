"""
Saturation and Oracle Analysis for Vidhik Phase 5.2
Evaluates:
  1. Saturation curve across budgets B in {2, 4, 6, 8, 10, 15}
  2. Diminishing returns & marginal recall gain
  3. ORACLE ANALYSIS — EVALUATION ONLY:
     Greedy set-cover to find the theoretical minimum evidence windows
     required to achieve 80%, 90%, 95%, and 100% gold fact coverage.
"""

from typing import Dict, Any, List, Tuple
import pandas as pd
from evaluation.evaluate_fact_coverage import evaluate_fact_coverage_for_windows, compute_aggregate_metrics


def analyze_saturation(results_df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyzes saturation across increasing evidence budgets for each strategy.

    Args:
        results_df: DataFrame containing experimental runs across strategies and budgets.

    Returns:
        DataFrame with delta recalls and marginal efficiency.
    """
    saturation_rows = []

    for strategy, grp in results_df.groupby("strategy"):
        grp = grp.sort_values(by="budget").reset_index(drop=True)
        prev_recall = 0.0
        prev_crit_recall = 0.0
        prev_budget = 0

        for _, row in grp.iterrows():
            b = int(row["budget"])
            rec = float(row["overall_recall"])
            crit_rec = float(row["critical_recall"])
            delta_b = b - prev_budget
            delta_rec = rec - prev_recall
            delta_crit = crit_rec - prev_crit_recall
            marginal_gain_per_window = round(delta_rec / delta_b, 4) if delta_b > 0 else 0.0

            saturation_rows.append({
                "strategy": strategy,
                "budget": b,
                "overall_recall": rec,
                "critical_recall": crit_rec,
                "delta_overall_recall": round(delta_rec, 4),
                "delta_critical_recall": round(delta_crit, 4),
                "marginal_gain_per_window": marginal_gain_per_window,
                "estimated_tokens": int(row["estimated_llm_tokens"]),
                "is_saturated": marginal_gain_per_window < 0.02 and b >= 8
            })

            prev_recall = rec
            prev_crit_recall = crit_rec
            prev_budget = b

    return pd.DataFrame(saturation_rows)


def run_oracle_analysis(
    gold_facts_df: pd.DataFrame,
    candidate_windows_df: pd.DataFrame
) -> pd.DataFrame:
    """
    ORACLE ANALYSIS — EVALUATION ONLY.
    Determines the theoretical minimum evidence windows required to maximize fact coverage.
    Uses greedy set cover per document.
    """
    oracle_records = []
    bench_docs = sorted(gold_facts_df["doc_id"].unique())

    # For each document, greedily pick windows that cover the most uncovered facts
    for target_budget in [1, 2, 3, 4, 5, 6, 7, 8, 10, 15]:
        selected_oracle_windows = []

        for doc_id in bench_docs:
            doc_gold = gold_facts_df[gold_facts_df["doc_id"] == doc_id]
            doc_cands = candidate_windows_df[candidate_windows_df["document_id"] == doc_id].copy()

            if doc_cands.empty:
                continue

            # Greedy selection of windows for this document up to target_budget
            chosen_windows = []
            covered_fids = set()

            available_cands = doc_cands.copy()

            for step in range(min(target_budget, len(doc_cands))):
                best_cand = None
                best_new_coverage = -1
                best_new_fids = set()

                for _, cand in available_cands.iterrows():
                    cand_df = pd.DataFrame([cand])
                    cand_eval = evaluate_fact_coverage_for_windows(doc_gold, cand_df)
                    cand_supp = set(cand_eval[cand_eval["retrieval_status"] == "RETRIEVED_SUPPORTED"]["fact_id"])
                    
                    new_fids = cand_supp - covered_fids
                    if len(new_fids) > best_new_coverage:
                        best_new_coverage = len(new_fids)
                        best_cand = cand
                        best_new_fids = new_fids

                if best_cand is not None:
                    chosen_windows.append(best_cand)
                    covered_fids.update(best_new_fids)
                    # Remove from available
                    available_cands = available_cands[available_cands["evidence_id"] != best_cand["evidence_id"]]
                else:
                    break

            if chosen_windows:
                selected_oracle_windows.append(pd.DataFrame(chosen_windows))

        if selected_oracle_windows:
            all_chosen_df = pd.concat(selected_oracle_windows, ignore_index=True)
            eval_res = evaluate_fact_coverage_for_windows(gold_facts_df, all_chosen_df)
            metrics = compute_aggregate_metrics(eval_res)

            oracle_records.append({
                "budget_per_doc": target_budget,
                "total_windows_selected": len(all_chosen_df),
                "overall_recall": metrics["overall_recall"],
                "critical_recall": metrics["critical_recall"],
                "important_recall": metrics["important_recall"],
                "contextual_recall": metrics["contextual_recall"],
                "legal_outcome_recall": metrics["legal_outcome_recall"],
                "facts_retrieved": metrics["retrieved_supported"],
                "total_facts": metrics["total_facts"]
            })

    return pd.DataFrame(oracle_records)
