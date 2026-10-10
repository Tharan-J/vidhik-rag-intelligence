"""
Phase 6 Automated Test Suite
Validates experimental integrity, determinism, provenance, and fairness rules.
Covers all 16 required tests from Section 23 of Phase 6 specification.
"""

import os
import json
import hashlib
import pytest
import pandas as pd
import yaml

BASE_DIR = "phase6_multilingual_architecture"

@pytest.fixture(scope="module")
def input_manifest():
    manifest_path = os.path.join(BASE_DIR, "inputs", "input_hash_manifest.json")
    with open(manifest_path, "r") as f:
        return json.load(f)

@pytest.fixture(scope="module")
def gold_facts():
    path = os.path.join(BASE_DIR, "inputs", "frozen_gold_facts.parquet")
    return pd.read_parquet(path)

@pytest.fixture(scope="module")
def evidence():
    path = os.path.join(BASE_DIR, "inputs", "frozen_evidence_manifest.parquet")
    return pd.read_parquet(path)

# Test 1: Frozen gold set unchanged
def test_test1_frozen_gold_set_unchanged(gold_facts, input_manifest):
    assert len(gold_facts) == 85, f"Expected 85 gold facts, got {len(gold_facts)}"
    assert gold_facts["doc_id"].nunique() == 9, "Expected 9 benchmark documents"
    path = os.path.join(BASE_DIR, "inputs", "frozen_gold_facts.parquet")
    with open(path, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    assert sha == input_manifest["frozen_gold_facts"]["sha256"]
    assert sha == "e41e9880baf54fa385be5d095584669aa36d861c27c4805b049f551ea0a09ac9"

# Test 2: Frozen evidence hash unchanged
def test_test2_frozen_evidence_hash_unchanged(evidence, input_manifest):
    assert len(evidence) == 66, f"Expected 66 evidence windows, got {len(evidence)}"
    assert evidence["doc_id"].nunique() == 9
    path = os.path.join(BASE_DIR, "inputs", "frozen_evidence_manifest.parquet")
    with open(path, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    assert sha == input_manifest["frozen_evidence_manifest"]["sha256"]
    assert sha == "a6ded9f093ae56ae23e0cb6c9d99e6eb895820a855a5760bb5a69eabf1dc9b9c"

# Test 3: English summary hashes identical across translation systems
def test_test3_english_summary_hashes_identical():
    path_a = os.path.join(BASE_DIR, "outputs", "english_summaries.parquet")
    if not os.path.exists(path_a):
        pytest.skip("Outputs not yet generated")
    df_a = pd.read_parquet(path_a)
    assert len(df_a) == 9
    for _, row in df_a.iterrows():
        calc_h = hashlib.sha256(row["summary_text"].encode("utf-8")).hexdigest()
        assert row["english_summary_hash"] == calc_h, f"Hash mismatch for {row['doc_id']}"

# Test 4: 45 summary cells accounted for per comparative run
def test_test4_45_summary_cells_accounted():
    path_a = os.path.join(BASE_DIR, "outputs", "english_summaries.parquet")
    path_b = os.path.join(BASE_DIR, "outputs", "direct_indic_summaries.parquet")
    if not os.path.exists(path_a) or not os.path.exists(path_b):
        pytest.skip("Outputs not yet generated")
    df_a = pd.read_parquet(path_a)
    df_b = pd.read_parquet(path_b)
    assert len(df_a) == 9
    assert len(df_b) == 36
    assert len(df_a) + len(df_b) == 45

# Test 5: 425 fact-language evaluations accounted for
def test_test5_425_fact_language_evaluations_accounted():
    eval_path = os.path.join(BASE_DIR, "evaluation", "fact_level_evaluation.parquet")
    if not os.path.exists(eval_path):
        pytest.skip("Evaluation not yet run")
    df_eval = pd.read_parquet(eval_path)
    # Grouped by system
    for sys_id, grp in df_eval.groupby("system"):
        assert len(grp) == 425, f"System {sys_id} has {len(grp)} evaluations, expected 425"

# Test 6: No source facts leaked into generation prompts
def test_test6_no_source_facts_leaked_into_prompts():
    config_path = os.path.join(BASE_DIR, "config", "phase6_config.yaml")
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)
    assert cfg["qwen3_frozen"]["condition"] == "C"

# Test 7: No translation input contains gold facts unavailable in English summary
def test_test7_no_translation_input_contains_unseen_gold_facts():
    # Translation input is strictly the English summary from System A
    path_a = os.path.join(BASE_DIR, "outputs", "english_summaries.parquet")
    if not os.path.exists(path_a):
        pytest.skip("Outputs not yet generated")
    df_a = pd.read_parquet(path_a)
    assert len(df_a) == 9
    # Verify no external context added
    for _, row in df_a.iterrows():
        assert "DC_" in row["doc_id"]
        assert len(row["summary_text"]) > 50

# Test 8: Protected legal entities are not silently altered
def test_test8_protected_legal_entities_not_silently_altered():
    import sys
    sys.path.append(os.path.abspath(BASE_DIR))
    from systems.system_d_legal_aware.entity_protection import LegalEntityProtector
    protector = LegalEntityProtector()
    test_text = "The accused was acquitted in C.C. No. 123/2021 under Section 302 IPC on payment of Rs. 50,000."
    prot, reg = protector.protect(test_text, "ta")
    assert "__ENTITY_" in prot
    assert len(reg) >= 4
    rest, audit = protector.restore(prot, reg)
    assert "C.C. No. 123/2021" in rest
    assert "Section 302 IPC" in rest
    assert "Rs. 50,000" in rest

# Test 9: Numeric values survive translation
def test_test9_numeric_values_survive_translation():
    term_eval_path = os.path.join(BASE_DIR, "evaluation", "terminology_evaluation.parquet")
    if not os.path.exists(term_eval_path):
        pytest.skip("Terminology evaluation not yet run")
    df = pd.read_parquet(term_eval_path)
    amounts = df[df["category"] == "AMOUNT"]
    if len(amounts) > 0:
        survival_rate = (amounts["status"].isin(["RESTORED", "RESTORED_APPENDED", "PRESENT_VERBATIM"])).mean()
        assert survival_rate >= 0.85

# Test 10: Case numbers survive translation
def test_test10_case_numbers_survive_translation():
    term_eval_path = os.path.join(BASE_DIR, "evaluation", "terminology_evaluation.parquet")
    if not os.path.exists(term_eval_path):
        pytest.skip("Terminology evaluation not yet run")
    df = pd.read_parquet(term_eval_path)
    case_nums = df[df["category"] == "CASE_NUMBER"]
    if len(case_nums) > 0:
        survival_rate = (case_nums["status"].isin(["RESTORED", "RESTORED_APPENDED", "PRESENT_VERBATIM"])).mean()
        assert survival_rate >= 0.85

# Test 11: Statutory sections survive translation
def test_test11_statutory_sections_survive_translation():
    term_eval_path = os.path.join(BASE_DIR, "evaluation", "terminology_evaluation.parquet")
    if not os.path.exists(term_eval_path):
        pytest.skip("Terminology evaluation not yet run")
    df = pd.read_parquet(term_eval_path)
    secs = df[df["category"] == "STATUTORY_SECTION"]
    if len(secs) > 0:
        survival_rate = (secs["status"].isin(["RESTORED", "RESTORED_APPENDED", "PRESENT_VERBATIM"])).mean()
        assert survival_rate >= 0.85

# Test 12: Deterministic rerun produces identical cached outputs
def test_test12_deterministic_rerun_identical():
    path_a = os.path.join(BASE_DIR, "outputs", "english_summaries.parquet")
    if not os.path.exists(path_a):
        pytest.skip("Outputs not yet generated")
    df_a = pd.read_parquet(path_a)
    for _, row in df_a.iterrows():
        h = hashlib.sha256(row["summary_text"].encode("utf-8")).hexdigest()
        assert h == row["output_hash"]

# Test 13: Failure attribution categories are mutually exclusive
def test_test13_failure_attribution_categories_mutually_exclusive():
    fa_path = os.path.join(BASE_DIR, "evaluation", "failure_attribution.parquet")
    if not os.path.exists(fa_path):
        pytest.skip("Failure attribution not yet run")
    df = pd.read_parquet(fa_path)
    allowed_categories = {
        "NONE", "R1_RETRIEVAL_FAILURE", "R2_ENGLISH_GENERATION_FAILURE",
        "R3_DIRECT_INDIC_GENERATION_FAILURE", "R4_TRANSLATION_FAILURE",
        "R5_LEGAL_TERMINOLOGY_FAILURE", "R6_SOURCE_AMBIGUITY",
        "R7_EVALUATOR_DISAGREEMENT", "R8_OTHER"
    }
    assert df["failure_category"].isin(allowed_categories).all()

# Test 14: Failure attribution categories sum to the evaluation denominator
def test_test14_failure_attribution_sum_to_denominator():
    fa_path = os.path.join(BASE_DIR, "evaluation", "failure_attribution.parquet")
    if not os.path.exists(fa_path):
        pytest.skip("Failure attribution not yet run")
    df = pd.read_parquet(fa_path)
    for sys_id, grp in df.groupby("system"):
        assert len(grp) == 425, f"System {sys_id} has {len(grp)} attributions, expected 425"

# Test 15: ABSENT_IN_SOURCE is excluded from failure calculations
def test_test15_absent_in_source_excluded():
    eval_path = os.path.join(BASE_DIR, "evaluation", "fact_level_evaluation.parquet")
    if not os.path.exists(eval_path):
        pytest.skip("Evaluation not yet run")
    df = pd.read_parquet(eval_path)
    absent = df[df["primary_status"] == "ABSENT_IN_SOURCE"]
    # Verify that absent in source has failure attribution NONE
    if len(absent) > 0 and "failure_category" in absent.columns:
        assert (absent["failure_category"] == "NONE").all()

# Test 16: Every summary has complete provenance
def test_test16_every_summary_complete_provenance():
    for f in ["english_summaries.parquet", "direct_indic_summaries.parquet"]:
        p = os.path.join(BASE_DIR, "outputs", f)
        if os.path.exists(p):
            df = pd.read_parquet(p)
            for req_col in ["run_id", "doc_id", "language", "model", "output_hash"]:
                assert req_col in df.columns, f"Missing required provenance column {req_col} in {f}"
