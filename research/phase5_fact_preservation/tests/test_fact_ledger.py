"""
Vidhik Phase 5 - Automated Test Suite for Legal Fact Ledger (P5.1)
Verifies:
1. Schema compliance (required fields and data types).
2. Provenance linkage back to sentence, paragraph, page, document, and source SHA-256.
3. Criticality tier mapping.
4. Deterministic normalization rules (dates, amounts, case numbers, statutory sections, dispositions).
5. Explicit distinction enforcement (Rs. 50,000 == ₹50,000; Section 138 != Section 139; acquitted != convicted).
6. Confidence and verification status constraints.
"""

import sys
import re
import pytest
import pandas as pd
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))
PHASE5_DIR = ROOT_DIR / "phase5_fact_preservation"
CORPUS_DIR = PHASE5_DIR / "corpus"
PROTOTYPE_PARQUET = CORPUS_DIR / "fact_ledger_prototype_v1.parquet"


@pytest.fixture(scope="module")
def fact_df():
    assert PROTOTYPE_PARQUET.exists(), f"Fact ledger prototype parquet missing at {PROTOTYPE_PARQUET}"
    df = pd.read_parquet(PROTOTYPE_PARQUET)
    assert not df.empty, "Fact ledger prototype must not be empty"
    return df


# Test 1: File existence and row count
def test_1_prototype_file_and_volume(fact_df):
    assert len(fact_df) >= 50, f"Expected at least 50 extracted canonical facts, got {len(fact_df)}"
    assert fact_df["doc_id"].nunique() >= 5, "Expected facts across multiple documents"


# Test 2: Schema compliance
def test_2_schema_compliance(fact_df):
    required_cols = [
        "fact_id", "doc_id", "source_sha256", "category", "value",
        "normalized_value", "source_sentence_id", "paragraph_id",
        "page_number", "criticality", "confidence", "verification_status",
        "provenance_chain"
    ]
    for col in required_cols:
        assert col in fact_df.columns, f"Required column '{col}' missing from fact ledger"


# Test 3: Criticality validity and mapping
def test_3_criticality_mapping(fact_df):
    allowed_tiers = {"CRITICAL", "IMPORTANT", "CONTEXTUAL"}
    for val in fact_df["criticality"].unique():
        assert val in allowed_tiers, f"Invalid criticality tier: {val}"

    # Critical categories must map to CRITICAL
    critical_categories = {"DISPOSITION", "STATUTORY_SECTION", "CASE_NUMBER", "PARTIES"}
    for _, row in fact_df.iterrows():
        if row["category"] in critical_categories:
            assert row["criticality"] == "CRITICAL", f"Category {row['category']} must be CRITICAL, got {row['criticality']}"


# Test 4: Provenance chain integrity
def test_4_provenance_chain_integrity(fact_df):
    for _, row in fact_df.iterrows():
        chain = row["provenance_chain"]
        assert "->" in chain, "Provenance chain must have directional arrow delimiters"
        assert row["source_sentence_id"] in chain, "Sentence ID must be in provenance chain"
        assert row["paragraph_id"] in chain, "Paragraph ID must be in provenance chain"
        assert f"Page {row['page_number']}" in chain, "Page number must be in provenance chain"
        assert row["doc_id"] in chain, "Document ID must be in provenance chain"
        assert "SHA256:" in chain, "SHA256 prefix must be in provenance chain"


# Test 5: Source SHA-256 integrity
def test_5_sha256_integrity(fact_df):
    for sha in fact_df["source_sha256"].unique():
        assert isinstance(sha, str)
        assert len(sha) == 64, f"SHA256 must be exactly 64 hex characters, got '{sha}'"
        assert all(c in "0123456789abcdefABCDEF" for c in sha)


# Test 6: Normalization: Dates
def test_6_date_normalization(fact_df):
    dates_df = fact_df[fact_df["category"] == "DECISION_DATE"]
    assert not dates_df.empty, "DECISION_DATE facts must be present"
    for _, row in dates_df.iterrows():
        norm_val = row["normalized_value"]
        # Must be ISO YYYY-MM-DD format
        assert re.match(r'^\d{4}-\d{2}-\d{2}$', norm_val), f"Date normalized value '{norm_val}' is not in YYYY-MM-DD ISO format"


# Test 7: Normalization: Amounts (Rs. 50,000 == ₹50,000)
def test_7_amount_normalization():
    from stage5_1_fact_ledger_prototype import normalize_amount
    norm1 = normalize_amount("Rs. 50,000")
    norm2 = normalize_amount("₹50,000")
    norm3 = normalize_amount("INR 50000")
    assert norm1 == "₹50,000.00", f"Expected ₹50,000.00, got {norm1}"
    assert norm2 == "₹50,000.00", f"Expected ₹50,000.00, got {norm2}"
    assert norm3 == "₹50,000.00", f"Expected ₹50,000.00, got {norm3}"
    assert norm1 == norm2 == norm3, "Currency representations Rs. 50,000 and ₹50,000 must normalize to identical value"


# Test 8: Distinction enforcement: Section 138 != Section 139
def test_8_statutory_section_distinction():
    from stage5_1_fact_ledger_prototype import normalize_statutory_section
    sec_138 = normalize_statutory_section("138", "NI Act")
    sec_139 = normalize_statutory_section("139", "NI Act")
    assert sec_138 != sec_139, f"Section 138 and 139 must never be identical: {sec_138} vs {sec_139}"
    assert sec_138 == "SEC_138_NIACT"
    assert sec_139 == "SEC_139_NIACT"


# Test 9: Distinction enforcement: acquitted != convicted
def test_9_disposition_distinction(fact_df):
    from stage5_1_fact_ledger_prototype import DISPOSITION_LEXICON
    assert DISPOSITION_LEXICON["acquitted"] != DISPOSITION_LEXICON["convicted"]
    assert DISPOSITION_LEXICON["dismissed"] != DISPOSITION_LEXICON["allowed"]
    assert DISPOSITION_LEXICON["granted"] != DISPOSITION_LEXICON["denied"]


# Test 10: Confidence score and audit status bounds
def test_10_confidence_and_verification_status(fact_df):
    allowed_statuses = {"machine_extracted", "human_verified", "human_corrected", "ambiguous"}
    for _, row in fact_df.iterrows():
        conf = row["confidence"]
        assert 0.0 <= conf <= 1.0, f"Confidence {conf} out of bounds [0.0, 1.0]"
        status = row["verification_status"]
        assert status in allowed_statuses, f"Invalid verification status: {status}"
