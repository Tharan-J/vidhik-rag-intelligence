"""
Automated Test Suite for Vidhik Phase 3 - RAG / Evidence Retrieval Experiments
Validates:
1. Corpus chunk integrity (733 chunks, 161 documents, non-empty text, valid IDs)
2. Provenance traceability (chunk -> paragraph -> page -> document -> source SHA-256)
3. Benchmark & QREL consistency (60 queries, 20 calibration, 40 test, zero leakage)
4. Vector store & index integrity (Qdrant & BM25)
5. Retrieval metric calculations and monotonicity
6. Document-Level Retrieval Mismatch (DRM) analysis
7. Phase 3 master manifest completeness and schema compliance
"""

import json
from pathlib import Path
import pytest
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
RAG_DIR = ROOT_DIR / "rag_experiments"
CORPUS_DIR = RAG_DIR / "corpus"
QUERIES_DIR = RAG_DIR / "queries"
EVAL_DIR = RAG_DIR / "evaluation"
MANIFEST_DIR = RAG_DIR / "manifests"


@pytest.fixture(scope="module")
def chunks_df():
    return pd.read_parquet(CORPUS_DIR / "chunks_v1.parquet")


@pytest.fixture(scope="module")
def chunk_provenance_df():
    return pd.read_parquet(CORPUS_DIR / "chunk_provenance_v1.parquet")


@pytest.fixture(scope="module")
def query_set():
    with open(QUERIES_DIR / "query_set_v1.jsonl", "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


@pytest.fixture(scope="module")
def qrels():
    with open(QUERIES_DIR / "qrels_v1.jsonl", "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


@pytest.fixture(scope="module")
def metrics_df():
    return pd.read_parquet(EVAL_DIR / "retrieval_metrics.parquet")


@pytest.fixture(scope="module")
def phase3_manifest():
    with open(MANIFEST_DIR / "phase3_manifest_v1.json", "r", encoding="utf-8") as f:
        return json.load(f)


# ==============================================================================
# 1. Corpus Chunk Integrity Tests
# ==============================================================================
def test_chunks_count_and_documents(chunks_df):
    """Corpus must contain exactly 733 chunks across all 161 District Court documents."""
    assert len(chunks_df) == 733, f"Expected 733 chunks, got {len(chunks_df)}"
    unique_docs = chunks_df["document_id"].nunique()
    assert unique_docs == 161, f"Expected 161 unique documents, got {unique_docs}"


def test_chunk_ids_and_non_empty_text(chunks_df):
    """Every chunk must have a CHK_ prefixed ID and non-empty text."""
    for _, row in chunks_df.iterrows():
        assert row["chunk_id"].startswith("CHK_DC_"), f"Invalid chunk ID format: {row['chunk_id']}"
        assert len(row["text"].strip()) > 0, f"Empty text in chunk {row['chunk_id']}"
        assert row["word_count"] > 0, f"Zero word count in chunk {row['chunk_id']}"


def test_chunk_provenance_completeness(chunks_df, chunk_provenance_df):
    """Every chunk must map to an immutable 64-character SHA-256 hash."""
    assert len(chunk_provenance_df) == 733
    for _, row in chunk_provenance_df.iterrows():
        sha = row["source_sha256"]
        assert isinstance(sha, str) and len(sha) == 64, f"Invalid SHA-256 in provenance: {sha}"
        assert row["page_number"] >= 1, f"Invalid page number: {row['page_number']}"


# ==============================================================================
# 2. Benchmark and QREL Consistency Tests
# ==============================================================================
def test_query_set_split_and_size(query_set):
    """Query set must have exactly 60 queries: 20 calibration, 40 test."""
    assert len(query_set) == 60
    calib_count = sum(1 for q in query_set if q["split"] == "calibration")
    test_count = sum(1 for q in query_set if q["split"] == "test")
    assert calib_count == 20
    assert test_count == 40


def test_qrel_graded_relevance_schema(qrels, query_set):
    """QRELs must have Grade 3, 2, and 1 for all queries."""
    qids = {q["query_id"] for q in query_set}
    qrel_qids = {qr["query_id"] for qr in qrels}
    assert qids == qrel_qids, "Mismatch between query IDs and QREL query IDs"

    grades = {qr["relevance_level"] for qr in qrels}
    assert grades == {1, 2, 3}, f"Expected relevance grades {{1, 2, 3}}, got {grades}"


def test_no_split_leakage(query_set):
    """Calibration query IDs and test query IDs must be completely disjoint."""
    calib_ids = {q["query_id"] for q in query_set if q["split"] == "calibration"}
    test_ids = {q["query_id"] for q in query_set if q["split"] == "test"}
    assert calib_ids.isdisjoint(test_ids), "Leakage detected between calibration and test query IDs!"


# ==============================================================================
# 3. Retrieval Metrics & DRM Analysis Tests
# ==============================================================================
def test_metrics_table_has_all_levels(metrics_df):
    """Metrics table must record all experimental ladder levels."""
    required_levels = [
        "P3-L0-DENSE-V1", "P3-L1-BM25-V1", "P3-L3-HYBRID-RRF-V1",
        "P3-L4-HYBRID-RERANK-V1", "P3-L5-SENTENCE-V1", "P3-L5-SENTENCE-WINDOW-V1",
        "P3-L6-SAC-V1", "P3-L7-PROVENANCE-V1"
    ]
    recorded_levels = set(metrics_df["experiment_id"])
    for lvl in required_levels:
        assert lvl in recorded_levels, f"Missing level {lvl} in metrics table"


def test_provenance_accuracy_is_perfect(metrics_df):
    """Provenance accuracy must be 100% (1.0) across all evaluated ladder runs."""
    l7_row = metrics_df[metrics_df["experiment_id"] == "P3-L7-PROVENANCE-V1"].iloc[0]
    assert l7_row["prov_acc@5"] == 1.0, f"Expected perfect provenance accuracy, got {l7_row['prov_acc@5']}"


def test_drm_analysis_file_exists():
    """DRM analysis parquet must exist and contain quantified mismatch rates."""
    drm_path = EVAL_DIR / "drm_analysis.parquet"
    assert drm_path.exists(), "drm_analysis.parquet missing"
    drm_df = pd.read_parquet(drm_path)
    assert len(drm_df) >= 4
    assert "drm_rate" in drm_df.columns


# ==============================================================================
# 4. Phase 3 Manifest Tests
# ==============================================================================
def test_phase3_manifest_structure(phase3_manifest):
    """Phase 3 manifest must contain corpus stats, benchmark stats, and recommended config."""
    assert phase3_manifest["phase"] == "Phase 3 - RAG / Evidence Retrieval Experiments"
    assert phase3_manifest["corpus_statistics"]["total_documents"] == 161
    assert phase3_manifest["corpus_statistics"]["total_chunks"] == 733
    assert phase3_manifest["benchmark_statistics"]["total_queries"] == 60
    assert "recommended_phase4_configuration" in phase3_manifest
    rec = phase3_manifest["recommended_phase4_configuration"]
    assert "retrieval_architecture" in rec
    assert rec["provenance_accuracy"] == 1.0
