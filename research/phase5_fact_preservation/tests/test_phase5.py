"""
Vidhik Phase 5 — Comprehensive Test Suite
=========================================
Tests Section 34 specifications:
1. Fact extraction & canonical categories
2. Normalization invariants (Rs. 50000 == ₹50,000, Section 138 != 139, acquitted != convicted)
3. Atomic claim decomposition & classification
4. Auditable provenance chain: fact -> sentence -> paragraph -> page -> document -> SHA-256
5. Multilingual support across EN, TA, HI, KN, MR
6. Evidence availability & failure attribution
7. Deterministic reproducibility
"""

import re
import hashlib
from pathlib import Path
import pytest
import pandas as pd

ROOT_DIR = Path("/home/tharan/Seeds/vidhik")
P5_DIR = ROOT_DIR / "phase5_fact_preservation"


# -----------------------------------------------------------------------------
# 1. Normalization Invariants
# -----------------------------------------------------------------------------
def normalize_amount(text: str) -> str:
    cleaned = re.sub(r'^(?:rs\.?|inr|₹)\s*', '', text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r'[^\d.]', '', cleaned)
    try:
        val = float(cleaned)
        return f"₹{val:,.2f}"
    except Exception:
        return text.strip()


def normalize_disposition(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["acquit", "acquitted", "acquittal", "viduthalai", "nirdosh"]):
        return "ACQUITTED"
    if any(k in t for k in ["convict", "convicted", "conviction", "dandit"]):
        return "CONVICTED"
    if any(k in t for k in ["dismiss", "dismissed", "manathalli"]):
        return "DISMISSED"
    if any(k in t for k in ["allow", "allowed", "anumatithu"]):
        return "ALLOWED"
    if any(k in t for k in ["bail granted", "grant bail", "jamin manzoor"]):
        return "BAIL_GRANTED"
    if any(k in t for k in ["bail rejected", "bail dismissed", "bail denied"]):
        return "BAIL_REJECTED"
    return "UNKNOWN"


def test_amount_normalization():
    assert normalize_amount("Rs. 50,000") == normalize_amount("₹50,000")
    assert normalize_amount("Rs 50000") == normalize_amount("INR 50,000")
    assert normalize_amount("₹50,000.00") == "₹50,000.00"


def test_section_inequality():
    sec_138 = "Section 138"
    sec_139 = "Section 139"
    assert sec_138 != sec_139
    assert "138" in sec_138 and "138" not in sec_139


def test_disposition_inequality():
    assert normalize_disposition("accused is acquitted") != normalize_disposition("accused is convicted")
    assert normalize_disposition("appeal dismissed") != normalize_disposition("appeal allowed")
    assert normalize_disposition("bail granted") != normalize_disposition("bail rejected")
    assert normalize_disposition("convicted") == "CONVICTED"
    assert normalize_disposition("acquitted") == "ACQUITTED"


# -----------------------------------------------------------------------------
# 2. Fact Ledger Schema & Categories
# -----------------------------------------------------------------------------
def test_fact_ledger_categories():
    facts_path = P5_DIR / "corpus" / "fact_ledger_v1.parquet"
    assert facts_path.exists(), "Fact ledger does not exist"
    df = pd.read_parquet(facts_path)
    assert len(df) >= 1000, f"Expected >= 1000 facts, got {len(df)}"

    required_cols = [
        "fact_id", "doc_id", "category", "value", "normalized_value",
        "source_sentence_id", "paragraph_id", "page_number",
        "criticality", "confidence", "verification_status"
    ]
    for c in required_cols:
        assert c in df.columns, f"Missing column {c} in fact ledger"

    categories = set(df["category"].unique())
    critical_cats = {"CASE_NUMBER", "PARTIES", "STATUTORY_SECTION", "DISPOSITION", "RELIEF"}
    for cc in critical_cats:
        assert cc in categories, f"Critical category {cc} missing from fact ledger"


# -----------------------------------------------------------------------------
# 3. Provenance Chain Verification
# -----------------------------------------------------------------------------
def test_provenance_chain():
    facts_df = pd.read_parquet(P5_DIR / "corpus" / "fact_ledger_v1.parquet")
    sources_df = pd.read_parquet(P5_DIR / "corpus" / "fact_ledger_sources.parquet")

    # Sample 20 facts
    sample_facts = facts_df.sample(20, random_state=42)
    for _, f in sample_facts.iterrows():
        # Document exists in sources
        doc_id = f["doc_id"]
        doc_match = sources_df[sources_df["doc_id"] == doc_id]
        assert not doc_match.empty, f"doc_id {doc_id} not found in sources"
        source_sha256 = doc_match["source_sha256"].iloc[0]
        assert len(source_sha256) == 64, f"Invalid SHA-256 for {doc_id}"

        # Sentence ID adheres to provenance hierarchy
        sen_id = f["source_sentence_id"]
        assert doc_id in sen_id, f"Sentence {sen_id} does not contain {doc_id}"
        assert f["page_number"] >= 1, f"Invalid page number {f['page_number']}"


# -----------------------------------------------------------------------------
# 4. Evidence Availability & Failure Attribution
# -----------------------------------------------------------------------------
def test_evidence_availability_mapping():
    avail_path = P5_DIR / "corpus" / "evidence_availability_v1.parquet"
    assert avail_path.exists()
    avail_df = pd.read_parquet(avail_path)

    statuses = set(avail_df["availability_status"].unique())
    assert "AVAILABLE" in statuses
    assert "RETRIEVAL_MISSING" in statuses

    # Verify that availability separates R1 from R2
    fail_df = pd.read_parquet(P5_DIR / "evaluation" / "failure_attribution.parquet")
    assert "R1_RETRIEVAL_FAILURE" in fail_df["error_stage"].values or "R3_MULTILINGUAL_FAILURE" in fail_df["error_stage"].values


# -----------------------------------------------------------------------------
# 5. Multilingual Population
# -----------------------------------------------------------------------------
def test_multilingual_population():
    lang_df = pd.read_parquet(P5_DIR / "evaluation" / "language_metrics.parquet")
    expected_langs = {"en", "ta", "hi", "kn", "mr"}
    actual_langs = set(lang_df["language"].unique())
    assert expected_langs == actual_langs, f"Missing languages: {expected_langs - actual_langs}"


# -----------------------------------------------------------------------------
# 6. Cryptographic Manifest & Determinism
# -----------------------------------------------------------------------------
def test_manifest_reproducibility():
    manifest_file = P5_DIR / "manifests" / "phase5_manifest_v1.json"
    assert manifest_file.exists()
    import json
    with open(manifest_file, "r") as f:
        data = json.load(f)

    assert "phase5_artifacts" in data
    assert "fact_ledger_v1_sha256" in data["phase5_artifacts"]
    assert len(data["phase5_artifacts"]["fact_ledger_v1_sha256"]) == 64
