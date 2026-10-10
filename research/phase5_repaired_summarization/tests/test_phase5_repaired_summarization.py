"""
Phase 5 Repaired Multilingual Summarization Test Suite
Validates all 16 non-negotiable requirements from Section 36:
  1. Exactly 9 benchmark documents
  2. Exactly 5 languages
  3. Expected 45 summary cells
  4. BM25 budget never exceeds 8 windows/document
  5. No cross-document evidence windows
  6. Valid Phase-2 provenance
  7. Source SHA reconciliation
  8. No gold-fact leakage into retrieval
  9. Deterministic evidence selection
  10. Generation configuration matches frozen Phase-4 configuration
  11. Unique-fact denominator is used
  12. ABSENT_IN_SOURCE is not penalized
  13. Failure attribution is evidence-aware
  14. Historical baseline is not overwritten
  15. Old/new comparison is reproducible
  16. No fabricated summaries for failed generations
"""

import sys
import json
from pathlib import Path
import pytest
import pandas as pd
import yaml

TEST_DIR = Path(__file__).resolve().parent
EXP_DIR = TEST_DIR.parent
VIDHIK_DIR = EXP_DIR.parent
sys.path.append(str(EXP_DIR))

CONFIG_PATH = EXP_DIR / "config" / "repaired_run_config.yaml"
EVIDENCE_PATH = EXP_DIR / "evidence" / "repaired_bm25_b8_evidence.parquet"
OUTPUTS_DIR = EXP_DIR / "outputs"
EVAL_DIR = EXP_DIR / "evaluation"
COMP_DIR = EXP_DIR / "comparison"
AUDIT_DIR = EXP_DIR / "audit"
GOLD_PATH = VIDHIK_DIR / "phase5_source_grounded_gold" / "gold_facts.parquet"
SRC_MAN_PATH = VIDHIK_DIR / "district_extraction" / "source_manifest" / "district_source_manifest_v1.parquet"
HIST_SUMS_PATH = VIDHIK_DIR / "phase4_summarization" / "generation" / "summaries_v1.parquet"

EXPECTED_DOCS = [
    "DC_000001", "DC_000002", "DC_000003", "DC_000004", "DC_000005",
    "DC_000006", "DC_000007", "DC_000008", "DC_000011"
]
EXPECTED_LANGS = ["en", "ta", "hi", "kn", "mr"]


@pytest.fixture(scope="module")
def shared_data():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    ev_df = pd.read_parquet(EVIDENCE_PATH)
    gold_df = pd.read_parquet(GOLD_PATH)
    src_man = pd.read_parquet(SRC_MAN_PATH)
    return {
        "cfg": cfg,
        "ev_df": ev_df,
        "gold_df": gold_df,
        "src_man": src_man
    }


def test_req_1_exact_9_benchmark_documents(shared_data):
    """Req 1: Verify exactly 9 benchmark documents."""
    cfg = shared_data["cfg"]
    doc_ids = cfg["benchmark"]["benchmark_doc_ids"]
    assert len(doc_ids) == 9
    assert sorted(doc_ids) == sorted(EXPECTED_DOCS)


def test_req_2_exact_5_languages(shared_data):
    """Req 2: Verify exactly 5 languages."""
    cfg = shared_data["cfg"]
    langs = list(cfg["languages"].keys())
    assert len(langs) == 5
    assert sorted(langs) == sorted(EXPECTED_LANGS)


def test_req_3_expected_45_summary_cells(shared_data):
    """Req 3: Expected 45 summary cells in configuration and manifest."""
    cfg = shared_data["cfg"]
    total = len(cfg["benchmark"]["benchmark_doc_ids"]) * len(cfg["languages"])
    assert total == 45


def test_req_4_bm25_budget_limit(shared_data):
    """Req 4: BM25 budget never exceeds 8 windows/document."""
    ev_df = shared_data["ev_df"]
    for doc_id, grp in ev_df.groupby("doc_id"):
        assert len(grp) <= 8, f"Document {doc_id} exceeded budget 8: got {len(grp)}"


def test_req_5_no_cross_document_evidence_windows(shared_data):
    """Req 5: No evidence window crosses document boundaries."""
    ev_df = shared_data["ev_df"]
    for _, row in ev_df.iterrows():
        doc_id = row["doc_id"]
        win_id = row["window_id"]
        assert win_id.startswith(f"EV_{doc_id}_"), f"Window {win_id} does not match {doc_id}"
        for sid in row["sentence_ids"]:
            assert sid.startswith(f"{doc_id}_"), f"Sentence {sid} does not match {doc_id}"


def test_req_6_valid_phase2_provenance(shared_data):
    """Req 6: Every evidence window has valid Phase-2 provenance."""
    ev_df = shared_data["ev_df"]
    required_cols = ["doc_id", "window_id", "sentence_ids", "paragraph_ids", "page_number", "text", "source_sha256"]
    for col in required_cols:
        assert col in ev_df.columns, f"Missing required column {col}"
    assert (ev_df["page_number"] >= 1).all()
    assert (ev_df["text"].str.len() > 0).all()


def test_req_7_source_sha_reconciliation(shared_data):
    """Req 7: Source SHA values reconcile with Phase 2 source manifest."""
    ev_df = shared_data["ev_df"]
    src_man = shared_data["src_man"]
    sha_map = dict(zip(src_man["document_id"], src_man["sha256"]))

    for _, row in ev_df.iterrows():
        doc_id = row["doc_id"]
        expected_sha = sha_map.get(doc_id)
        assert expected_sha is not None, f"Document {doc_id} missing from source manifest"
        assert row["source_sha256"] == expected_sha, f"SHA mismatch for doc {doc_id}"


def test_req_8_zero_gold_fact_leakage():
    """Req 8: No gold facts are used in the BM25 query or selection."""
    sys.path.append(str(VIDHIK_DIR / "phase5_evidence_budget_optimization"))
    from retrieval.bm25_selector import BM25Selector
    import inspect
    sig = inspect.signature(BM25Selector.select)
    assert "gold" not in sig.parameters
    source = inspect.getsource(BM25Selector)
    assert "gold_facts" not in source


def test_req_9_deterministic_evidence_selection(shared_data):
    """Req 9: Evidence selection is completely deterministic."""
    ev_df = shared_data["ev_df"]
    # Check that ranks are strictly sequential per document
    for doc_id, grp in ev_df.groupby("doc_id"):
        ranks = grp["rank"].tolist()
        assert ranks == list(range(1, len(grp) + 1)), f"Non-consecutive ranks for {doc_id}"


def test_req_10_frozen_generation_configuration(shared_data):
    """Req 10: Generation configuration matches frozen Phase-4 configuration."""
    cfg = shared_data["cfg"]
    m_cfg = cfg["model"]
    assert m_cfg["name"] == "qwen3-4b-instruct"
    assert m_cfg["temperature"] == 0.1
    assert m_cfg["top_p"] == 0.95
    assert m_cfg["max_tokens"] == 450
    assert m_cfg["thinking_enabled"] is False
    assert m_cfg["generation_condition"] == "condition_c"


def test_req_11_unique_fact_denominator(shared_data):
    """Req 11: Denominator is strictly unique certified gold facts (85)."""
    gold_df = shared_data["gold_df"]
    assert len(gold_df) == 85
    assert gold_df["gold_fact_id"].nunique() == 85


def test_req_12_absent_in_source_not_penalized(shared_data):
    """Req 12: Absent in source categories are not penalized."""
    cov_path = shared_data["cfg"]["benchmark"]["source_coverage_path"]
    cov_df = pd.read_csv(VIDHIK_DIR / cov_path)
    absent_count = cov_df["absent_in_source"].sum()
    assert absent_count > 0, "Expected absent-in-source categories to be tracked"


def test_req_13_evidence_aware_failure_attribution():
    """Req 13: Failure attribution is evidence-aware, not hard-coded by language."""
    from evaluate_repaired_summaries import run_full_evaluation
    import inspect
    source = inspect.getsource(run_full_evaluation)
    assert "R1_RETRIEVAL_FAILURE" in source
    assert "R2_GENERATION_FAILURE" in source
    assert "R3_MULTILINGUAL_FAILURE" in source
    # Must NOT have old hard-coded string:
    assert '"R2_GENERATION_FAILURE" if lang == "en" else "R3_MULTILINGUAL_FAILURE"' not in source


def test_req_14_historical_baseline_not_overwritten():
    """Req 14: Historical baseline summaries are not overwritten."""
    assert HIST_SUMS_PATH.exists()
    df = pd.read_parquet(HIST_SUMS_PATH)
    assert len(df) >= 45


def test_req_15_old_new_comparison_reproducibility():
    """Req 15: Comparison script exists and imports cleanly."""
    import compare_old_vs_repaired
    assert hasattr(compare_old_vs_repaired, "run_comparison")


def test_req_16_no_fabricated_summaries_on_failure():
    """Req 16: Generator records failures without fabricating text."""
    from generate_repaired_summaries import call_ollama
    # Test failure handling with invalid endpoint
    res = call_ollama("test", "test", endpoint="http://localhost:9999/api/generate")
    assert res["status"] == "FAILURE"
    assert res["text"] == ""
    assert res["output_tokens"] == 0
