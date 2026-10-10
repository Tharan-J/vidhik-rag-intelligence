"""
Ingestion Manifest & Pipeline Resumability Subsystem
===================================================
Tracks processing status, document counts, and errors across all 1,361 documents.
Guarantees resumability: completed documents are never re-uploaded or lost on crash.
Stored as Parquet with synchronous CSV mirroring for inspection.
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd

logger = logging.getLogger("VidhikIngestion.Manifest")

MANIFEST_SCHEMA = [
    "document_id",
    "source_file",
    "status",  # 'pending', 'processing', 'success', 'failed'
    "page_count",
    "paragraph_count",
    "sentence_count",
    "chunk_count",
    "embedding_status",
    "qdrant_status",
    "bm25_index_status",
    "error",
    "processed_at",
]


class IngestionManifest:
    def __init__(self, parquet_path: Path, csv_path: Optional[Path] = None):
        self.parquet_path = Path(parquet_path)
        self.csv_path = Path(csv_path) if csv_path else self.parquet_path.with_suffix(".csv")
        self.parquet_path.parent.mkdir(parents=True, exist_ok=True)
        self.records: Dict[str, Dict[str, Any]] = {}
        self.load()

    def load(self):
        """Load manifest from disk if it exists."""
        if self.parquet_path.exists():
            try:
                df = pd.read_parquet(self.parquet_path)
                for _, row in df.iterrows():
                    d = row.to_dict()
                    self.records[str(d["document_id"])] = d
                logger.info(f"Loaded existing manifest with {len(self.records)} records from {self.parquet_path.name}")
            except Exception as e:
                logger.warning(f"Could not read existing parquet manifest: {e}")

    def save(self):
        """Persist manifest atomically to Parquet and CSV."""
        if not self.records:
            return

        df = pd.DataFrame(list(self.records.values()))
        # Ensure all columns exist
        for col in MANIFEST_SCHEMA:
            if col not in df.columns:
                df[col] = None
        df = df[MANIFEST_SCHEMA]

        # Write Parquet atomically
        tmp_parquet = self.parquet_path.with_suffix(".tmp.parquet")
        df.to_parquet(tmp_parquet, index=False)
        tmp_parquet.replace(self.parquet_path)

        # Write CSV mirror
        try:
            df.to_csv(self.csv_path, index=False)
        except Exception as e:
            logger.debug(f"CSV mirror write failed: {e}")

    def is_completed(self, document_id: str) -> bool:
        """Check if document has already succeeded in a prior run."""
        rec = self.records.get(str(document_id))
        return bool(rec and rec.get("status") == "success" and rec.get("qdrant_status") == "success")

    def record_start(self, document_id: str, source_file: str):
        """Mark document as processing."""
        self.records[str(document_id)] = {
            "document_id": str(document_id),
            "source_file": str(source_file),
            "status": "processing",
            "page_count": 0,
            "paragraph_count": 0,
            "sentence_count": 0,
            "chunk_count": 0,
            "embedding_status": "pending",
            "qdrant_status": "pending",
            "bm25_index_status": "pending",
            "error": None,
            "processed_at": datetime.utcnow().isoformat(),
        }

    def record_success(
        self,
        document_id: str,
        source_file: str,
        page_count: int,
        paragraph_count: int,
        sentence_count: int,
        chunk_count: int,
        bm25_indexed: bool = True,
    ):
        """Mark document as successfully ingested."""
        self.records[str(document_id)] = {
            "document_id": str(document_id),
            "source_file": str(source_file),
            "status": "success",
            "page_count": page_count,
            "paragraph_count": paragraph_count,
            "sentence_count": sentence_count,
            "chunk_count": chunk_count,
            "embedding_status": "success",
            "qdrant_status": "success",
            "bm25_index_status": "indexed" if bm25_indexed else "pending",
            "error": None,
            "processed_at": datetime.utcnow().isoformat(),
        }
        self.save()

    def record_failure(
        self,
        document_id: str,
        source_file: str,
        stage: str,
        error_msg: str,
    ):
        """Record document failure and error trace."""
        self.records[str(document_id)] = {
            "document_id": str(document_id),
            "source_file": str(source_file),
            "status": "failed",
            "page_count": 0,
            "paragraph_count": 0,
            "sentence_count": 0,
            "chunk_count": 0,
            "embedding_status": f"failed_at_{stage}",
            "qdrant_status": "failed",
            "bm25_index_status": "failed",
            "error": f"[{stage}] {error_msg}",
            "processed_at": datetime.utcnow().isoformat(),
        }
        self.save()

    def summary(self) -> Dict[str, Any]:
        """Return summary statistics of manifest records."""
        total = len(self.records)
        statuses = {}
        for r in self.records.values():
            s = r.get("status", "unknown")
            statuses[s] = statuses.get(s, 0) + 1
        return {
            "total_tracked": total,
            "by_status": statuses,
            "completed_count": statuses.get("success", 0),
            "failed_count": statuses.get("failed", 0),
        }
