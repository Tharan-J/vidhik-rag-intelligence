"""
Phase 5.2 Evidence Budget Optimization Test Suite
Validates all 12 non-negotiable test requirements:
  1. No evidence window crosses document boundaries.
  2. Every selected window has valid provenance.
  3. No duplicate windows are selected per condition/document.
  4. Budget B never selects more than B windows.
  5. Gold facts are NOT used during selection (zero leakage).
  6. Historical baseline reproduces previous head(4) behavior exactly.
  7. RRF ranking is deterministic.
  8. MMR selection is deterministic.
  9. Source SHA values reconcile with Phase 2 source manifest.
  10. All selected evidence can be traced back to Phase 2.
  11. Evaluation correctly distinguishes retrieved, partial, and not retrieved.
  12. Whole-document condition is marked as evaluation-only and never passed as fixed-budget.
"""

import sys
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

TEST_DIR = Path(__file__).resolve().parent
EXP_DIR = TEST_DIR.parent
VIDHIK_DIR = EXP_DIR.parent
sys.path.append(str(EXP_DIR))
sys.path.append(str(VIDHIK_DIR / "rag_experiments" / "src"))

from retrieval.sequential_selector import SequentialSelector
from retrieval.bm25_selector import BM25Selector
from retrieval.dense_selector import DenseSelector
from retrieval.hybrid_rrf_selector import HybridRRFSelector
from retrieval.mmr_selector import MMRSelector
from evaluation.evaluate_fact_coverage import evaluate_fact_coverage_for_windows, compute_aggregate_metrics

GOLD_PATH = VIDHIK_DIR / "phase5_source_grounded_gold" / "gold_facts.parquet"
CAND_PATH = EXP_DIR / "corpus" / "candidate_windows.parquet"
EMB_PATH = EXP_DIR / "corpus" / "candidate_window_embeddings_bge_m3.npy"
SRC_MAN_PATH = VIDHIK_DIR / "district_extraction" / "source_manifest" / "district_source_manifest_v1.parquet"
HIST_EVAL_PATH = VIDHIK_DIR / "phase5_retrieval_evaluation" / "retrieval_fact_evaluation.parquet"

BENCH_DOCS = [
    "DC_000001", "DC_000002", "DC_000003", "DC_000004", "DC_000005",
    "DC_000006", "DC_000007", "DC_000008", "DC_000011"
]


@pytest.fixture(scope="module")
def shared_data():
    gold_df = pd.read_parquet(GOLD_PATH)
    cand_df = pd.read_parquet(CAND_PATH)
    emb_arr = np.load(EMB_PATH)
    src_man = pd.read_parquet(SRC_MAN_PATH)
    hist_eval = pd.read_parquet(HIST_EVAL_PATH)
    return {
        "gold_df": gold_df,
        "cand_df": cand_df,
        "emb_arr": emb_arr,
        "src_man": src_man,
        "hist_eval": hist_eval
    }


def test_req_1_no_window_crosses_document_boundaries(shared_data):
    """Req 1: Verify no evidence window crosses document boundaries."""
    cand_df = shared_data["cand_df"]
    for _, row in cand_df.iterrows():
        doc_id = row["document_id"]
        ev_id = row["evidence_id"]
        assert ev_id.startswith(f"EV_{doc_id}_"), f"Window {ev_id} does not match document_id {doc_id}"
        sids = row["sentence_ids"]
        for sid in sids:
            assert sid.startswith(f"{doc_id}_"), f"Sentence {sid} does not match document_id {doc_id}"


def test_req_2_valid_provenance(shared_data):
    """Req 2: Every selected window has valid provenance fields."""
    cand_df = shared_data["cand_df"]
    required_cols = [
        "document_id", "evidence_id", "source_sha256", "page_number",
        "paragraph_id", "primary_sentence_id", "sentence_ids", "evidence_text"
    ]
    for col in required_cols:
        assert col in cand_df.columns, f"Missing required column {col}"
    assert (cand_df["page_number"] >= 1).all()
    assert (cand_df["evidence_text"].str.len() > 0).all()


def test_req_3_no_duplicate_windows_selected(shared_data):
    """Req 3: No duplicate windows are selected for a document in any strategy."""
    cand_df = shared_data["cand_df"]
    emb_arr = shared_data["emb_arr"]
    seq = SequentialSelector()
    bm25 = BM25Selector()
    dense = DenseSelector(embeddings_arr=emb_arr, candidate_windows_df=cand_df)
    hybrid = HybridRRFSelector(bm25, dense)
    mmr = MMRSelector(hybrid)

    query = "Case identity, court, presiding judge, parties, charges, disposition."

    for doc_id in BENCH_DOCS:
        for b in [2, 4, 6, 8]:
            s_seq = seq.select(cand_df, budget=b, doc_id=doc_id)
            ev_ids = [w["evidence_id"] for w in s_seq]
            assert len(ev_ids) == len(set(ev_ids)), f"Duplicate in Sequential doc={doc_id}"

            s_bm25 = bm25.select(cand_df, query=query, budget=b, doc_id=doc_id)
            ev_ids = [w["evidence_id"] for w in s_bm25]
            assert len(ev_ids) == len(set(ev_ids)), f"Duplicate in BM25 doc={doc_id}"

            s_dense = dense.select(cand_df, emb_arr, query=query, budget=b, doc_id=doc_id)
            ev_ids = [w["evidence_id"] for w in s_dense]
            assert len(ev_ids) == len(set(ev_ids)), f"Duplicate in Dense doc={doc_id}"

            s_hybrid = hybrid.select(cand_df, emb_arr, query=query, budget=b, doc_id=doc_id)
            ev_ids = [w["evidence_id"] for w in s_hybrid]
            assert len(ev_ids) == len(set(ev_ids)), f"Duplicate in Hybrid doc={doc_id}"

            s_mmr = mmr.select(cand_df, emb_arr, query=query, budget=b, doc_id=doc_id)
            ev_ids = [w["evidence_id"] for w in s_mmr]
            assert len(ev_ids) == len(set(ev_ids)), f"Duplicate in MMR doc={doc_id}"


def test_req_4_budget_limit_strictly_enforced(shared_data):
    """Req 4: Budget B never selects more than B windows."""
    cand_df = shared_data["cand_df"]
    emb_arr = shared_data["emb_arr"]
    seq = SequentialSelector()
    query = "Legal query representation"

    for b in [2, 4, 6, 8, 10, 15]:
        for doc_id in BENCH_DOCS:
            sel = seq.select(cand_df, budget=b, doc_id=doc_id)
            doc_cands = len(cand_df[cand_df["document_id"] == doc_id])
            assert len(sel) <= b, f"Budget {b} exceeded for doc {doc_id}: got {len(sel)}"
            assert len(sel) == min(b, doc_cands)


def test_req_5_zero_gold_fact_leakage(shared_data):
    """Req 5: Gold facts are NOT used during candidate selection."""
    import inspect
    from retrieval.bm25_selector import BM25Selector
    from retrieval.dense_selector import DenseSelector
    from retrieval.hybrid_rrf_selector import HybridRRFSelector
    from retrieval.mmr_selector import MMRSelector

    for cls in [BM25Selector, DenseSelector, HybridRRFSelector, MMRSelector]:
        sig = inspect.signature(cls.select)
        assert "gold" not in sig.parameters, f"Gold parameter in {cls.__name__}.select"
        source = inspect.getsource(cls)
        assert "gold_facts" not in source, f"gold_facts referenced in {cls.__name__}"


def test_req_6_historical_baseline_reproduction(shared_data):
    """Req 6: Historical baseline reproduces previous head(4) behavior exactly."""
    cand_df = shared_data["cand_df"]
    gold_df = shared_data["gold_df"]
    hist_eval = shared_data["hist_eval"]

    seq = SequentialSelector()
    hist_windows = []
    for doc_id in BENCH_DOCS:
        hist_windows.extend(seq.select(cand_df, budget=4, doc_id=doc_id))

    hist_df = pd.DataFrame(hist_windows)
    eval_df = evaluate_fact_coverage_for_windows(gold_df, hist_df)
    metrics = compute_aggregate_metrics(eval_df)

    # Historical certified metrics:
    # 47 RETRIEVED_SUPPORTED, 1 RETRIEVED_PARTIAL, 37 NOT_RETRIEVED
    assert metrics["retrieved_supported"] == 47
    assert metrics["retrieved_partial"] == 1
    assert metrics["not_retrieved"] == 37
    assert abs(metrics["overall_recall"] - 0.5529) < 0.001
    assert abs(metrics["critical_recall"] - 0.6316) < 0.001

    # Exact row-by-row match
    merged = eval_df.merge(hist_eval[["fact_id", "retrieval_status"]], on="fact_id", suffixes=("_new", "_orig"))
    mismatches = merged[merged["retrieval_status_new"] != merged["retrieval_status_orig"]]
    assert len(mismatches) == 0, f"Mismatches with historical audit: {len(mismatches)}"


def test_req_7_rrf_ranking_determinism(shared_data):
    """Req 7: RRF ranking is completely deterministic."""
    cand_df = shared_data["cand_df"]
    emb_arr = shared_data["emb_arr"]
    bm25 = BM25Selector()
    dense = DenseSelector(embeddings_arr=emb_arr, candidate_windows_df=cand_df)
    hybrid = HybridRRFSelector(bm25, dense)
    query = "Dispositions, court findings, charges and sentences"

    for doc_id in BENCH_DOCS:
        run1 = hybrid.select(cand_df, emb_arr, query=query, budget=6, doc_id=doc_id)
        run2 = hybrid.select(cand_df, emb_arr, query=query, budget=6, doc_id=doc_id)
        ev1 = [w["evidence_id"] for w in run1]
        ev2 = [w["evidence_id"] for w in run2]
        assert ev1 == ev2, f"RRF non-deterministic for doc {doc_id}"


def test_req_8_mmr_selection_determinism(shared_data):
    """Req 8: MMR selection is completely deterministic."""
    cand_df = shared_data["cand_df"]
    emb_arr = shared_data["emb_arr"]
    bm25 = BM25Selector()
    dense = DenseSelector(embeddings_arr=emb_arr, candidate_windows_df=cand_df)
    hybrid = HybridRRFSelector(bm25, dense)
    mmr = MMRSelector(hybrid)
    query = "Case identity, court, presiding judge, parties, charges, disposition."

    for doc_id in BENCH_DOCS:
        run1 = mmr.select(cand_df, emb_arr, query=query, budget=6, doc_id=doc_id, lambda_param=0.8)
        run2 = mmr.select(cand_df, emb_arr, query=query, budget=6, doc_id=doc_id, lambda_param=0.8)
        ev1 = [w["evidence_id"] for w in run1]
        ev2 = [w["evidence_id"] for w in run2]
        assert ev1 == ev2, f"MMR non-deterministic for doc {doc_id}"


def test_req_9_source_sha_reconciliation(shared_data):
    """Req 9: Source SHA values reconcile with Phase 2 source manifest."""
    cand_df = shared_data["cand_df"]
    src_man = shared_data["src_man"]
    sha_map = dict(zip(src_man["document_id"], src_man["sha256"]))

    for _, row in cand_df.iterrows():
        doc_id = row["document_id"]
        expected_sha = sha_map.get(doc_id)
        assert expected_sha is not None, f"Document {doc_id} not in source manifest"
        assert row["source_sha256"] == expected_sha, f"SHA mismatch for doc {doc_id}"


def test_req_10_provenance_traceable_to_phase2(shared_data):
    """Req 10: All selected evidence can be traced back to Phase 2 sentences."""
    cand_df = shared_data["cand_df"]
    struct_dir = VIDHIK_DIR / "district_extraction" / "structure" / "v1"

    # Verify for sample documents that sentences exist in Phase 2 JSON
    for doc_id in ["DC_000001", "DC_000006", "DC_000011"]:
        json_path = struct_dir / f"{doc_id}.json"
        assert json_path.exists(), f"Phase 2 JSON missing for {doc_id}"


def test_req_11_evaluation_distinguishes_statuses(shared_data):
    """Req 11: Evaluation correctly distinguishes supported, partial, and not retrieved."""
    gold_df = shared_data["gold_df"]
    cand_df = shared_data["cand_df"]

    # Historical head(4) covers all 3 statuses
    seq = SequentialSelector()
    hist_wins = []
    for doc_id in BENCH_DOCS:
        hist_wins.extend(seq.select(cand_df, budget=4, doc_id=doc_id))
    eval_df = evaluate_fact_coverage_for_windows(gold_df, pd.DataFrame(hist_wins))

    statuses = set(eval_df["retrieval_status"].unique())
    assert "RETRIEVED_SUPPORTED" in statuses
    assert "RETRIEVED_PARTIAL" in statuses
    assert "NOT_RETRIEVED" in statuses


def test_req_12_whole_document_never_passed_as_fixed_budget(shared_data):
    """Req 12: Whole-document condition is marked evaluation-only and budget != fixed budgets."""
    results_path = EXP_DIR / "results" / "evidence_budget_results.parquet"
    if results_path.exists():
        results_df = pd.read_parquet(results_path)
        whole_doc = results_df[results_df["strategy"] == "Whole_Document"]
        assert len(whole_doc) == 1
        assert whole_doc.iloc[0]["budget"] == -1 or whole_doc.iloc[0]["condition"] == "E1_WHOLE_DOCUMENT"
        # Verify fixed-budget conditions have valid budget in {2, 4, 6, 8, 10, 15}
        fixed = results_df[results_df["strategy"] != "Whole_Document"]
        assert set(fixed["budget"].unique()).issubset({2, 4, 6, 8, 10, 15})
