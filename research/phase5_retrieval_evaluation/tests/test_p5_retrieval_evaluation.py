"""
Test Suite: Phase 5.2 Source-Grounded Retrieval Evaluation Validation
====================================================================
Enforces the 14 Quality Control rules defined in Section "QUALITY CONTROL"
of the Phase 5.2 Retrieval Evaluation Specification.
"""

from pathlib import Path
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
BASE_DIR = ROOT / "phase5_retrieval_evaluation"
GOLD_PATH = ROOT / "phase5_source_grounded_gold" / "gold_facts.parquet"
EVAL_PATH = BASE_DIR / "retrieval_fact_evaluation.parquet"
MANIFEST_PATH = BASE_DIR / "retrieval_evidence_manifest.parquet"
SRC_MAN_PATH = ROOT / "district_extraction" / "source_manifest" / "district_source_manifest_v1.parquet"
BENCH_INV_PATH = ROOT / "phase5_source_grounded_gold" / "benchmark_inventory.csv"

ALLOWED_STATUSES = {
    'RETRIEVED_SUPPORTED',
    'RETRIEVED_PARTIAL',
    'RETRIEVED_BUT_INSUFFICIENT',
    'NOT_RETRIEVED',
    'ABSENT_IN_SOURCE',
}


@pytest.fixture(scope="module")
def gold_df():
    assert GOLD_PATH.exists(), f"Missing {GOLD_PATH}"
    return pd.read_parquet(GOLD_PATH)


@pytest.fixture(scope="module")
def eval_df():
    assert EVAL_PATH.exists(), f"Missing {EVAL_PATH}"
    return pd.read_parquet(EVAL_PATH)


@pytest.fixture(scope="module")
def manifest_df():
    assert MANIFEST_PATH.exists(), f"Missing {MANIFEST_PATH}"
    return pd.read_parquet(MANIFEST_PATH)


@pytest.fixture(scope="module")
def src_man_df():
    assert SRC_MAN_PATH.exists(), f"Missing {SRC_MAN_PATH}"
    return pd.read_parquet(SRC_MAN_PATH)


@pytest.fixture(scope="module")
def bench_inv_df():
    assert BENCH_INV_PATH.exists(), f"Missing {BENCH_INV_PATH}"
    return pd.read_csv(BENCH_INV_PATH)


# ---------------------------------------------------------------------------
# QC 1: Exactly 85 gold facts are represented
# ---------------------------------------------------------------------------
def test_qc1_exactly_85_gold_facts_represented(eval_df):
    assert len(eval_df) == 85, f"Expected exactly 85 facts in evaluation, found {len(eval_df)}"


# ---------------------------------------------------------------------------
# QC 2: No duplicate fact_id
# ---------------------------------------------------------------------------
def test_qc2_no_duplicate_fact_id(eval_df):
    dups = eval_df[eval_df.duplicated('fact_id', keep=False)]
    assert len(dups) == 0, f"Found duplicate fact_ids:\n{dups[['fact_id', 'doc_id', 'normalized_value']]}"


# ---------------------------------------------------------------------------
# QC 3: Every retrieval_status is from the allowed enum
# ---------------------------------------------------------------------------
def test_qc3_allowed_retrieval_status_enum(eval_df):
    invalid = eval_df[~eval_df['retrieval_status'].isin(ALLOWED_STATUSES)]
    assert len(invalid) == 0, f"Found invalid retrieval_status values:\n{invalid[['fact_id', 'retrieval_status']]}"


# ---------------------------------------------------------------------------
# QC 4: Every non-ABSENT fact has a valid source provenance reference
# ---------------------------------------------------------------------------
def test_qc4_valid_source_provenance_for_non_absent(eval_df):
    non_absent = eval_df[eval_df['retrieval_status'] != 'ABSENT_IN_SOURCE']
    for col in ['source_sentence_id', 'source_paragraph_id', 'source_page']:
        assert col in non_absent.columns
        nulls = non_absent[col].isna().sum()
        assert nulls == 0, f"Column {col} has {nulls} null values in non-absent facts"
        empty_str = (non_absent[col].astype(str).str.strip() == '').sum()
        assert empty_str == 0, f"Column {col} has {empty_str} empty string values in non-absent facts"


# ---------------------------------------------------------------------------
# QC 5: RETRIEVED_SUPPORTED facts contain evidence references
# ---------------------------------------------------------------------------
def test_qc5_retrieved_supported_contain_evidence_references(eval_df):
    supported = eval_df[eval_df['retrieval_status'] == 'RETRIEVED_SUPPORTED']
    assert len(supported) > 0, "No RETRIEVED_SUPPORTED facts found"
    for _, row in supported.iterrows():
        assert str(row['evidence_sentence_ids']).strip() != '', f"Fact {row['fact_id']} missing evidence_sentence_ids"
        assert str(row['evidence_paragraph_ids']).strip() != '', f"Fact {row['fact_id']} missing evidence_paragraph_ids"
        assert str(row['evidence_pages']).strip() != '', f"Fact {row['fact_id']} missing evidence_pages"
        assert str(row['evidence_text']).strip() != '', f"Fact {row['fact_id']} missing evidence_text"


# ---------------------------------------------------------------------------
# QC 6: RETRIEVED_PARTIAL facts contain evidence references
# ---------------------------------------------------------------------------
def test_qc6_retrieved_partial_contain_evidence_references(eval_df):
    partial = eval_df[eval_df['retrieval_status'] == 'RETRIEVED_PARTIAL']
    for _, row in partial.iterrows():
        assert str(row['evidence_sentence_ids']).strip() != '', f"Fact {row['fact_id']} missing evidence_sentence_ids"
        assert str(row['evidence_paragraph_ids']).strip() != '', f"Fact {row['fact_id']} missing evidence_paragraph_ids"
        assert str(row['evidence_pages']).strip() != '', f"Fact {row['fact_id']} missing evidence_pages"
        assert str(row['evidence_text']).strip() != '', f"Fact {row['fact_id']} missing evidence_text"


# ---------------------------------------------------------------------------
# QC 7: RETRIEVED_BUT_INSUFFICIENT facts contain evidence references
# ---------------------------------------------------------------------------
def test_qc7_retrieved_insufficient_contain_evidence_references(eval_df):
    insufficient = eval_df[eval_df['retrieval_status'] == 'RETRIEVED_BUT_INSUFFICIENT']
    for _, row in insufficient.iterrows():
        assert str(row['evidence_sentence_ids']).strip() != '', f"Fact {row['fact_id']} missing evidence_sentence_ids"
        assert str(row['evidence_paragraph_ids']).strip() != '', f"Fact {row['fact_id']} missing evidence_paragraph_ids"
        assert str(row['evidence_pages']).strip() != '', f"Fact {row['fact_id']} missing evidence_pages"
        assert str(row['evidence_text']).strip() != '', f"Fact {row['fact_id']} missing evidence_text"


# ---------------------------------------------------------------------------
# QC 8: NOT_RETRIEVED facts do not falsely contain evidence references
# ---------------------------------------------------------------------------
def test_qc8_not_retrieved_facts_have_no_evidence_references(eval_df):
    not_ret = eval_df[eval_df['retrieval_status'] == 'NOT_RETRIEVED']
    assert len(not_ret) > 0, "No NOT_RETRIEVED facts found"
    for _, row in not_ret.iterrows():
        sids = str(row['evidence_sentence_ids']).strip()
        pids = str(row['evidence_paragraph_ids']).strip()
        pages = str(row['evidence_pages']).strip()
        txt = str(row['evidence_text']).strip()
        assert sids in ['', 'None', 'nan'], f"NOT_RETRIEVED fact {row['fact_id']} falsely has sentence IDs: {sids}"
        assert pids in ['', 'None', 'nan'], f"NOT_RETRIEVED fact {row['fact_id']} falsely has paragraph IDs: {pids}"
        assert pages in ['', 'None', 'nan'], f"NOT_RETRIEVED fact {row['fact_id']} falsely has pages: {pages}"
        assert txt in ['', 'None', 'nan'], f"NOT_RETRIEVED fact {row['fact_id']} falsely has evidence text: {txt[:30]}"


# ---------------------------------------------------------------------------
# QC 9: Every document in the benchmark inventory is represented
# ---------------------------------------------------------------------------
def test_qc9_every_benchmark_document_represented(eval_df, bench_inv_df):
    eval_docs = set(eval_df['doc_id'].unique())
    bench_docs = set(bench_inv_df['doc_id'].unique())
    assert eval_docs == bench_docs, f"Mismatch in documents. Difference: {eval_docs ^ bench_docs}"
    assert len(eval_docs) == 9


# ---------------------------------------------------------------------------
# QC 10: Every critical gold fact is represented
# ---------------------------------------------------------------------------
def test_qc10_every_critical_gold_fact_represented(eval_df, gold_df):
    gold_crit_ids = set(gold_df[gold_df['criticality'] == 'CRITICAL']['gold_fact_id'])
    eval_crit_ids = set(eval_df[eval_df['criticality'] == 'CRITICAL']['fact_id'])
    assert eval_crit_ids == gold_crit_ids, f"Critical facts mismatch: {eval_crit_ids ^ gold_crit_ids}"
    assert len(eval_crit_ids) == 38


# ---------------------------------------------------------------------------
# QC 11: No new facts are introduced
# ---------------------------------------------------------------------------
def test_qc11_no_new_facts_introduced(eval_df, gold_df):
    gold_ids = set(gold_df['gold_fact_id'])
    eval_ids = set(eval_df['fact_id'])
    assert eval_ids == gold_ids, f"Fact ID mismatch: extra={eval_ids - gold_ids}, missing={gold_ids - eval_ids}"


# ---------------------------------------------------------------------------
# QC 12: Source SHA-256 references remain unchanged
# ---------------------------------------------------------------------------
def test_qc12_source_sha256_unchanged(eval_df, src_man_df):
    sha_map = dict(zip(src_man_df['document_id'], src_man_df['sha256']))
    for _, row in eval_df.iterrows():
        expected = sha_map.get(row['doc_id'])
        actual = row['source_sha256']
        assert actual == expected, f"Fact {row['fact_id']} SHA mismatch: got {actual}, expected {expected}"


# ---------------------------------------------------------------------------
# QC 13: Retrieval evaluation does not depend on model summary text
# ---------------------------------------------------------------------------
def test_qc13_no_summary_text_dependency(eval_df):
    forbidden_cols = {'summary_text', 'model_id', 'language', 'generation_run_id'}
    assert not any(col in eval_df.columns for col in forbidden_cols), "Evaluation contains model summary dependencies"


# ---------------------------------------------------------------------------
# QC 14: Counts reconcile exactly
# ---------------------------------------------------------------------------
def test_qc14_counts_reconcile_exactly(eval_df):
    status_counts = eval_df['retrieval_status'].value_counts().to_dict()
    total = sum(status_counts.values())
    assert total == 85, f"Sum of status counts ({total}) does not equal 85"
    assert status_counts.get('RETRIEVED_SUPPORTED', 0) + \
           status_counts.get('RETRIEVED_PARTIAL', 0) + \
           status_counts.get('RETRIEVED_BUT_INSUFFICIENT', 0) + \
           status_counts.get('NOT_RETRIEVED', 0) + \
           status_counts.get('ABSENT_IN_SOURCE', 0) == 85
