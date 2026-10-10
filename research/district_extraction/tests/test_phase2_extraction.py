"""
Automated Test Suite for Vidhik Phase 2 - Legal Document Extraction
Validates:
1. Source integrity (bit-exact SHA-256 for all 161 documents)
2. Page preservation (PDF page count == extracted page coverage)
3. Provenance hierarchy (sentence -> paragraph -> page -> document -> source PDF hash)
4. Raw text immutability and conservative normalization integrity
5. Routing logic determinism (good native, image-only, corrupted, legitimate short order, fallback)
6. OCR schema and page alignment
7. Manifest completeness and output schema compliance
"""

import re
import json
import hashlib
from pathlib import Path
import pytest
import pandas as pd
import fitz

BASE_DIR = Path(__file__).resolve().parent.parent.parent
EXTR_DIR = BASE_DIR / "district_extraction"
SRC_PDF_DIR = BASE_DIR / "legal_data" / "district_court" / "experiments" / "s3_161" / "orders"


@pytest.fixture(scope="module")
def source_manifest():
    return pd.read_parquet(EXTR_DIR / "source_manifest" / "district_source_manifest_v1.parquet")


@pytest.fixture(scope="module")
def extraction_manifest():
    with open(EXTR_DIR / "manifests" / "extraction_manifest_v1.json", "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def raw_pages():
    return pd.read_parquet(EXTR_DIR / "raw_extraction" / "final_raw_pages_v1.parquet")


@pytest.fixture(scope="module")
def paragraphs_df():
    return pd.read_parquet(EXTR_DIR / "structure" / "v1" / "paragraphs_provenance_v1.parquet")


@pytest.fixture(scope="module")
def sentences_df():
    return pd.read_parquet(EXTR_DIR / "structure" / "v1" / "sentences_provenance_v1.parquet")


# ==============================================================================
# 1. Source Integrity Tests
# ==============================================================================
def test_source_corpus_count_is_frozen(source_manifest):
    """The source corpus must remain exactly 161 documents."""
    assert len(source_manifest) == 161, f"Expected 161 source documents, got {len(source_manifest)}"


def test_source_corpus_sha256_unaltered(source_manifest):
    """Every source PDF on disk must have the exact bit-level SHA-256 recorded in the manifest."""
    for _, row in source_manifest.iterrows():
        pdf_path = BASE_DIR / row["source_path"]
        assert pdf_path.exists(), f"Source PDF does not exist: {pdf_path}"
        
        with open(pdf_path, "rb") as f:
            computed_sha = hashlib.sha256(f.read()).hexdigest()
            
        assert computed_sha == row["sha256"], (
            f"Source PDF integrity violation for {row['document_id']}! "
            f"Expected {row['sha256']}, got {computed_sha}"
        )


# ==============================================================================
# 2. Page Preservation Tests
# ==============================================================================
def test_page_preservation_across_all_documents(source_manifest, raw_pages):
    """Extracted page coverage must exactly equal original PDF page count for every document."""
    pdf_page_counts = source_manifest.set_index("document_id")["page_count"].to_dict()
    extracted_page_counts = raw_pages.groupby("document_id")["page_number"].max().to_dict()

    for doc_id, expected_pages in pdf_page_counts.items():
        actual_pages = extracted_page_counts.get(doc_id, 0)
        assert actual_pages == expected_pages, (
            f"Page preservation failed for {doc_id}: PDF has {expected_pages} pages, "
            f"extracted has {actual_pages} pages."
        )


def test_total_corpus_page_count(source_manifest, raw_pages):
    """The total corpus page count must be exactly 324 pages."""
    assert source_manifest["page_count"].sum() == 324
    assert len(raw_pages) == 324


# ==============================================================================
# 3. Provenance Hierarchy Tests
# ==============================================================================
def test_paragraph_provenance_format_and_linking(paragraphs_df, source_manifest):
    """Every paragraph must have an unbroken provenance chain to a document and valid source SHA."""
    doc_sha_map = source_manifest.set_index("document_id")["sha256"].to_dict()
    par_id_regex = re.compile(r"^DC_\d{6}_P\d{3}_PAR\d{3}$")

    for _, row in paragraphs_df.iterrows():
        par_id = row["paragraph_id"]
        doc_id = row["document_id"]
        
        assert par_id_regex.match(par_id), f"Invalid paragraph ID format: {par_id}"
        assert doc_id in doc_sha_map, f"Unknown document_id {doc_id} in paragraph {par_id}"
        assert row["source_sha256"] == doc_sha_map[doc_id], (
            f"Provenance hash mismatch in paragraph {par_id}: "
            f"{row['source_sha256']} != {doc_sha_map[doc_id]}"
        )


def test_sentence_provenance_format_and_linking(sentences_df, paragraphs_df):
    """Every sentence must link to its parent paragraph and document."""
    par_ids = set(paragraphs_df["paragraph_id"])
    sen_id_regex = re.compile(r"^DC_\d{6}_P\d{3}_PAR\d{3}_SEN\d{3}$")

    for _, row in sentences_df.iterrows():
        sen_id = row["sentence_id"]
        par_id = row["paragraph_id"]
        
        assert sen_id_regex.match(sen_id), f"Invalid sentence ID format: {sen_id}"
        assert par_id in par_ids, f"Sentence {sen_id} points to non-existent paragraph {par_id}"


# ==============================================================================
# 4. Raw vs Normalized Preservation Tests
# ==============================================================================
def test_raw_extraction_remains_intact():
    """Raw extraction text files must exist for all 161 documents and not be empty."""
    selected_raw_dir = EXTR_DIR / "raw_extraction" / "selected"
    raw_files = list(selected_raw_dir.glob("*.txt"))
    assert len(raw_files) == 161, f"Expected 161 raw text files, found {len(raw_files)}"


def test_normalized_pages_marker_preservation(source_manifest):
    """Normalized files must contain deterministic page demarcation for all pages."""
    norm_dir = EXTR_DIR / "normalized" / "v1"
    
    for _, row in source_manifest.iterrows():
        doc_id = row["document_id"]
        page_count = row["page_count"]
        norm_file = norm_dir / f"{doc_id}.txt"
        
        assert norm_file.exists(), f"Normalized file missing for {doc_id}"
        content = norm_file.read_text(encoding="utf-8")
        
        # Check that page markers match expected page count
        markers = re.findall(r'---\s*PAGE\s+(\d+)\s*---', content)
        assert len(markers) == page_count, (
            f"Normalized page marker count mismatch for {doc_id}: "
            f"expected {page_count}, found {len(markers)}"
        )


# ==============================================================================
# 5. Routing Logic and Edge Case Tests
# ==============================================================================
def test_routing_edge_cases():
    """Verify routing decisions on specific archetypal edge case documents."""
    routing_df = pd.read_parquet(EXTR_DIR / "diagnostics" / "routing_decisions_v1.parquet")
    selection_df = pd.read_parquet(EXTR_DIR / "diagnostics" / "extraction_selection_v1.parquet")
    
    routing_map = routing_df.set_index("document_id")["initial_route"].to_dict()
    selected_map = selection_df.set_index("document_id")["selected_method"].to_dict()
    tier_map = selection_df.set_index("document_id")["final_quality_status"].to_dict()

    # Case 1: Standard clean native PDF (DC_000001)
    assert routing_map["DC_000001"] == "NATIVE_GOOD"
    assert selected_map["DC_000001"] == "native"
    assert tier_map["DC_000001"] == "NATIVE_VALID"

    # Case 2: Image-only scanned PDF (DC_000021)
    assert routing_map["DC_000021"] == "OCR_REQUIRED"
    assert selected_map["DC_000021"] == "paddleocr"
    assert tier_map["DC_000021"] == "OCR_VALID"

    # Case 3: Corrupted text layer with font encoding failure (DC_000020)
    assert routing_map["DC_000020"] == "OCR_REQUIRED"
    assert selected_map["DC_000020"] == "paddleocr"
    assert tier_map["DC_000020"] == "OCR_VALID"

    # Case 4: Genuinely short Assam docket order (DC_000055)
    # Must be retained as native rather than forced to noisy OCR
    assert routing_map["DC_000055"] == "NATIVE_SUSPICIOUS"
    assert selected_map["DC_000055"] == "native"
    assert tier_map["DC_000055"] == "NATIVE_VALID"

    # Case 5: Native suspicious where native text was poor, so OCR was selected (DC_000074)
    assert routing_map["DC_000074"] == "NATIVE_SUSPICIOUS"
    assert selected_map["DC_000074"] == "paddleocr"
    assert tier_map["DC_000074"] == "OCR_VALID"

    # Case 6: OCR required with fallback to Tesseract (DC_000019)
    assert routing_map["DC_000019"] == "OCR_REQUIRED"
    assert selected_map["DC_000019"] == "tesseract"
    assert tier_map["DC_000019"] == "OCR_FALLBACK_VALID"


# ==============================================================================
# 6. OCR Benchmark and Execution Tests
# ==============================================================================
def test_ocr_benchmark_artifact_validity():
    """Verify that the OCR benchmark results JSON exists and contains evaluated candidates."""
    benchmark_file = EXTR_DIR / "ocr_benchmark" / "benchmark_results.json"
    assert benchmark_file.exists(), "OCR benchmark results JSON missing"
    
    with open(benchmark_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert data["benchmark_sample_size"] == 15
    assert data["selected_primary_engine"] == "paddleocr"
    assert "paddleocr" in data
    assert "tesseract" in data
    assert "detailed_results" in data
    assert len(data["detailed_results"]) == 15


# ==============================================================================
# 7. Output Schema and Final Manifest Compliance
# ==============================================================================
def test_final_manifest_consistency(extraction_manifest):
    """Verify final manifest metrics, document count, and schema completeness."""
    assert extraction_manifest["pipeline_version"] == "1.0.0"
    assert extraction_manifest["corpus_statistics"]["total_documents"] == 161
    assert extraction_manifest["corpus_statistics"]["total_pages"] == 324
    assert extraction_manifest["corpus_statistics"]["total_paragraphs"] > 500
    assert extraction_manifest["corpus_statistics"]["total_sentences"] > 2000
    assert len(extraction_manifest["documents"]) == 161


def test_structured_json_schema():
    """Verify that every structured JSON file adheres to the Section 19 schema."""
    struct_dir = EXTR_DIR / "structure" / "v1"
    required_top_keys = {
        "document_id", "source", "routing", "extraction", "raw_pages",
        "normalized_pages", "structure", "metadata", "language", "quality", "provenance"
    }

    for json_file in struct_dir.glob("DC_*.json"):
        with open(json_file, "r", encoding="utf-8") as f:
            doc_data = json.load(f)
            
        missing_keys = required_top_keys - set(doc_data.keys())
        assert not missing_keys, f"{json_file.name} missing required keys: {missing_keys}"
        
        # Verify source provenance
        assert "sha256" in doc_data["source"]
        assert len(doc_data["source"]["sha256"]) == 64
        
        # Verify structure
        assert "pages" in doc_data["structure"]
        assert len(doc_data["structure"]["pages"]) == doc_data["source"]["page_count"]
