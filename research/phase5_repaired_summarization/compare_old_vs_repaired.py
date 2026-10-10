"""
Old vs Repaired Comparison Engine for Vidhik Phase 5
Directly compares the historical head(4) baseline against the repaired BM25 B=8 summarization run.

Produces:
  1. comparison/old_vs_repaired.csv
  2. comparison/old_vs_repaired_by_language.csv
  3. comparison/failure_shift.csv
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Old_Vs_Repaired")

ROOT_DIR = Path(__file__).resolve().parent.parent
EXP_DIR = ROOT_DIR / "phase5_repaired_summarization"
sys.path.append(str(EXP_DIR))

from evaluate_repaired_summaries import evaluate_fact_preservation, LEGAL_OUTCOME_CATEGORIES

GOLD_PATH = ROOT_DIR / "phase5_source_grounded_gold" / "gold_facts.parquet"
HIST_SUMS_PATH = ROOT_DIR / "phase4_summarization" / "generation" / "summaries_v1.parquet"
HIST_EVAL_PATH = ROOT_DIR / "phase5_retrieval_evaluation" / "retrieval_fact_evaluation.parquet"
REPAIRED_EVAL_PATH = EXP_DIR / "evaluation" / "fact_level_evaluation.parquet"
REPAIRED_OVERALL_PATH = EXP_DIR / "evaluation" / "overall_results.csv"
REPAIRED_LANG_PATH = EXP_DIR / "evaluation" / "language_level_results.csv"
COMP_DIR = EXP_DIR / "comparison"

BENCH_DOCS = [
    "DC_000001", "DC_000002", "DC_000003", "DC_000004", "DC_000005",
    "DC_000006", "DC_000007", "DC_000008", "DC_000011"
]


def run_comparison():
    logger.info("Initializing Old vs Repaired Scientific Comparison...")
    gold_df = pd.read_parquet(GOLD_PATH)
    hist_sums = pd.read_parquet(HIST_SUMS_PATH)
    hist_eval_ret = pd.read_parquet(HIST_EVAL_PATH)
    repaired_eval = pd.read_parquet(REPAIRED_EVAL_PATH)
    repaired_overall = pd.read_csv(REPAIRED_OVERALL_PATH).iloc[0]
    repaired_lang = pd.read_csv(REPAIRED_LANG_PATH)

    # Filter historical 45 summaries
    hist_45 = hist_sums[
        (hist_sums["document_id"].isin(BENCH_DOCS)) &
        (hist_sums["model_id"] == "qwen3-4b-instruct") &
        (hist_sums["prompt_condition"] == "condition_c")
    ].copy().reset_index(drop=True)

    logger.info("Loaded %d historical benchmark summaries.", len(hist_45))

    # Evaluate historical summaries against 85 gold facts
    # Map historical retrieval status for each fact
    hist_ret_map = dict(zip(hist_eval_ret["fact_id"], hist_eval_ret["retrieval_status"]))

    hist_eval_records = []
    # Pass 1: English evaluation for R3 mapping
    en_hist_map = {}
    for _, s_row in hist_45[hist_45["language"] == "en"].iterrows():
        doc_id = s_row["document_id"]
        doc_gold = gold_df[gold_df["doc_id"] == doc_id]
        for _, f_row in doc_gold.iterrows():
            fid = f_row["gold_fact_id"]
            st, reas = evaluate_fact_preservation(f_row, s_row["summary_text"], "en", "")
            en_hist_map[(doc_id, fid)] = st

    # Pass 2: All 45 historical summaries
    for _, s_row in hist_45.iterrows():
        doc_id = s_row["document_id"]
        lang = s_row["language"]
        sum_text = s_row["summary_text"]
        doc_gold = gold_df[gold_df["doc_id"] == doc_id]

        for _, f_row in doc_gold.iterrows():
            fid = f_row["gold_fact_id"]
            cat = f_row["category"]
            crit = f_row["criticality"]
            norm = f_row["normalized_value"]
            ret_status = hist_ret_map.get(fid, "NOT_RETRIEVED")
            is_retrieved = ret_status == "RETRIEVED_SUPPORTED"

            status, reason = evaluate_fact_preservation(f_row, sum_text, lang, "")

            failure_stage = "SUCCESS_GROUNDED"
            if status in ["OMITTED", "CONTRADICTED", "UNSUPPORTED"]:
                if not is_retrieved:
                    failure_stage = "R1_RETRIEVAL_FAILURE"
                else:
                    en_st = en_hist_map.get((doc_id, fid), "OMITTED")
                    if en_st != "SUPPORTED":
                        failure_stage = "R2_GENERATION_FAILURE"
                    else:
                        failure_stage = "R3_MULTILINGUAL_FAILURE"

            hist_eval_records.append({
                "doc_id": doc_id,
                "language": lang,
                "fact_id": fid,
                "category": cat,
                "criticality": crit,
                "normalized_value": norm,
                "retrieval_status": ret_status,
                "summary_preservation_status": status,
                "is_legal_outcome": cat in LEGAL_OUTCOME_CATEGORIES,
                "failure_stage": failure_stage
            })

    hist_eval_df = pd.DataFrame(hist_eval_records)

    # 1. Overall Comparison Metrics
    tot_hist = len(hist_eval_df)
    hist_supp = (hist_eval_df["summary_preservation_status"] == "SUPPORTED").sum()
    hist_crit = hist_eval_df[hist_eval_df["criticality"] == "CRITICAL"]
    hist_crit_supp = (hist_crit["summary_preservation_status"] == "SUPPORTED").sum()
    hist_crit_omit = (hist_crit["summary_preservation_status"] == "OMITTED").sum()
    hist_contra = (hist_eval_df["summary_preservation_status"] == "CONTRADICTED").sum()
    hist_outcome = hist_eval_df[hist_eval_df["is_legal_outcome"]]
    hist_outcome_supp = (hist_outcome["summary_preservation_status"] == "SUPPORTED").sum()
    hist_disp = hist_eval_df[hist_eval_df["category"] == "DISPOSITION"]
    hist_disp_supp = (hist_disp["summary_preservation_status"] == "SUPPORTED").sum()
    hist_sec = hist_eval_df[hist_eval_df["category"].isin(["STATUTORY_SECTION", "CHARGE"])]
    hist_sec_supp = (hist_sec["summary_preservation_status"] == "SUPPORTED").sum()

    # Old rates
    old_overall = round(hist_supp / tot_hist, 4)
    old_crit_pres = round(hist_crit_supp / len(hist_crit), 4)
    old_crit_omit = round(hist_crit_omit / len(hist_crit), 4)
    old_contra = round(hist_contra / tot_hist, 4)
    old_disp = round(hist_disp_supp / len(hist_disp), 4)
    old_stat = round(hist_sec_supp / len(hist_sec), 4)
    old_outcome = round(hist_outcome_supp / len(hist_outcome), 4)

    # Repaired rates
    new_overall = float(repaired_overall["overall_preservation_rate"])
    new_crit_pres = float(repaired_overall["critical_preservation_rate"])
    new_crit_omit = float(repaired_overall["critical_omission_rate"])
    new_contra = float(repaired_overall["contradiction_rate"])
    new_disp = float(repaired_overall["disposition_preservation_rate"])
    new_stat = float(repaired_overall["statutory_preservation_rate"])
    new_outcome = float(repaired_overall["legal_outcome_preservation_rate"])

    comp_metrics = [
        ("Overall Fact Preservation", old_overall, new_overall),
        ("Critical Fact Preservation", old_crit_pres, new_crit_pres),
        ("Critical Omission", old_crit_omit, new_crit_omit),
        ("Contradiction", old_contra, new_contra),
        ("Disposition Preservation", old_disp, new_disp),
        ("Statutory Preservation", old_stat, new_stat),
        ("Legal Outcome Preservation", old_outcome, new_outcome)
    ]

    comp_rows = []
    for metric_name, old_val, new_val in comp_metrics:
        abs_change = round(new_val - old_val, 4)
        rel_change = round((abs_change / old_val) * 100.0, 2) if old_val > 0 else (100.0 if new_val > 0 else 0.0)
        comp_rows.append({
            "metric": metric_name,
            "historical_head_4": old_val,
            "historical_head_4_pct": f"{old_val * 100:.1f}%",
            "repaired_bm25_b8": new_val,
            "repaired_bm25_b8_pct": f"{new_val * 100:.1f}%",
            "absolute_change": abs_change,
            "absolute_change_pct": f"{abs_change * 100:+.1f}%",
            "relative_change_pct": f"{rel_change:+.1f}%"
        })

    comp_df = pd.DataFrame(comp_rows)
    comp_df.to_csv(COMP_DIR / "old_vs_repaired.csv", index=False)
    logger.info("Saved %s", COMP_DIR / "old_vs_repaired.csv")

    # 2. Per-Language Comparison
    lang_comp_rows = []
    for lang in ["en", "ta", "hi", "kn", "mr"]:
        h_sub = hist_eval_df[hist_eval_df["language"] == lang]
        h_crit = h_sub[h_sub["criticality"] == "CRITICAL"]
        h_out = h_sub[h_sub["is_legal_outcome"]]

        h_ov = round((h_sub["summary_preservation_status"] == "SUPPORTED").sum() / len(h_sub), 4)
        h_cr = round((h_crit["summary_preservation_status"] == "SUPPORTED").sum() / len(h_crit), 4)
        h_om = round((h_crit["summary_preservation_status"] == "OMITTED").sum() / len(h_crit), 4)
        h_ot = round((h_out["summary_preservation_status"] == "SUPPORTED").sum() / len(h_out), 4)

        r_sub = repaired_lang[repaired_lang["language"] == lang].iloc[0]
        r_ov = float(r_sub["overall_preservation"])
        r_cr = float(r_sub["critical_preservation"])
        r_om = float(r_sub["critical_omission"])
        r_ot = float(r_sub["legal_outcome_preservation"])

        lang_comp_rows.append({
            "language": lang,
            "old_overall_preservation": h_ov,
            "new_overall_preservation": r_ov,
            "overall_change": round(r_ov - h_ov, 4),
            "old_critical_preservation": h_cr,
            "new_critical_preservation": r_cr,
            "critical_change": round(r_cr - h_cr, 4),
            "old_critical_omission": h_om,
            "new_critical_omission": r_om,
            "omission_change": round(r_om - h_om, 4),
            "old_legal_outcome_preservation": h_ot,
            "new_legal_outcome_preservation": r_ot,
            "outcome_change": round(r_ot - h_ot, 4)
        })

    lang_comp_df = pd.DataFrame(lang_comp_rows)
    lang_comp_df.to_csv(COMP_DIR / "old_vs_repaired_by_language.csv", index=False)
    logger.info("Saved %s", COMP_DIR / "old_vs_repaired_by_language.csv")

    # 3. Failure Shift Analysis
    # Compare failure stages between historical and repaired runs
    hist_fail_counts = hist_eval_df["failure_stage"].value_counts().to_dict()
    repaired_fail_counts = repaired_eval["failure_stage"].value_counts().to_dict()

    all_stages = ["SUCCESS_GROUNDED", "R1_RETRIEVAL_FAILURE", "R2_GENERATION_FAILURE", "R3_MULTILINGUAL_FAILURE"]
    shift_rows = []
    for stage in all_stages:
        old_c = hist_fail_counts.get(stage, 0)
        new_c = repaired_fail_counts.get(stage, 0)
        delta = new_c - old_c
        shift_rows.append({
            "stage": stage,
            "historical_head_4_count": old_c,
            "historical_pct": f"{old_c / tot_hist * 100:.1f}%",
            "repaired_bm25_b8_count": new_c,
            "repaired_pct": f"{new_c / tot_hist * 100:.1f}%",
            "delta_count": delta,
            "delta_pct": f"{delta / tot_hist * 100:+.1f}%"
        })

    shift_df = pd.DataFrame(shift_rows)
    shift_df.to_csv(COMP_DIR / "failure_shift.csv", index=False)
    logger.info("Saved %s", COMP_DIR / "failure_shift.csv")

    return comp_df, lang_comp_df, shift_df


if __name__ == "__main__":
    run_comparison()
