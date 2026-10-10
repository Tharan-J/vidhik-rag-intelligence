import os
import pytest
import pandas as pd
import hashlib

BASE_DIR = "/home/tharan/Seeds/vidhik"
P7_DIR = os.path.join(BASE_DIR, "phase7_translation")
AUDIT_DIR = os.path.join(BASE_DIR, "phase7_forensic_audit")

def test_1_frozen_gold_facts_sha():
    p = os.path.join(P7_DIR, "inputs", "frozen_gold_facts.parquet")
    with open(p, "rb") as f: h = hashlib.sha256(f.read()).hexdigest()
    assert h == "e41e9880baf54fa385be5d095584669aa36d861c27c4805b049f551ea0a09ac9"

def test_2_frozen_english_summaries_sha():
    df_en = pd.read_parquet(os.path.join(P7_DIR, "inputs", "frozen_english_summaries.parquet"))
    assert len(df_en) == 9
    for _, r in df_en.iterrows():
        act_h = hashlib.sha256(r["summary_text"].encode("utf-8")).hexdigest()
        assert act_h == r["output_hash"]

def test_3_evaluation_universe_counts():
    df_eval = pd.read_parquet(os.path.join(P7_DIR, "outputs", "fact_level_evaluation.parquet"))
    assert len(df_eval) == 2040 # 6 systems * 340 units
    for s in df_eval["system_id"].unique():
        sub = df_eval[df_eval["system_id"] == s]
        assert len(sub) == 340
        assert len(sub[sub["criticality"] == "CRITICAL"]) == 152

def test_4_cross_language_distinctness():
    df_trans = pd.read_parquet(os.path.join(P7_DIR, "outputs", "translations.parquet"))
    for (s, doc), g in df_trans.groupby(["system_id", "doc_id"]):
        assert g["output_hash"].nunique() == 4, f"Hash collision across languages in {s} {doc}"
        assert g["translated_text"].nunique() == 4

def test_5_t3_t4_t5_hash_identity():
    # Audits the finding that T3, T4, and T5 produced identical outputs
    df_trans = pd.read_parquet(os.path.join(P7_DIR, "outputs", "translations.parquet"))
    d3 = df_trans[df_trans["system_id"] == "T3_CLAIM_ALIGNED"].set_index(["doc_id", "target_language"])["output_hash"]
    d4 = df_trans[df_trans["system_id"] == "T4_CANDIDATE_RERANKING"].set_index(["doc_id", "target_language"])["output_hash"]
    d5 = df_trans[df_trans["system_id"] == "T5_COMBINED_OPTIMAL"].set_index(["doc_id", "target_language"])["output_hash"]
    assert (d3 == d4).all()
    assert (d4 == d5).all()

def test_6_t2_vs_t5_hash_distinction():
    # Audits that T2 and T5 are distinct generated texts
    df_trans = pd.read_parquet(os.path.join(P7_DIR, "outputs", "translations.parquet"))
    d2 = df_trans[df_trans["system_id"] == "T2_STRONGER_TERMINOLOGY"].set_index(["doc_id", "target_language"])["output_hash"]
    d5 = df_trans[df_trans["system_id"] == "T5_COMBINED_OPTIMAL"].set_index(["doc_id", "target_language"])["output_hash"]
    assert (d2 != d5).all()

def test_7_recomputed_t0_baseline_metrics():
    df_comp = pd.read_csv(os.path.join(AUDIT_DIR, "recomputed_system_results.csv"))
    t0 = df_comp[df_comp["system_id"] == "T0_BASELINE_LEGAL_AWARE"].iloc[0]
    assert t0["critical_supported"] == 36
    assert t0["critical_partial"] == 4
    assert t0["critical_omitted"] == 112
    assert t0["partial_inclusive_critical_preservation"] == "26.32%"

def test_8_recomputed_t2_metrics():
    df_comp = pd.read_csv(os.path.join(AUDIT_DIR, "recomputed_system_results.csv"))
    t2 = df_comp[df_comp["system_id"] == "T2_STRONGER_TERMINOLOGY"].iloc[0]
    assert t2["critical_supported"] == 36
    assert t2["critical_partial"] == 32
    assert t2["critical_omitted"] == 84
    assert t2["partial_inclusive_critical_preservation"] == "44.74%"

def test_9_traceable_28_unit_delta():
    df_changes = pd.read_csv(os.path.join(AUDIT_DIR, "t0_t2_fact_changes.csv"))
    assert len(df_changes) == 28 # Exactly 28 units shifted from OMITTED to PARTIALLY_SUPPORTED
    # All 28 units correspond to the 7 State of Telangana party facts across 4 languages
    assert (df_changes["category"] == "PARTIES").all()
    assert (df_changes["criticality"] == "CRITICAL").all()

def test_10_zero_contradictions_and_unsupported_additions():
    df_comp = pd.read_csv(os.path.join(AUDIT_DIR, "recomputed_system_results.csv"))
    for _, r in df_comp.iterrows():
        assert r["contradictions"] == 0
        assert r["unsupported_additions"] == 0
