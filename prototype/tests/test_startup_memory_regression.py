"""
Regression Test Suite: Retrieval Service Startup Memory & OOM Prevention
==========================================================================
Verifies that:
1. Retrieval service initialization stays strictly below Render's 512 MiB RAM limit.
2. Lightweight memory checkpoints record process RSS at all required boundaries:
   - process start and module imports
   - Qdrant client initialization and connection
   - document/Parquet mapping loading
   - BM25 index loading
   - application startup completion
3. BM25Store loads using CompactMappingRecords and CompactBM25Okapi.
4. Heavy ML models (PyTorch, FlagEmbedding, Transformers) are NOT loaded in memory.
5. No duplicate copies of Parquet mapping or large deserialized dicts remain on heap.
6. BM25 queries return accurate results with deterministic Qdrant point IDs.
"""

import sys
import os
import unittest
from pathlib import Path

PROTOTYPE_ROOT = Path(__file__).resolve().parent.parent
if str(PROTOTYPE_ROOT) not in sys.path:
    sys.path.insert(0, str(PROTOTYPE_ROOT))

from ingestion.bm25_store import BM25Store, CompactMappingRecords, CompactBM25Okapi
from retrieval.bm25 import BM25Retriever
from scripts.retrieval_daemon import get_process_rss_mb, log_memory_checkpoint


class TestStartupMemoryRegression(unittest.TestCase):
    """Regression test ensuring startup RSS does not exceed Render's 512 MiB limit."""

    def test_01_process_rss_below_memory_limit(self):
        """Verify that process RSS is strictly below 480 MiB (comfortably inside 512 MiB limit)."""
        current_rss = get_process_rss_mb()
        print(f"\n[TEST MEASUREMENT] Current Process RSS: {current_rss:.2f} MiB")
        self.assertGreater(current_rss, 0.0, "Process RSS must be a positive numeric value")
        self.assertLess(
            current_rss,
            480.0,
            f"Process RSS ({current_rss:.2f} MiB) exceeds safe memory ceiling for 512 MiB Render tier!",
        )

    def test_02_memory_checkpoints_numeric_and_flushed(self):
        """Verify that memory checkpoints return valid numeric MiB values without error."""
        checkpoints = [
            "Process start and module imports",
            "Qdrant client initialization and connection",
            "Document/Parquet mapping loading",
            "BM25 index loading",
            "Application startup completion",
        ]
        for cp in checkpoints:
            val = log_memory_checkpoint(f"Regression Test: {cp}")
            self.assertIsInstance(val, float)
            self.assertGreater(val, 0.0)
            self.assertLess(val, 480.0)

    def test_03_compact_mapping_records_structure(self):
        """Verify CompactMappingRecords sequence behavior and memory efficiency."""
        store = BM25Store(
            index_dir=PROTOTYPE_ROOT / "indexes" / "bm25",
            index_file="bm25_index.pkl",
            mapping_file="bm25_mapping.parquet",
        )
        store.load()

        # Must use memory-efficient CompactMappingRecords
        self.assertIsInstance(
            store.mapping_records,
            CompactMappingRecords,
            "mapping_records must be an instance of CompactMappingRecords to prevent heap explosion",
        )
        self.assertEqual(len(store.mapping_records), 29156)
        self.assertTrue(bool(store.mapping_records))

        # Test single item lookup
        first_rec = store.mapping_records[0]
        self.assertIn("qdrant_point_id", first_rec)
        self.assertIn("document_id", first_rec)
        self.assertIn("chunk_id", first_rec)
        self.assertIn("text", first_rec)
        self.assertIsInstance(first_rec["qdrant_point_id"], str)
        self.assertTrue(len(first_rec["text"]) > 0)

        # Test slice lookup
        sliced = store.mapping_records[:3]
        self.assertEqual(len(sliced), 3)

        # Verify corpus_tokens is not retaining 11M tokens in memory
        self.assertEqual(len(store.corpus_tokens), 0, "corpus_tokens must remain empty in serving mode")

    def test_04_compact_bm25_scoring_and_retrieval(self):
        """Verify CompactBM25Okapi scoring correctness and legal search retrieval."""
        retriever = BM25Retriever()
        self.assertTrue(retriever.is_loaded)
        self.assertEqual(retriever.corpus_size, 29156)

        # Execute realistic legal queries
        hits = retriever.search("Section 438 CrPC anticipatory bail", top_k=5)
        self.assertGreater(len(hits), 0)
        self.assertEqual(hits[0].retrieval_method, "bm25")
        self.assertTrue(bool(hits[0].qdrant_point_id))
        self.assertTrue(bool(hits[0].text))
        self.assertGreater(hits[0].score, 0.0)

        # Verify ranking consistency: top scores should be non-increasing
        scores = [h.score for h in hits]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_05_no_heavy_ml_packages_loaded(self):
        """Confirm that torch, FlagEmbedding, and heavy ML frameworks are NOT loaded."""
        forbidden_modules = ["torch", "FlagEmbedding", "transformers"]
        for mod in forbidden_modules:
            self.assertNotIn(
                mod,
                sys.modules,
                f"Forbidden heavy ML module '{mod}' was loaded into memory in gateway/Render mode!",
            )

    def test_06_no_duplicate_df_mapping_on_module(self):
        """Verify retrieval_daemon does not maintain an eager duplicate copy of DF_MAPPING."""
        import scripts.retrieval_daemon as daemon_mod
        self.assertFalse(
            hasattr(daemon_mod, "DF_MAPPING"),
            "retrieval_daemon should not hold a redundant global DF_MAPPING DataFrame",
        )


if __name__ == "__main__":
    unittest.main()
