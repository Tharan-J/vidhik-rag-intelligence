"""
End-to-End Vidhik Ingestion Pipeline Engine
===========================================
Coordinates the entire flow:
Corpus Discovery -> PDF Validation -> Page Extraction (Native/OCR) -> Normalization ->
Structure Reconstruction -> Structure-Aware Chunking -> BGE-M3 Embedding -> Qdrant Cloud Upsert -> Manifest Tracking
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from tqdm import tqdm

from .config import IngestionConfig
from .extract import extract_document, PDFValidationError
from .normalize import normalize_legal_text
from .structure import build_document_structure
from .chunk import chunk_document, LegalChunk
from .embed import BGEM3EmbeddingEngine
from .qdrant_store import QdrantCloudStore
from .bm25_store import BM25Store
from .manifest import IngestionManifest

logger = logging.getLogger("VidhikIngestion.Pipeline")


class IngestionPipeline:
    def __init__(self, config: IngestionConfig):
        self.config = config
        self.manifest = IngestionManifest(
            parquet_path=config.manifest_path,
            csv_path=config.manifest_csv_path
        )
        self.qdrant_store = QdrantCloudStore(
            url=config.qdrant.url,
            api_key=config.qdrant.api_key,
            collection_name=config.qdrant.collection_name,
            dense_vector_name=config.qdrant.dense_vector_name,
            upsert_batch_size=config.qdrant.upsert_batch_size,
            timeout=config.qdrant.timeout,
            https=config.qdrant.https,
            port=config.qdrant.port,
        )
        self.bm25_store = BM25Store(
            index_dir=config.bm25.index_dir,
            index_file=config.bm25.index_file,
            mapping_file=config.bm25.mapping_file,
            k1=config.bm25.k1,
            b=config.bm25.b,
            epsilon=config.bm25.epsilon,
        )
        self.embed_engine: Optional[BGEM3EmbeddingEngine] = None
        self._corpus_df: Optional[pd.DataFrame] = None

    def _get_embed_engine(self) -> BGEM3EmbeddingEngine:
        """Lazily initialize embedding engine."""
        if self.embed_engine is None:
            self.embed_engine = BGEM3EmbeddingEngine(
                model_name=self.config.embedding.model,
                local_model_dir=self.config.embedding.local_model_dir,
                onnx_model_file=self.config.embedding.onnx_model_file,
                tokenizer_file=self.config.embedding.tokenizer_file,
                dense_dim=self.config.embedding.dense_dim,
                max_length=self.config.embedding.max_length,
                batch_size=self.config.embedding.batch_size,
            )
        return self.embed_engine

    def load_corpus_catalog(self) -> pd.DataFrame:
        """Load and resolve master corpus metadata for 1,361 documents."""
        if self._corpus_df is not None:
            return self._corpus_df

        meta_p = self.config.corpus.master_metadata_parquet
        if meta_p.exists():
            logger.info(f"Loading master catalog from {meta_p}...")
            df = pd.read_parquet(meta_p)
        else:
            meta_csv = self.config.corpus.master_metadata_csv
            if meta_csv.exists():
                logger.info(f"Loading master catalog from CSV fallback {meta_csv}...")
                df = pd.read_csv(meta_csv)
            else:
                raise FileNotFoundError(f"Corpus catalog not found at {meta_p} or {meta_csv}")

        logger.info(f"Discovered {len(df)} documents in corpus catalog.")
        self._corpus_df = df
        return df

    def resolve_pdf_path(self, raw_path: str) -> Optional[Path]:
        """Resolve PDF path on disk across repository structure variants."""
        if not raw_path or pd.isna(raw_path):
            return None

        p = Path(raw_path)
        if p.exists():
            return p

        # Check in research/legal_data
        raw_str = str(raw_path)
        if "/legal_data/" in raw_str:
            sub = raw_str.split("/legal_data/", 1)[1]
            alt1 = self.config.corpus.legal_data_dir / sub
            if alt1.exists():
                return alt1
            alt2 = self.config.base_dir.parent / "research" / "legal_data" / sub
            if alt2.exists():
                return alt2

        # Check relative to base repo
        repo_root = self.config.base_dir.parent
        alt3 = repo_root / raw_str.lstrip("/")
        if alt3.exists():
            return alt3

        return None

    def resolve_pre_extracted_json(self, doc_id: str) -> Optional[Path]:
        """Check if verified pre-extracted structured JSON exists for this document."""
        struct_dir = self.config.corpus.district_structure_dir
        if not struct_dir.exists():
            return None

        # Direct check
        cand1 = struct_dir / f"{doc_id}.json"
        if cand1.exists():
            return cand1

        # Check DC numbering mapping (e.g. DC_DC-S3-001 -> DC_000001)
        if "DC-S3-" in doc_id:
            try:
                # Extract number
                parts = doc_id.split("DC-S3-")[1].split("_")[0]
                num = int(parts)
                cand2 = struct_dir / f"DC_{num:06d}.json"
                if cand2.exists():
                    return cand2
            except Exception:
                pass

        return None

    def process_single_document(
        self,
        doc_row: Dict[str, Any],
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Process a single document through extraction, structuring, chunking, and upload.
        """
        doc_id = str(doc_row["document_id"])
        raw_pdf_path = str(doc_row.get("pdf_path", ""))
        pdf_path = self.resolve_pdf_path(raw_pdf_path)
        sha256 = str(doc_row.get("pdf_sha256", "UNKNOWN_SHA256"))

        if not pdf_path or not pdf_path.exists():
            msg = f"PDF file not found on disk for document_id={doc_id} (path={raw_pdf_path})"
            if not dry_run:
                self.manifest.record_failure(doc_id, raw_pdf_path, "path_resolution", msg)
            raise FileNotFoundError(msg)

        # Check verified cache
        cached_json = self.resolve_pre_extracted_json(doc_id)

        # Stage 1: Extraction
        try:
            pages_data = extract_document(
                pdf_path=pdf_path,
                pre_extracted_json=cached_json,
                min_page_chars=self.config.extraction.min_page_chars,
                enable_ocr_fallback=True,
            )
        except Exception as e:
            if not dry_run:
                self.manifest.record_failure(doc_id, str(pdf_path), "extraction", str(e))
            raise

        # Stage 2: Structure Reconstruction
        try:
            doc_struct = build_document_structure(
                document_id=doc_id,
                pages_data=pages_data,
                metadata=doc_row,
                source_file=str(pdf_path),
                document_sha256=sha256,
                pre_extracted_json=cached_json,
            )
        except Exception as e:
            if not dry_run:
                self.manifest.record_failure(doc_id, str(pdf_path), "structure", str(e))
            raise

        page_count = len(doc_struct.pages)
        par_count = len(doc_struct.paragraphs)
        sen_count = len(doc_struct.sentences)

        # Stage 3: Structure-Aware Chunking
        try:
            chunks = chunk_document(
                doc_struct=doc_struct,
                target_tokens=self.config.chunking.target_tokens,
                min_tokens=self.config.chunking.min_tokens,
                max_tokens=self.config.chunking.max_tokens,
                overlap_tokens=self.config.chunking.overlap_tokens,
                tokenizer_dir=self.config.embedding.local_model_dir,
            )
        except Exception as e:
            if not dry_run:
                self.manifest.record_failure(doc_id, str(pdf_path), "chunking", str(e))
            raise

        chunk_count = len(chunks)

        if dry_run:
            return {
                "document_id": doc_id,
                "pages": page_count,
                "paragraphs": par_count,
                "sentences": sen_count,
                "chunks": chunk_count,
                "status": "DRY_RUN_SUCCESS",
            }

        # Stage 4: Dense Embedding Generation (BGE-M3 1024-d only)
        try:
            embedder = self._get_embed_engine()
            chunk_texts = [c.text for c in chunks]
            dense_vectors = embedder.encode_dense_batch(chunk_texts)
        except Exception as e:
            self.manifest.record_failure(doc_id, str(pdf_path), "embedding", str(e))
            raise

        # Stage 5: Qdrant Upload (Dense vectors only)
        try:
            self.qdrant_store.upsert_chunks(
                chunks=chunks,
                dense_vectors=dense_vectors,
            )
        except Exception as e:
            self.manifest.record_failure(doc_id, str(pdf_path), "qdrant_upsert", str(e))
            raise

        # Stage 6: Accumulate chunks into BM25 Store
        self.bm25_store.add_chunks(chunks)

        # Stage 7: Manifest Record
        self.manifest.record_success(
            document_id=doc_id,
            source_file=str(pdf_path),
            page_count=page_count,
            paragraph_count=par_count,
            sentence_count=sen_count,
            chunk_count=chunk_count,
            bm25_indexed=True,
        )

        return {
            "document_id": doc_id,
            "pages": page_count,
            "paragraphs": par_count,
            "sentences": sen_count,
            "chunks": chunk_count,
            "status": "SUCCESS",
        }

    def run_full(self, limit: Optional[int] = None):
        """Execute full production ingestion across corpus."""
        df = self.load_corpus_catalog()
        total = len(df) if limit is None else min(limit, len(df))
        logger.info(f"Initiating ingestion pipeline for {total} documents...")

        # Ensure collection exists before uploading
        self.qdrant_store.ensure_collection()

        success_count = 0
        skipped_count = 0
        failed_count = 0

        for idx, row in tqdm(df.head(total).iterrows(), total=total, desc="Ingesting Documents"):
            doc_id = str(row["document_id"])

            if self.manifest.is_completed(doc_id):
                skipped_count += 1
                continue

            try:
                self.process_single_document(row.to_dict(), dry_run=False)
                success_count += 1
                logger.info(f"Document {doc_id} processed successfully.")
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed processing document {doc_id}: {e}")

        # Build and persist finalized corpus-level BM25 index across all ingested chunks
        if self.bm25_store.mapping_records:
            logger.info("Building corpus-level BM25 index across all ingested chunks...")
            self.bm25_store.build_index()
            self.bm25_store.save()
            logger.info(f"Corpus-level BM25 index persisted to {self.config.bm25.index_dir}.")

        logger.info(f"Ingestion finished: {success_count} succeeded, {skipped_count} skipped, {failed_count} failed.")
