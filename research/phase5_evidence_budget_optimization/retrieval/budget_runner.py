"""
Evidence Budget Optimization Experiment Runner for Vidhik Phase 5.2
Executes all experimental conditions:
  - E0: Historical Baseline (head(4))
  - E1: Whole Document Upper Bound (all candidate windows; evaluation-only)
  - E2: Fixed Sequential Budget (B in {2, 4, 6, 8, 10, 15})
  - E3: BM25 Retrieval (B in {2, 4, 6, 8, 10, 15})
  - E4: Dense BGE-M3 Retrieval (B in {2, 4, 6, 8, 10, 15})
  - E5: Hybrid BM25 + Dense RRF (B in {2, 4, 6, 8, 10, 15})
  - E6: Hybrid + MMR Diversity Selector (lambdas 0.7, 0.8, 0.9; B in {2, 4, 6, 8, 10, 15})

Saves:
  - results/evidence_budget_results.parquet & .csv
  - results/selected_evidence_manifest.parquet & .csv
  - results/oracle_budget_analysis.csv
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List, Any
import numpy as np
import pandas as pd
import yaml

# Add project root and local modules to path
EXPERIMENT_ROOT = Path(__file__).resolve().parent.parent
VIDHIK_ROOT = EXPERIMENT_ROOT.parent
sys.path.append(str(EXPERIMENT_ROOT))
sys.path.append(str(VIDHIK_ROOT / "rag_experiments" / "src"))

from retrieval.sequential_selector import SequentialSelector
from retrieval.bm25_selector import BM25Selector
from retrieval.dense_selector import DenseSelector
from retrieval.hybrid_rrf_selector import HybridRRFSelector
from retrieval.mmr_selector import MMRSelector

from evaluation.evaluate_fact_coverage import evaluate_fact_coverage_for_windows, compute_aggregate_metrics
from evaluation.evaluate_category_coverage import compute_category_coverage, compute_document_coverage
from evaluation.evaluate_budget_efficiency import compute_evidence_budget_metrics
from evaluation.evaluate_saturation import analyze_saturation, run_oracle_analysis

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("P5_2_BudgetRunner")


def load_config() -> Dict[str, Any]:
    config_path = EXPERIMENT_ROOT / "config" / "evidence_budget_config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_experiment():
    logger.info("Initializing Phase 5.2 Evidence Budget Optimization Experiment...")
    cfg = load_config()

    # Load certified gold facts (immutable)
    gold_path = VIDHIK_ROOT / cfg["benchmark"]["gold_facts_path"]
    gold_facts_df = pd.read_parquet(gold_path)
    logger.info("Loaded %d certified gold facts from %s", len(gold_facts_df), gold_path)

    # Load candidate windows
    cand_path = EXPERIMENT_ROOT / "corpus" / "candidate_windows.parquet"
    if not cand_path.exists():
        # Fallback to phase4_evidence
        cand_path = VIDHIK_ROOT / cfg["benchmark"]["candidate_evidence_path"]
        p4_ev = pd.read_parquet(cand_path)
        cand_df = p4_ev[p4_ev["document_id"].isin(cfg["benchmark"]["benchmark_doc_ids"])].copy().reset_index(drop=True)
    else:
        cand_df = pd.read_parquet(cand_path)
    logger.info("Loaded %d candidate windows across 9 benchmark documents.", len(cand_df))

    # Load precomputed BGE-M3 embeddings
    emb_path = EXPERIMENT_ROOT / "corpus" / "candidate_window_embeddings_bge_m3.npy"
    embeddings_arr = np.load(emb_path)
    logger.info("Loaded candidate embeddings of shape %s from %s", str(embeddings_arr.shape), emb_path)

    # Initialize selectors
    seq_selector = SequentialSelector(strategy_name="SEQUENTIAL")
    bm25_selector = BM25Selector(
        k1=cfg["bm25"]["k1"],
        b=cfg["bm25"]["b"],
        epsilon=cfg["bm25"]["epsilon"],
        strategy_name="BM25"
    )
    dense_selector = DenseSelector(
        embeddings_arr=embeddings_arr,
        candidate_windows_df=cand_df,
        strategy_name="DENSE_BGE_M3"
    )
    hybrid_selector = HybridRRFSelector(
        bm25_selector=bm25_selector,
        dense_selector=dense_selector,
        k=cfg["rrf"]["k"],
        dense_weight=cfg["rrf"]["dense_weight"],
        bm25_weight=cfg["rrf"]["bm25_weight"],
        strategy_name="HYBRID_RRF"
    )
    mmr_selector = MMRSelector(
        hybrid_selector=hybrid_selector,
        lambda_param=cfg["mmr"]["default_lambda"],
        strategy_name="HYBRID_MMR"
    )

    bench_docs = cfg["benchmark"]["benchmark_doc_ids"]
    budgets = cfg["budgets"]  # [2, 4, 6, 8, 10, 15]
    base_query = cfg["query"]["base_task_query"]

    # Manifest of all selected evidence windows
    all_selected_manifest_records = []

    # Results table records
    results_records = []

    # --- Condition E0: Historical Baseline (head(4)) ---
    logger.info("Running Condition E0: Historical Baseline (head(4))...")
    e0_windows = []
    for doc_id in bench_docs:
        selected = seq_selector.select(cand_df, budget=4, doc_id=doc_id)
        for s in selected:
            s["experiment_condition"] = "E0_HISTORICAL"
            s["strategy"] = "Historical"
            s["budget"] = 4
        e0_windows.extend(selected)

    e0_df = pd.DataFrame(e0_windows)
    all_selected_manifest_records.extend(e0_windows)

    e0_eval = evaluate_fact_coverage_for_windows(gold_facts_df, e0_df)
    e0_metrics = compute_aggregate_metrics(e0_eval)
    e0_budget_metrics = compute_evidence_budget_metrics(
        e0_df, e0_metrics["overall_recall"], e0_metrics["critical_recall"]
    )

    results_records.append({
        "condition": "E0_HISTORICAL",
        "strategy": "Historical",
        "budget": 4,
        **e0_metrics,
        **e0_budget_metrics
    })

    # --- Condition E1: Whole Document Upper Bound (All Candidate Windows) ---
    logger.info("Running Condition E1: Whole Document Upper Bound...")
    e1_windows = []
    for doc_id in bench_docs:
        doc_wins = cand_df[cand_df["document_id"] == doc_id].copy().reset_index(drop=True)
        for r, (_, row) in enumerate(doc_wins.iterrows(), start=1):
            sids = row["sentence_ids"]
            sids_list = sids.tolist() if hasattr(sids, "tolist") else list(sids)
            e1_windows.append({
                "document_id": doc_id,
                "evidence_id": row["evidence_id"],
                "sentence_id": row["primary_sentence_id"],
                "sentence_ids": sids_list,
                "paragraph_id": row["paragraph_id"],
                "page_id": int(row["page_number"]),
                "page_number": int(row["page_number"]),
                "source_pdf_identifier": f"{doc_id}.pdf",
                "source_sha256": row["source_sha256"],
                "evidence_text": row["evidence_text"],
                "window_boundaries": f"{sids_list[0]}..{sids_list[-1]}" if len(sids_list) > 1 else sids_list[0],
                "retrieval_score": 1.0,
                "retrieval_strategy": "WHOLE_DOCUMENT_ORACLE",
                "budget": -1,
                "rank": r,
                "selection_reason": "Upper bound evaluation (all extracted document text available)",
                "experiment_condition": "E1_WHOLE_DOCUMENT",
                "strategy": "Whole_Document"
            })

    e1_df = pd.DataFrame(e1_windows)
    all_selected_manifest_records.extend(e1_windows)

    e1_eval = evaluate_fact_coverage_for_windows(gold_facts_df, e1_df)
    e1_metrics = compute_aggregate_metrics(e1_eval)
    e1_budget_metrics = compute_evidence_budget_metrics(
        e1_df, e1_metrics["overall_recall"], e1_metrics["critical_recall"]
    )

    results_records.append({
        "condition": "E1_WHOLE_DOCUMENT",
        "strategy": "Whole_Document",
        "budget": -1,  # Full document
        **e1_metrics,
        **e1_budget_metrics
    })

    # --- Condition E2: Fixed Sequential Budget ---
    logger.info("Running Condition E2: Fixed Sequential Budget...")
    for b in budgets:
        cond_wins = []
        for doc_id in bench_docs:
            selected = seq_selector.select(cand_df, budget=b, doc_id=doc_id)
            for s in selected:
                s["experiment_condition"] = f"E2_SEQUENTIAL_B{b}"
                s["strategy"] = "Sequential"
            cond_wins.extend(selected)

        cond_df = pd.DataFrame(cond_wins)
        all_selected_manifest_records.extend(cond_wins)

        eval_df = evaluate_fact_coverage_for_windows(gold_facts_df, cond_df)
        metrics = compute_aggregate_metrics(eval_df)
        b_metrics = compute_evidence_budget_metrics(
            cond_df, metrics["overall_recall"], metrics["critical_recall"]
        )

        results_records.append({
            "condition": f"E2_SEQUENTIAL_B{b}",
            "strategy": "Sequential",
            "budget": b,
            **metrics,
            **b_metrics
        })

    # --- Condition E3: BM25 Retrieval ---
    logger.info("Running Condition E3: BM25 Retrieval...")
    for b in budgets:
        cond_wins = []
        for doc_id in bench_docs:
            selected = bm25_selector.select(cand_df, query=base_query, budget=b, doc_id=doc_id)
            for s in selected:
                s["experiment_condition"] = f"E3_BM25_B{b}"
                s["strategy"] = "BM25"
            cond_wins.extend(selected)

        cond_df = pd.DataFrame(cond_wins)
        all_selected_manifest_records.extend(cond_wins)

        eval_df = evaluate_fact_coverage_for_windows(gold_facts_df, cond_df)
        metrics = compute_aggregate_metrics(eval_df)
        b_metrics = compute_evidence_budget_metrics(
            cond_df, metrics["overall_recall"], metrics["critical_recall"]
        )

        results_records.append({
            "condition": f"E3_BM25_B{b}",
            "strategy": "BM25",
            "budget": b,
            **metrics,
            **b_metrics
        })

    # --- Condition E4: Dense BGE-M3 Retrieval ---
    logger.info("Running Condition E4: Dense BGE-M3 Retrieval...")
    for b in budgets:
        cond_wins = []
        for doc_id in bench_docs:
            selected = dense_selector.select(
                cand_df, embeddings_arr, query=base_query, budget=b, doc_id=doc_id
            )
            for s in selected:
                s["experiment_condition"] = f"E4_DENSE_BGE_B{b}"
                s["strategy"] = "Dense_BGE_M3"
            cond_wins.extend(selected)

        cond_df = pd.DataFrame(cond_wins)
        all_selected_manifest_records.extend(cond_wins)

        eval_df = evaluate_fact_coverage_for_windows(gold_facts_df, cond_df)
        metrics = compute_aggregate_metrics(eval_df)
        b_metrics = compute_evidence_budget_metrics(
            cond_df, metrics["overall_recall"], metrics["critical_recall"]
        )

        results_records.append({
            "condition": f"E4_DENSE_BGE_B{b}",
            "strategy": "Dense_BGE_M3",
            "budget": b,
            **metrics,
            **b_metrics
        })

    # --- Condition E5: Hybrid BM25 + Dense RRF ---
    logger.info("Running Condition E5: Hybrid BM25 + Dense RRF...")
    for b in budgets:
        cond_wins = []
        for doc_id in bench_docs:
            selected = hybrid_selector.select(
                cand_df, embeddings_arr, query=base_query, budget=b, doc_id=doc_id
            )
            for s in selected:
                s["experiment_condition"] = f"E5_HYBRID_RRF_B{b}"
                s["strategy"] = "Hybrid_RRF"
            cond_wins.extend(selected)

        cond_df = pd.DataFrame(cond_wins)
        all_selected_manifest_records.extend(cond_wins)

        eval_df = evaluate_fact_coverage_for_windows(gold_facts_df, cond_df)
        metrics = compute_aggregate_metrics(eval_df)
        b_metrics = compute_evidence_budget_metrics(
            cond_df, metrics["overall_recall"], metrics["critical_recall"]
        )

        results_records.append({
            "condition": f"E5_HYBRID_RRF_B{b}",
            "strategy": "Hybrid_RRF",
            "budget": b,
            **metrics,
            **b_metrics
        })

    # --- Condition E6: Hybrid + MMR Diversity Selector ---
    logger.info("Running Condition E6: Hybrid + MMR Diversity Selector...")
    for lam in cfg["mmr"]["lambdas"]:  # [0.7, 0.8, 0.9]
        strategy_name = f"Hybrid_MMR_λ{lam}"
        for b in budgets:
            cond_wins = []
            for doc_id in bench_docs:
                selected = mmr_selector.select(
                    cand_df,
                    embeddings_arr,
                    query=base_query,
                    budget=b,
                    doc_id=doc_id,
                    lambda_param=lam
                )
                for s in selected:
                    s["experiment_condition"] = f"E6_MMR_LAMBDA_{lam}_B{b}"
                    s["strategy"] = strategy_name
                cond_wins.extend(selected)

            cond_df = pd.DataFrame(cond_wins)
            all_selected_manifest_records.extend(cond_wins)

            eval_df = evaluate_fact_coverage_for_windows(gold_facts_df, cond_df)
            metrics = compute_aggregate_metrics(eval_df)
            b_metrics = compute_evidence_budget_metrics(
                cond_df, metrics["overall_recall"], metrics["critical_recall"]
            )

            results_records.append({
                "condition": f"E6_MMR_LAMBDA_{lam}_B{b}",
                "strategy": strategy_name,
                "budget": b,
                **metrics,
                **b_metrics
            })

    # Save Results
    results_df = pd.DataFrame(results_records)
    results_dir = EXPERIMENT_ROOT / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    results_parquet_path = results_dir / "evidence_budget_results.parquet"
    results_csv_path = results_dir / "evidence_budget_results.csv"
    results_df.to_parquet(results_parquet_path, index=False)
    results_df.to_csv(results_csv_path, index=False)
    logger.info("Saved %d experimental results to %s and %s", len(results_df), results_parquet_path, results_csv_path)

    # Save Selected Evidence Manifest
    manifest_df = pd.DataFrame(all_selected_manifest_records)
    manifest_parquet_path = results_dir / "selected_evidence_manifest.parquet"
    manifest_csv_path = results_dir / "selected_evidence_manifest.csv"
    manifest_df.to_parquet(manifest_parquet_path, index=False)
    manifest_df.to_csv(manifest_csv_path, index=False)
    logger.info("Saved %d selected evidence rows to manifest: %s", len(manifest_df), manifest_parquet_path)

    # --- Run Oracle Analysis ---
    logger.info("Running ORACLE ANALYSIS — EVALUATION ONLY...")
    oracle_df = run_oracle_analysis(gold_facts_df, cand_df)
    oracle_csv_path = results_dir / "oracle_budget_analysis.csv"
    oracle_df.to_csv(oracle_csv_path, index=False)
    logger.info("Saved oracle analysis to %s", oracle_csv_path)

    # --- Run Saturation Analysis ---
    logger.info("Running Saturation Analysis...")
    saturation_df = analyze_saturation(results_df)
    saturation_csv_path = results_dir / "saturation_analysis.csv"
    saturation_df.to_csv(saturation_csv_path, index=False)
    logger.info("Saved saturation analysis to %s", saturation_csv_path)

    return results_df, manifest_df, oracle_df, saturation_df


if __name__ == "__main__":
    run_experiment()
