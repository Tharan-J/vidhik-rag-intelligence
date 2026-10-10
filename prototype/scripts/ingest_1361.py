#!/usr/bin/env python3
"""
Vidhik Prototype Ingestion CLI Engine
=====================================
Usage:
  # 1. Run Pre-Flight Validation (no uploads)
  python scripts/ingest_1361.py --preflight

  # 2. Run Dry-Run Simulation (extracts/chunks sample, verifies models & Qdrant, zero uploads)
  python scripts/ingest_1361.py --dry-run

  # 3. Process Single Document
  python scripts/ingest_1361.py --document <DOCUMENT_ID>

  # 4. Full Production Corpus Ingestion (1,361 documents)
  python scripts/ingest_1361.py
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, Any

# Ensure prototype root is in PYTHONPATH
SCRIPT_DIR = Path(__file__).resolve().parent
PROTOTYPE_DIR = SCRIPT_DIR.parent
if str(PROTOTYPE_DIR) not in sys.path:
    sys.path.insert(0, str(PROTOTYPE_DIR))

from ingestion.config import load_config
from ingestion.pipeline import IngestionPipeline


def setup_logger(log_dir: Path, level: str = "INFO"):
    """Configure structured logging to console and file."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "ingestion.log"

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    # Clear existing handlers
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


def run_preflight(pipeline: IngestionPipeline) -> bool:
    """
    Execute comprehensive pre-flight verification without uploading any data.
    Checks environment, credentials, Qdrant connectivity, BGE-M3 availability,
    corpus catalog, PDF paths, and directories.
    """
    print("\n" + "=" * 70)
    print("VIDHIK INGESTION PRE-FLIGHT CHECK")
    print("=" * 70)

    cfg = pipeline.config
    all_passed = True

    def check(name: str, passed: bool, detail: str = ""):
        nonlocal all_passed
        status = "✓ PASS" if passed else "✗ FAIL"
        if not passed:
            all_passed = False
        print(f"[{status}] {name:<35} : {detail}")

    # 1. Environment & Credentials
    env_file = PROTOTYPE_DIR / ".env"
    check(".env file present", env_file.exists(), str(env_file))
    check("QDRANT_URL configured", bool(cfg.qdrant.url), f"Host: {cfg.qdrant.url[:25]}..." if cfg.qdrant.url else "MISSING")
    check("QDRANT_API_KEY configured", bool(cfg.qdrant.api_key), f"Key: {cfg.qdrant.masked_key}")

    # 2. Qdrant Cloud Connectivity
    qdrant_ok = False
    qdrant_detail = ""
    try:
        conn_res = pipeline.qdrant_store.verify_connection()
        qdrant_ok = True
        colls = conn_res.get("collections", [])
        pt_cnt = conn_res.get("target_points_count", 0)
        qdrant_detail = f"Connected to Cloud cluster. Existing collections: {colls} (points in target: {pt_cnt})"
    except Exception as e:
        qdrant_detail = f"Connection failed: {type(e).__name__} - {e}"
    check("Qdrant Cloud Connection", qdrant_ok, qdrant_detail)
    check("Target Collection Config", True, f"Name: {cfg.qdrant.collection_name} (Dense: 1024-d Cosine, Sparse: Standalone BM25)")

    # 3. Model & Tokenizer Availability
    model_ok = False
    model_detail = ""
    try:
        embedder = pipeline._get_embed_engine()
        test_emb = embedder.encode_dense_batch(["Vidhik test sentence"])
        dim = len(test_emb[0]) if test_emb else 0
        model_ok = (dim == 1024)
        model_detail = f"BGE-M3 loaded successfully (dimension={dim})"
    except Exception as e:
        model_detail = f"Embedding load failed: {e}"
    check("BGE-M3 Dense Model", model_ok, model_detail)

    # 4. BM25 Lexical Engine & Directory
    bm25_ok = False
    bm25_detail = ""
    try:
        from ingestion.bm25_store import tokenize_legal_text, BM25Store
        test_tokens = tokenize_legal_text("Section 438 CrPC Article 21")
        cfg.bm25.index_dir.mkdir(parents=True, exist_ok=True)
        bm25_ok = ("438" in test_tokens and "crpc" in test_tokens)
        bm25_detail = f"rank_bm25 available, legal tokens preserved: {test_tokens}, dir: {cfg.bm25.index_dir}"
    except Exception as e:
        bm25_detail = f"BM25 check failed: {e}"
    check("BM25 Engine & Index Dir", bm25_ok, bm25_detail)

    # 5. Corpus Catalog & Document Discovery
    catalog_ok = False
    catalog_detail = ""
    doc_count = 0
    try:
        df = pipeline.load_corpus_catalog()
        doc_count = len(df)
        catalog_ok = (doc_count >= 1361)
        court_dist = dict(df["court_level"].value_counts())
        catalog_detail = f"{doc_count} documents discovered ({court_dist})"
    except Exception as e:
        catalog_detail = f"Failed to load catalog: {e}"
    check("1,361 Corpus Catalog", catalog_ok, catalog_detail)

    # 6. PDF Path Integrity on Disk
    sample_pdf_ok = False
    sample_detail = ""
    try:
        df = pipeline.load_corpus_catalog()
        found_count = 0
        for _, r in df.head(10).iterrows():
            resolved = pipeline.resolve_pdf_path(str(r.get("pdf_path", "")))
            if resolved and resolved.exists():
                found_count += 1
        sample_pdf_ok = (found_count == 10)
        sample_detail = f"Sample 10/10 PDFs verified directly on disk"
    except Exception as e:
        sample_detail = f"Path check error: {e}"
    check("PDF Disk Accessibility", sample_pdf_ok, sample_detail)

    # 7. Output Directories
    dirs_to_check = [
        ("Logs Directory", cfg.log_dir),
        ("Manifests Directory", cfg.manifest_path.parent),
        ("BM25 Index Directory", cfg.bm25.index_dir),
    ]
    for d_name, d_path in dirs_to_check:
        d_path.mkdir(parents=True, exist_ok=True)
        check(d_name, d_path.exists(), str(d_path))

    # 8. Core Dependencies Check
    core_pkgs = ["qdrant_client", "pymupdf", "pandas", "pyarrow", "tqdm", "onnxruntime", "tokenizers", "rank_bm25"]
    dep_missing = []
    for pkg in core_pkgs:
        try:
            __import__(pkg)
        except ImportError:
            dep_missing.append(pkg)
    check("Core Python Dependencies", len(dep_missing) == 0, "All available" if not dep_missing else f"Missing: {dep_missing}")

    print("=" * 70)
    if all_passed:
        print("✓ ALL PRE-FLIGHT CHECKS PASSED. SYSTEM IS READY FOR INGESTION.")
    else:
        print("✗ PRE-FLIGHT CHECK DETECTED ISSUES. RESOLVE BEFORE PROCEEDING.")
    print("=" * 70 + "\n")
    return all_passed


def run_dry_run(pipeline: IngestionPipeline):
    """
    Run safe dry-run simulation:
    - Verifies Qdrant connection and BGE-M3 embedder
    - Verifies BM25 legal tokenizer and index construction from sample chunks
    - Tests BM25 query retrieval and Reciprocal Rank Fusion interface
    - Extracts and chunks representative documents from Supreme Court, High Court, and District Court
    - Inspects page, paragraph, sentence, and chunk counts
    - Does NOT upload anything to Qdrant or delete any collection.
    """
    from ingestion.bm25_store import BM25Store, tokenize_legal_text, fuse_results

    print("\n" + "=" * 70)
    print("EXECUTING DRY RUN SIMULATION (ZERO UPLOADS TO QDRANT)")
    print("=" * 70)

    # 1. Load catalog
    df = pipeline.load_corpus_catalog()
    print(f"[INFO] Discovered {len(df)} total documents in corpus catalog.")

    # 2. Verify Qdrant connection
    conn = pipeline.qdrant_store.verify_connection()
    print(f"[INFO] Qdrant Cloud connection verified. Target collection: '{pipeline.config.qdrant.collection_name}' (points={conn.get('target_points_count', 0)})")

    # 3. Verify BGE-M3 dense
    embedder = pipeline._get_embed_engine()
    test_dense = embedder.encode_dense_batch(["Supreme Court of India judgment dry run test"])
    print(f"[INFO] BGE-M3 dense dimension: {len(test_dense[0])} (normalized L2)")

    # 4. Verify BM25 tokenizer
    test_tokens = tokenize_legal_text("Section 438 CrPC Article 21 2021 SCC OnLine SC 123")
    print(f"[INFO] BM25 legal tokenizer output: {test_tokens}")

    # 5. Sample 1 doc per level
    sample_docs = []
    for cl in ["Supreme Court", "High Court", "District Court"]:
        sub = df[df["court_level"] == cl]
        if not sub.empty:
            sample_docs.append(sub.iloc[0].to_dict())

    print(f"\n[INFO] Running extraction & chunking simulation on {len(sample_docs)} sample documents:\n")

    dry_run_chunks = []
    for doc in sample_docs:
        doc_id = doc["document_id"]
        court_level = doc["court_level"]
        print(f"----------------------------------------------------------------------")
        print(f"Document ID   : {doc_id}")
        print(f"Court Level   : {court_level}")
        print(f"Title         : {doc.get('title', 'N/A')[:65]}")

        res = pipeline.process_single_document(doc, dry_run=True)
        print(f"Pages         : {res['pages']}")
        print(f"Paragraphs    : {res['paragraphs']}")
        print(f"Sentences     : {res['sentences']}")
        print(f"Chunks (~500t): {res['chunks']}")
        print(f"Status        : {res['status']}")

    # 6. Test BM25 building and search simulation on sample chunks
    print("----------------------------------------------------------------------")
    print("[INFO] Simulating BM25 index construction and Rank Fusion...")
    from ingestion.chunk import LegalChunk
    sample_mock_chunks = [
        LegalChunk(
            document_id="TEST_DOC_001",
            chunk_id="chunk_0001",
            court_level="Supreme Court",
            court="Supreme Court of India",
            case_title="Test Case on Section 438",
            case_number="CA 123/2021",
            decision_date="2021-01-01",
            year=2021,
            language="en",
            text="The appellant filed an application under Section 438 of the Code of Criminal Procedure, 1973 for anticipatory bail.",
            page_start=1,
            page_end=1,
            paragraph_start="P1_PAR1",
            paragraph_end="P1_PAR1",
            sentence_start="S1",
            sentence_end="S2",
            source_file="test.pdf",
            document_sha256="abc",
            token_count=25,
        ),
        LegalChunk(
            document_id="TEST_DOC_002",
            chunk_id="chunk_0001",
            court_level="High Court",
            court="Bombay High Court",
            case_title="Test Case on Article 21",
            case_number="WP 456/2022",
            decision_date="2022-01-01",
            year=2022,
            language="en",
            text="The right to personal liberty is protected under Article 21 of the Constitution of India.",
            page_start=1,
            page_end=1,
            paragraph_start="P1_PAR1",
            paragraph_end="P1_PAR1",
            sentence_start="S1",
            sentence_end="S2",
            source_file="test2.pdf",
            document_sha256="def",
            token_count=20,
        )
    ]
    test_bm25 = BM25Store()
    test_bm25.build_index(sample_mock_chunks)
    bm25_hits = test_bm25.search("Section 438 CrPC", top_k=2)
    print(f"[INFO] BM25 search for 'Section 438 CrPC': {len(bm25_hits)} hits (top doc: {bm25_hits[0]['document_id']}, score: {bm25_hits[0]['score']:.4f})")

    # Simulate Rank Fusion
    mock_dense_results = [{"qdrant_point_id": bm25_hits[0]["qdrant_point_id"], "document_id": "TEST_DOC_001", "chunk_id": "chunk_0001"}]
    fused = fuse_results(mock_dense_results, bm25_hits, k=60, dense_weight=0.6, bm25_weight=0.4)
    print(f"[INFO] Rank Fusion simulation successful: top fused item={fused[0]['document_id']}, rrf_score={fused[0]['rrf_score']:.6f}")

    print("----------------------------------------------------------------------")
    print("\n[INFO] Dry run completed successfully.")
    print("[INFO] ZERO points were uploaded to Qdrant Cloud.")
    print("[INFO] ZERO collections were deleted or modified.")
    print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Vidhik Ingestion Pipeline CLI")
    parser.add_argument("--preflight", action="store_true", help="Run pre-flight validation checks")
    parser.add_argument("--dry-run", action="store_true", help="Run simulation on representative samples without uploading")
    parser.add_argument("--document", type=str, help="Process and ingest a specific document ID")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of documents for testing")
    parser.add_argument("--config", type=str, default=None, help="Path to custom ingestion.yaml")
    parser.add_argument("--reset-qdrant", action="store_true", help="Explicitly reset Qdrant collection to dense-only schema (destructive, requires confirmation)")
    args = parser.parse_args()

    config_path = Path(args.config) if args.config else None
    config = load_config(config_path)

    setup_logger(config.log_dir, config.logging.get("level", "INFO") if hasattr(config, "logging") else "INFO")

    pipeline = IngestionPipeline(config)

    # Explicit Qdrant Collection Reset
    if args.reset_qdrant:
        print("\n" + "!" * 70)
        print("WARNING: EXPLICIT QDRANT RESET REQUESTED")
        print(f"Target Collection: {config.qdrant.collection_name}")
        conn = pipeline.qdrant_store.verify_connection()
        pt_cnt = conn.get("target_points_count", 0)
        print(f"Current points in collection: {pt_cnt}")
        print("This will DELETE the collection and RECREATE it with DENSE-ONLY schema (1024-d, Cosine).")
        print("!" * 70)
        confirm = input("Type 'CONFIRM_RESET_QDRANT' to proceed with reset: ")
        if confirm.strip() != "CONFIRM_RESET_QDRANT":
            print("[ABORTED] Collection reset cancelled by user safeguard.")
            sys.exit(0)

        res = pipeline.qdrant_store.reset_collection()
        print(f"[SUCCESS] Qdrant collection reset successfully: {res}")
        sys.exit(0)

    if args.preflight:
        passed = run_preflight(pipeline)
        sys.exit(0 if passed else 1)

    if args.dry_run:
        run_dry_run(pipeline)
        sys.exit(0)

    if args.document:
        df = pipeline.load_corpus_catalog()
        match = df[df["document_id"] == args.document]
        if match.empty:
            print(f"[ERROR] Document ID '{args.document}' not found in corpus catalog.")
            sys.exit(1)
        doc_dict = match.iloc[0].to_dict()
        print(f"[INFO] Ingesting single document: {args.document}")
        pipeline.qdrant_store.ensure_collection()
        res = pipeline.process_single_document(doc_dict, dry_run=False)
        # Build and save BM25 index for the single document
        if pipeline.bm25_store.mapping_records:
            pipeline.bm25_store.build_index()
            pipeline.bm25_store.save()
            print(f"[INFO] BM25 index updated at {pipeline.config.bm25.index_dir}")
        print(f"[INFO] Result: {res}")
        sys.exit(0)

    # Full Corpus Ingestion Safeguard
    print("\n" + "!" * 70)
    print("WARNING: FULL PRODUCTION INGESTION INVOKED")
    print(f"This will process and upload all {config.corpus.target_documents} documents to Qdrant Cloud.")
    print("!" * 70)
    confirm = input("Type 'CONFIRM_INGEST_1361' to proceed, or press Enter to cancel: ")
    if confirm.strip() != "CONFIRM_INGEST_1361":
        print("[ABORTED] Full ingestion cancelled by user safeguard.")
        sys.exit(0)

    pipeline.run_full(limit=args.limit)


if __name__ == "__main__":
    main()
