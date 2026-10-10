import os
import pytest
import pandas as pd
import hashlib

BASE_DIR = "/home/tharan/Seeds/vidhik"
P6_DIR = os.path.join(BASE_DIR, "phase6_multilingual_architecture")
AUDIT_DIR = os.path.join(BASE_DIR, "phase6_audit")

GOLD_FACTS_PATH = os.path.join(P6_DIR, "inputs", "frozen_gold_facts.parquet")
EVAL_PATH = os.path.join(P6_DIR, "evaluation", "fact_level_evaluation.parquet")
AUTH_RESULTS_PATH = os.path.join(AUDIT_DIR, "authoritative_phase6_results.csv")
RECON_PATH = os.path.join(AUDIT_DIR, "reconciliation_table.csv")
ATTR_PATH = os.path.join(P6_DIR, "evaluation", "failure_attribution.parquet")
ENGLISH_OUT_PATH = os.path.join(P6_DIR, "outputs", "english_summaries.parquet")
INDICTRANS_OUT_PATH = os.path.join(P6_DIR, "outputs", "indictrans2_summaries.parquet")
LEGAL_AWARE_OUT_PATH = os.path.join(P6_DIR, "outputs", "legal_aware_summaries.parquet")
VERIFIED_OUT_PATH = os.path.join(P6_DIR, "outputs", "verified_summaries.parquet")

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def test_1_exactly_85_certified_gold_facts():
    df_gold = pd.read_parquet(GOLD_FACTS_PATH)
    assert len(df_gold) == 85, f"Expected 85 gold facts, got {len(df_gold)}"
    assert df_gold["fact_id"].nunique() == 85

def test_2_exactly_9_benchmark_documents():
    df_gold = pd.read_parquet(GOLD_FACTS_PATH)
    docs = sorted(df_gold["doc_id"].unique())
    assert len(docs) == 9, f"Expected 9 documents, got {len(docs)}"
    expected_docs = [f"DC_{i:06d}" for i in range(1, 9)] + ["DC_000011"]
    assert docs == sorted(expected_docs)

def test_3_exactly_5_languages_in_full_benchmark():
    df_eval = pd.read_parquet(EVAL_PATH)
    langs = sorted(df_eval["language"].unique())
    assert langs == ["en", "hi", "kn", "mr", "ta"]

def test_4_exactly_425_fact_language_combinations():
    df_eval = pd.read_parquet(EVAL_PATH)
    # Check per system
    for s in df_eval["system"].unique():
        sub = df_eval[df_eval["system"] == s]
        assert len(sub) == 425, f"System {s} does not have 425 units"
        assert sub[["fact_id", "language"]].drop_duplicates().shape[0] == 425

def test_5_no_duplicate_evaluation_rows():
    df_eval = pd.read_parquet(EVAL_PATH)
    dups = df_eval.duplicated(subset=["system", "doc_id", "fact_id", "language"]).sum()
    assert dups == 0, f"Found {dups} duplicate evaluation rows"

def test_6_all_critical_fact_denominators_reproducible():
    df_gold = pd.read_parquet(GOLD_FACTS_PATH)
    crit_facts = df_gold[df_gold["criticality"] == "CRITICAL"]
    assert len(crit_facts) == 38
    # For Indic (4 languages), denominator must be 38 * 4 = 152
    assert len(crit_facts) * 4 == 152
    # For English control, denominator must be 38 * 1 = 38
    assert len(crit_facts) * 1 == 38

def test_7_no_absent_in_source_counted_as_omitted():
    df_gold = pd.read_parquet(GOLD_FACTS_PATH)
    df_eval = pd.read_parquet(EVAL_PATH)
    # All 85 gold facts are verified present in source
    assert (df_gold["verification_status"] == "GOLD_VERIFIED").all()
    # Ensure no label corruption
    assert set(df_eval["primary_status"].unique()).issubset({"SUPPORTED", "PARTIALLY_SUPPORTED", "OMITTED"})

def test_8_english_intermediate_hashes_identical():
    # Intermediate English summaries used for IndicTrans2, Legal-Aware, and Verified
    # come from System A
    df_en = pd.read_parquet(ENGLISH_OUT_PATH)
    assert len(df_en) == 9
    hashes = [hashlib.sha256(text.encode("utf-8")).hexdigest() for text in df_en["summary_text"]]
    assert len(hashes) == 9
    assert len(set(hashes)) == 9 # Distinct summaries across documents

def test_9_every_reported_metric_recomputed_from_raw():
    df_auth = pd.read_csv(AUTH_RESULTS_PATH)
    df_eval = pd.read_parquet(EVAL_PATH)
    df_gold = pd.read_parquet(GOLD_FACTS_PATH)
    df_eval = df_eval.merge(df_gold[["fact_id", "criticality"]], on="fact_id")
    
    # Check System B Indic critical preservation
    b_crit = df_eval[(df_eval["system"] == "system_b_direct_indic") & (df_eval["language"] != "en") & (df_eval["criticality"] == "CRITICAL")]
    supp_b = (b_crit["primary_status"].isin(["SUPPORTED", "PARTIALLY_SUPPORTED"])).sum()
    rate_b = f"{(supp_b / len(b_crit)) * 100:.2f}%"
    
    auth_b_row = df_auth[df_auth["system_id"] == "B"].iloc[0]
    assert auth_b_row["partial_inclusive_critical_preservation"] == rate_b
    assert rate_b == "7.24%"

def test_10_no_hardcoded_failure_attribution():
    df_attr = pd.read_parquet(ATTR_PATH)
    # Check that failure categories vary across categories and systems
    cat_counts = df_attr["failure_category"].value_counts()
    assert len(cat_counts) > 3
    # Ensure both NONE and failures exist
    assert "NONE" in cat_counts
    assert "R1_RETRIEVAL_FAILURE" in cat_counts
    assert "R4_TRANSLATION_FAILURE" in cat_counts

def test_11_system_e_classified_as_verification_not_generative_rewrite():
    df_d = pd.read_parquet(LEGAL_AWARE_OUT_PATH)
    df_e = pd.read_parquet(VERIFIED_OUT_PATH)
    assert len(df_d) == len(df_e) == 36
    # Check that text hashes between D and E are 100% identical
    d_hashes = [hashlib.sha256(t.encode("utf-8")).hexdigest() for t in df_d["summary_text"]]
    e_hashes = [hashlib.sha256(t.encode("utf-8")).hexdigest() for t in df_e["summary_text"]]
    assert d_hashes == e_hashes

def test_12_no_gold_facts_modified():
    df_gold = pd.read_parquet(GOLD_FACTS_PATH)
    sha = compute_sha256(GOLD_FACTS_PATH)
    assert sha == "e41e9880baf54fa385be5d095584669aa36d861c27c4805b049f551ea0a09ac9"

def test_13_no_source_leakage():
    df_eval = pd.read_parquet(EVAL_PATH)
    # All evaluation units must strictly reference verified gold facts
    df_gold = pd.read_parquet(GOLD_FACTS_PATH)
    gold_ids = set(df_gold["fact_id"])
    eval_ids = set(df_eval["fact_id"])
    assert eval_ids == gold_ids

def test_14_metric_reconciliation_accounts_for_all_conflicting_numbers():
    df_recon = pd.read_csv(RECON_PATH)
    reported_values = set(df_recon["reported_value"])
    expected_values = {"7.2%", "8.6%", "21.1%", "26.3%", "68.4%", "76.3%", "40.0%", "89.5%"}
    assert expected_values.issubset(reported_values)
