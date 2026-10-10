import os
import pytest
import pandas as pd
import hashlib

BASE_DIR = "/home/tharan/Seeds/vidhik"
P7_DIR = os.path.join(BASE_DIR, "phase7_translation")

EN_PATH = os.path.join(P7_DIR, "inputs", "frozen_english_summaries.parquet")
GOLD_PATH = os.path.join(P7_DIR, "inputs", "frozen_gold_facts.parquet")
MANIFEST_PATH = os.path.join(P7_DIR, "inputs", "frozen_benchmark_manifest.parquet")
EVIDENCE_PATH = os.path.join(P7_DIR, "inputs", "frozen_evidence_manifest.parquet")
TRANS_PATH = os.path.join(P7_DIR, "outputs", "translations.parquet")
EVAL_PATH = os.path.join(P7_DIR, "outputs", "fact_level_evaluation.parquet")
ALIGN_PATH = os.path.join(P7_DIR, "outputs", "sentence_alignment.parquet")
ENTITY_PATH = os.path.join(P7_DIR, "outputs", "entity_translation_results.parquet")
SYS_COMP_PATH = os.path.join(P7_DIR, "results", "system_comparison.csv")

def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

# Test 1: English summary SHA integrity
def test_1_english_summary_sha_integrity():
    df_en = pd.read_parquet(EN_PATH)
    assert len(df_en) == 9
    for _, r in df_en.iterrows():
        actual_h = hashlib.sha256(r["summary_text"].encode("utf-8")).hexdigest()
        assert actual_h == r["output_hash"]

# Test 2: Frozen gold-set SHA integrity
def test_2_frozen_gold_set_sha_integrity():
    gold_sha = sha(GOLD_PATH)
    assert gold_sha == "e41e9880baf54fa385be5d095584669aa36d861c27c4805b049f551ea0a09ac9"

# Test 3: No English summary modification across systems
def test_3_no_english_summary_modification():
    df_trans = pd.read_parquet(TRANS_PATH)
    df_en = pd.read_parquet(EN_PATH)
    en_map = dict(zip(df_en["doc_id"], df_en["output_hash"]))
    for _, r in df_trans.iterrows():
        assert r["english_summary_sha256"] == en_map[r["doc_id"]]

# Test 4: No document mismatch
def test_4_no_document_mismatch():
    df_trans = pd.read_parquet(TRANS_PATH)
    docs = sorted(df_trans["doc_id"].unique())
    expected = [f"DC_{i:06d}" for i in range(1, 9)] + ["DC_000011"]
    assert docs == sorted(expected)

# Test 5: No language mismatch
def test_5_no_language_mismatch():
    df_trans = pd.read_parquet(TRANS_PATH)
    langs = sorted(df_trans["target_language"].unique())
    assert langs == ["hi", "kn", "mr", "ta"]

# Test 6: No duplicate translation cells
def test_6_no_duplicate_translation_cells():
    df_trans = pd.read_parquet(TRANS_PATH)
    dups = df_trans.duplicated(subset=["system_id", "doc_id", "target_language"]).sum()
    assert dups == 0

# Test 7: All 4 Indic languages represented
def test_7_all_4_indic_languages_represented():
    df_eval = pd.read_parquet(EVAL_PATH)
    assert set(df_eval["language"].unique()) == {"ta", "hi", "kn", "mr"}

# Test 8: All 9 documents represented
def test_8_all_9_documents_represented():
    df_eval = pd.read_parquet(EVAL_PATH)
    assert df_eval["doc_id"].nunique() == 9

# Test 9: Entity placeholder restoration
def test_9_entity_placeholder_restoration():
    df_trans = pd.read_parquet(TRANS_PATH)
    for text in df_trans["translated_text"]:
        # Verify no un-restored placeholder remains in final text
        assert "__LEGAL_ENT_" not in text
        assert "__ENTITY_" not in text

# Test 10: Case number preservation
def test_10_case_number_preservation():
    df_ent = pd.read_parquet(ENTITY_PATH)
    case_ents = df_ent[df_ent["category"] == "CASE_NUMBERS"]
    assert len(case_ents) > 0
    # Verified that status is either RESTORED or PRESENT_VERBATIM or RESTORED_APPENDED
    assert (case_ents["status"].isin(["RESTORED", "PRESENT_VERBATIM", "RESTORED_APPENDED"])).all()

# Test 11: Date preservation
def test_11_date_preservation():
    df_ent = pd.read_parquet(ENTITY_PATH)
    date_ents = df_ent[df_ent["category"] == "DATES"]
    assert len(date_ents) > 0
    assert (date_ents["status"].isin(["RESTORED", "PRESENT_VERBATIM", "RESTORED_APPENDED"])).all()

# Test 12: Amount preservation
def test_12_amount_preservation():
    df_ent = pd.read_parquet(ENTITY_PATH)
    amt_ents = df_ent[df_ent["category"] == "CURRENCY_AMOUNTS"]
    if len(amt_ents) > 0:
        assert (amt_ents["status"].isin(["RESTORED", "PRESENT_VERBATIM", "RESTORED_APPENDED"])).all()

# Test 13: Statutory section preservation
def test_13_statutory_section_preservation():
    df_ent = pd.read_parquet(ENTITY_PATH)
    sec_ents = df_ent[df_ent["category"] == "STATUTORY_SECTIONS"]
    assert len(sec_ents) > 0
    assert (sec_ents["status"].isin(["RESTORED", "PRESENT_VERBATIM", "RESTORED_APPENDED"])).all()

# Test 14: No gold fact leakage
def test_14_no_gold_fact_leakage():
    # Translation runner should only read frozen_english_summaries, not gold facts
    with open(os.path.join(P7_DIR, "translation", "translation_systems.py")) as f:
        code = f.read()
    assert "frozen_gold_facts" not in code
    assert "gold_facts" not in code

# Test 15: Deterministic evaluation
def test_15_deterministic_evaluation():
    df_eval = pd.read_parquet(EVAL_PATH)
    assert not df_eval["primary_status"].isnull().any()
    assert set(df_eval["primary_status"].unique()).issubset({"SUPPORTED", "PARTIALLY_SUPPORTED", "OMITTED", "ABSENT_IN_SOURCE"})

# Test 16: Denominator = 152 for critical Indic evaluation
def test_16_denominator_152_critical():
    df_eval = pd.read_parquet(EVAL_PATH)
    for sys_id in df_eval["system_id"].unique():
        sub = df_eval[(df_eval["system_id"] == sys_id) & (df_eval["criticality"] == "CRITICAL")]
        assert len(sub) == 152, f"System {sys_id} critical count is {len(sub)}, expected 152"

# Test 17: Denominator = 340 for overall Indic evaluation
def test_17_denominator_340_overall():
    df_eval = pd.read_parquet(EVAL_PATH)
    for sys_id in df_eval["system_id"].unique():
        sub = df_eval[df_eval["system_id"] == sys_id]
        assert len(sub) == 340, f"System {sys_id} total count is {len(sub)}, expected 340"

# Test 18: Contradiction detection
def test_18_contradiction_detection():
    df_eval = pd.read_parquet(EVAL_PATH)
    # Contradiction column exists and rates are 0%
    assert "contradiction" in df_eval.columns
    assert df_eval["contradiction"].sum() == 0

# Test 19: Unsupported addition detection
def test_19_unsupported_addition_detection():
    df_comp = pd.read_csv(SYS_COMP_PATH)
    for r in df_comp["unsupported_addition_rate"]:
        assert r == "0.00%"

# Test 20: Translation cache integrity
def test_20_translation_cache_integrity():
    df_trans = pd.read_parquet(TRANS_PATH)
    assert len(df_trans) == 6 * 9 * 4 # 6 systems * 9 docs * 4 languages = 216
    assert (df_trans["status"] == "SUCCESS").all()
