"""
Test Suite: Phase 5 Source-Grounded Legal Fact Gold Set Validation
==================================================================
Enforces the 14 Quality Gates defined in Section 21 of the Phase 5 Specification.
All tests must pass before certification.
"""

import json
import re
from pathlib import Path
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
BASE_DIR = ROOT / "phase5_source_grounded_gold"
GOLD_PARQUET = BASE_DIR / "gold_facts.parquet"
SRC_MAN = ROOT / "district_extraction" / "source_manifest" / "district_source_manifest_v1.parquet"
SENT_PARQUET = ROOT / "district_extraction" / "structure" / "v1" / "sentences_provenance_v1.parquet"
STRUCT_DIR = ROOT / "district_extraction" / "structure" / "v1"
BENCH_INV = BASE_DIR / "benchmark_inventory.csv"
SRC_INV = BASE_DIR / "source_inventory.csv"
COV_CSV = BASE_DIR / "source_fact_coverage.csv"
SUMM_PARQUET = ROOT / "phase4_summarization" / "generation" / "summaries_v1.parquet"

EXPECTED_BENCH_DOCS = [
    'DC_000001', 'DC_000002', 'DC_000003', 'DC_000004', 'DC_000005',
    'DC_000006', 'DC_000007', 'DC_000008', 'DC_000011',
]
EXPECTED_LANGUAGES = {'en', 'ta', 'hi', 'kn', 'mr'}


@pytest.fixture(scope="module")
def gold_df():
    assert GOLD_PARQUET.exists(), f"Missing {GOLD_PARQUET}"
    return pd.read_parquet(GOLD_PARQUET)


@pytest.fixture(scope="module")
def sent_df():
    assert SENT_PARQUET.exists(), f"Missing {SENT_PARQUET}"
    return pd.read_parquet(SENT_PARQUET)


@pytest.fixture(scope="module")
def src_man_df():
    assert SRC_MAN.exists(), f"Missing {SRC_MAN}"
    return pd.read_parquet(SRC_MAN)


@pytest.fixture(scope="module")
def bench_inv_df():
    assert BENCH_INV.exists(), f"Missing {BENCH_INV}"
    return pd.read_csv(BENCH_INV)


# ---------------------------------------------------------------------------
# Test 1: Exactly 9 benchmark documents
# ---------------------------------------------------------------------------
def test_1_exactly_nine_benchmark_documents(gold_df, bench_inv_df):
    docs = sorted(gold_df['doc_id'].unique().tolist())
    assert len(docs) == 9, f"Expected exactly 9 benchmark documents, got {len(docs)}: {docs}"
    assert docs == sorted(EXPECTED_BENCH_DOCS)
    assert len(bench_inv_df) == 9
    assert sorted(bench_inv_df['doc_id'].tolist()) == sorted(EXPECTED_BENCH_DOCS)


# ---------------------------------------------------------------------------
# Test 2: Exactly 45 actual summaries discovered
# ---------------------------------------------------------------------------
def test_2_exactly_45_actual_summaries_discovered(bench_inv_df):
    total_summaries = bench_inv_df['summary_count'].sum()
    assert total_summaries == 45, f"Expected 45 actual summaries, got {total_summaries}"


# ---------------------------------------------------------------------------
# Test 3: Every benchmark document has 5 languages
# ---------------------------------------------------------------------------
def test_3_every_benchmark_document_has_five_languages(bench_inv_df):
    for _, row in bench_inv_df.iterrows():
        langs = set(row['languages_present'].split(','))
        assert langs == EXPECTED_LANGUAGES, f"Doc {row['doc_id']} missing languages: {EXPECTED_LANGUAGES - langs}"
        assert row['all_five_languages_present'] is True or row['all_five_languages_present'] == 1


# ---------------------------------------------------------------------------
# Test 4: Every GOLD_VERIFIED fact has complete provenance
# ---------------------------------------------------------------------------
def test_4_every_gold_verified_fact_has_complete_provenance(gold_df):
    required_cols = [
        'gold_fact_id', 'doc_id', 'category', 'criticality',
        'source_value', 'normalized_value', 'source_text',
        'source_page', 'source_paragraph_id', 'source_sentence_id',
        'pdf_sha256', 'verification_status', 'verification_method',
        'reviewer', 'review_timestamp', 'notes',
    ]
    for col in required_cols:
        assert col in gold_df.columns, f"Missing required column: {col}"
        null_count = gold_df[col].isna().sum()
        assert null_count == 0, f"Column {col} has {null_count} nulls in gold fact set"
        # Check non-empty strings
        if gold_df[col].dtype == object:
            empty_count = (gold_df[col].astype(str).str.strip() == '').sum()
            assert empty_count == 0, f"Column {col} has {empty_count} empty strings"


# ---------------------------------------------------------------------------
# Test 5: Every GOLD_VERIFIED fact traces to a real Phase-2 sentence
# ---------------------------------------------------------------------------
def test_5_every_gold_fact_traces_to_real_phase2_sentence(gold_df, sent_df):
    valid_sentence_ids = set(sent_df['sentence_id'].unique())
    missing_sentences = []
    for _, row in gold_df.iterrows():
        sid = row['source_sentence_id']
        if sid not in valid_sentence_ids:
            missing_sentences.append((row['gold_fact_id'], row['doc_id'], sid))
    assert len(missing_sentences) == 0, f"Found gold facts with invalid sentence IDs: {missing_sentences}"


# ---------------------------------------------------------------------------
# Test 6: Every source sentence belongs to the correct document
# ---------------------------------------------------------------------------
def test_6_every_source_sentence_belongs_to_correct_document(gold_df, sent_df):
    sent_doc_map = dict(zip(sent_df['sentence_id'], sent_df['document_id']))
    mismatched = []
    for _, row in gold_df.iterrows():
        sid = row['source_sentence_id']
        expected_doc = row['doc_id']
        actual_doc = sent_doc_map.get(sid)
        if actual_doc != expected_doc:
            mismatched.append((row['gold_fact_id'], expected_doc, sid, actual_doc))
    assert len(mismatched) == 0, f"Sentence document ID mismatches: {mismatched}"


# ---------------------------------------------------------------------------
# Test 7: PDF SHA matches the frozen source
# ---------------------------------------------------------------------------
def test_7_pdf_sha_matches_frozen_source(gold_df, src_man_df):
    expected_sha_map = dict(zip(src_man_df['document_id'], src_man_df['sha256']))
    for _, row in gold_df.iterrows():
        doc_id = row['doc_id']
        sha = row['pdf_sha256']
        expected = expected_sha_map.get(doc_id)
        assert expected is not None, f"Doc {doc_id} not in source manifest"
        assert sha == expected, f"Doc {doc_id} SHA mismatch: got {sha}, expected {expected}"


# ---------------------------------------------------------------------------
# Test 8: No malformed AMOUNT gold facts
# ---------------------------------------------------------------------------
def test_8_no_malformed_amount_gold_facts(gold_df):
    amount_facts = gold_df[gold_df['category'] == 'AMOUNT']
    for _, row in amount_facts.iterrows():
        val = str(row['source_value']).strip()
        norm = str(row['normalized_value']).strip()
        # Must contain digits
        assert bool(re.search(r'\d', val)), f"AMOUNT fact {row['gold_fact_id']} lacks numbers: {val!r}"
        assert bool(re.search(r'\d', norm)), f"AMOUNT fact {row['gold_fact_id']} normalized lacks numbers: {norm!r}"
        # Must not be a standalone currency symbol
        assert not re.match(r'^(Rs\.?|INR|Rs|,)\s*$', val, re.IGNORECASE)


# ---------------------------------------------------------------------------
# Test 9: No known docket-header PARTIES gold facts
# ---------------------------------------------------------------------------
def test_9_no_docket_header_parties_gold_facts(gold_df):
    party_facts = gold_df[gold_df['category'] == 'PARTIES']
    docket_patterns = [
        r'^IN THE COURT',
        r'^PRESENT:',
        r'^DOCKET ORDER',
        r'^COMMITTAL ORDER',
        r'^JUDGMENT',
        r'^C\.C\.',
        r'^PRC\.',
        r'^\d+\s+CC\s+\d+',
        r'^\d+\s+PRC\s+\d+',
        r'^Accused\s*$',
    ]
    for _, row in party_facts.iterrows():
        val = str(row['source_value']).strip()
        for pat in docket_patterns:
            assert not re.match(pat, val, re.IGNORECASE), f"PARTIES fact {row['gold_fact_id']} contains docket header text: {val!r}"


# ---------------------------------------------------------------------------
# Test 10: No unqualified administrative transfer as DISPOSITION
# ---------------------------------------------------------------------------
def test_10_no_unqualified_administrative_transfer_as_disposition(gold_df):
    disp_facts = gold_df[gold_df['category'] == 'DISPOSITION']
    for _, row in disp_facts.iterrows():
        norm = str(row['normalized_value']).lower()
        val = str(row['source_value']).lower()
        assert 'transfer' not in norm, f"Fact {row['gold_fact_id']} misclassified administrative transfer as DISPOSITION: {row['normalized_value']!r}"
        assert 'transfer' not in val, f"Fact {row['gold_fact_id']} misclassified administrative transfer as DISPOSITION: {row['source_value']!r}"
        assert 'lpc' not in norm, f"Fact {row['gold_fact_id']} misclassified LPC entry as DISPOSITION: {row['normalized_value']!r}"


# ---------------------------------------------------------------------------
# Test 11: No duplicate gold facts without relationship metadata
# ---------------------------------------------------------------------------
def test_11_no_duplicate_gold_facts_without_relationship_metadata(gold_df):
    dup_mask = gold_df.duplicated(subset=['doc_id', 'category', 'normalized_value'], keep=False)
    dups = gold_df[dup_mask]
    assert len(dups) == 0, f"Found unmanaged duplicate gold facts:\n{dups[['gold_fact_id', 'doc_id', 'category', 'normalized_value']]}"


# ---------------------------------------------------------------------------
# Test 12: No machine-only fact marked GOLD_VERIFIED
# ---------------------------------------------------------------------------
def test_12_no_machine_only_fact_marked_gold_verified(gold_df):
    for _, row in gold_df.iterrows():
        assert row['verification_status'] == 'GOLD_VERIFIED'
        assert row['reviewer'] == 'HUMAN_LEGAL_AUDITOR'
        assert row['verification_method'] in {'PDF_VISUAL_PLUS_PHASE2', 'PDF_VISUAL', 'PHASE2_TEXT'}


# ---------------------------------------------------------------------------
# Test 13: No source-grounded fact has an invented value
# ---------------------------------------------------------------------------
def test_13_no_source_grounded_fact_has_invented_value(gold_df):
    for _, row in gold_df.iterrows():
        sval = row['source_value'].strip()
        stext = row['source_text']
        # Normalize whitespace for multi-line OCR matches
        norm_sval = ' '.join(sval.split()).lower()
        norm_stext = ' '.join(stext.split()).lower()
        
        # Check first token or full substring match
        first_tok = norm_sval.split()[0].strip('.,()[]{}:;') if norm_sval.split() else ''
        assert first_tok in norm_stext or norm_sval[:20] in norm_stext, (
            f"Fact {row['gold_fact_id']} source_value {sval[:30]!r} not grounded in source_text: {stext[:50]!r}"
        )


# ---------------------------------------------------------------------------
# Test 14: Independent coverage pass recorded for every document
# ---------------------------------------------------------------------------
def test_14_independent_coverage_pass_recorded_for_every_document(gold_df, bench_inv_df):
    independent_facts = gold_df[gold_df['candidate_source'] == 'INDEPENDENT_SOURCE_PASS']
    docs_with_independent_coverage = set(independent_facts['doc_id'].unique())
    all_bench_docs = set(bench_inv_df['doc_id'].unique())
    
    missing = all_bench_docs - docs_with_independent_coverage
    assert len(missing) == 0, f"Documents lacking independent coverage pass facts: {missing}"
    assert len(independent_facts) > 0, "No independent coverage facts found in gold set"
