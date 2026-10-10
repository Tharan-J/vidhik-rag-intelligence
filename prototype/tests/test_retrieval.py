"""
Automated Verification Suite for Vidhik Hybrid Retrieval Engine
================================================================
Test 1: BM25 index and mapping file loading (27,864 chunks).
Test 2: BGE-M3 dense query embedding generation (1024-d normalized vector).
Test 3: Qdrant Cloud dense vector query execution (collection: vidhik_legal_chunks).
Test 4: Reciprocal Rank Fusion (RRF with k=60) mathematical correctness.
Test 5: End-to-end hybrid retrieval with complete provenance preservation.
"""

import sys
import unittest
from pathlib import Path
import numpy as np

# Ensure prototype root is in PYTHONPATH
PROTOTYPE_DIR = Path(__file__).resolve().parent.parent
if str(PROTOTYPE_DIR) not in sys.path:
    sys.path.insert(0, str(PROTOTYPE_DIR))

from retrieval.config import load_retrieval_config
from retrieval.models import RetrievalResult, HybridRetrievalResult
from retrieval.dense import DenseRetriever
from retrieval.bm25 import BM25Retriever
from retrieval.fusion import reciprocal_rank_fusion
from retrieval.engine import HybridRetrievalEngine


class TestVidhikRetrievalEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_retrieval_config()

    def test_01_bm25_loading(self):
        """Test 1: Verify persistent BM25 index and mapping load successfully with 29,156 entries."""
        bm25_retriever = BM25Retriever(config=self.config.bm25)
        self.assertTrue(bm25_retriever.is_loaded, "BM25 index should be loaded")
        self.assertEqual(
            bm25_retriever.corpus_size,
            29156,
            f"Expected exactly 29,156 chunks in BM25 mapping, got {bm25_retriever.corpus_size}",
        )
        
        # Test basic keyword retrieval
        hits = bm25_retriever.search("Section 438 CrPC", top_k=5)
        self.assertGreater(len(hits), 0, "BM25 should return hits for legal section query")
        self.assertIsInstance(hits[0], RetrievalResult)
        self.assertEqual(hits[0].retrieval_method, "bm25")
        self.assertTrue(hits[0].qdrant_point_id, "BM25 hits must resolve to deterministic Qdrant point IDs")

    def test_02_dense_query_embedding(self):
        """Test 2: Verify BGE-M3 generates 1024-dimensional normalized dense vectors."""
        dense_retriever = DenseRetriever(
            config=self.config.dense,
            embedding_config=self.config.embedding,
        )
        query = "What is the limitation period for filing an appeal?"
        vec = dense_retriever.encode_query(query)
        
        self.assertEqual(len(vec), 1024, f"Expected 1024 dimensions, got {len(vec)}")
        norm = sum(x * x for x in vec) ** 0.5
        self.assertAlmostEqual(norm, 1.0, places=4, msg="Dense vector should be L2 normalized")

    def test_03_qdrant_retrieval(self):
        """Test 3: Verify Qdrant Cloud dense query execution on 'vidhik_legal_chunks'."""
        dense_retriever = DenseRetriever(
            config=self.config.dense,
            embedding_config=self.config.embedding,
        )
        # Health check on collection
        conn = dense_retriever.verify_connection()
        self.assertEqual(conn["status"], "connected")
        self.assertEqual(conn["collection"], "vidhik_legal_chunks")
        self.assertGreater(conn["points_count"], 0)

        # Execute dense search
        results = dense_retriever.search(
            query="limitation period appeal High Court",
            top_k=5,
        )
        self.assertGreater(len(results), 0, "Dense retriever should return points")
        self.assertIsInstance(results[0], RetrievalResult)
        self.assertEqual(results[0].retrieval_method, "dense")
        self.assertTrue(results[0].text, "Dense hit must include chunk text")
        self.assertTrue(results[0].document_id, "Dense hit must include document_id")
        self.assertIn("court_level", results[0].metadata, "Dense hit payload must include court_level")

    def test_04_reciprocal_rank_fusion(self):
        """Test 4: Verify deterministic RRF fusion calculation with k=60."""
        # Candidate A: dense rank 1, bm25 rank 2
        # Candidate B: dense rank 2, not in bm25
        # Candidate C: not in dense, bm25 rank 1
        dense_hits = [
            RetrievalResult(
                chunk_id="chunk_01",
                document_id="doc_A",
                qdrant_point_id="pt_A",
                score=0.90,
                retrieval_method="dense",
                text="Text A",
                rank=1,
            ),
            RetrievalResult(
                chunk_id="chunk_02",
                document_id="doc_B",
                qdrant_point_id="pt_B",
                score=0.85,
                retrieval_method="dense",
                text="Text B",
                rank=2,
            ),
        ]
        bm25_hits = [
            RetrievalResult(
                chunk_id="chunk_03",
                document_id="doc_C",
                qdrant_point_id="pt_C",
                score=18.5,
                retrieval_method="bm25",
                text="Text C",
                rank=1,
            ),
            RetrievalResult(
                chunk_id="chunk_01",
                document_id="doc_A",
                qdrant_point_id="pt_A",
                score=15.2,
                retrieval_method="bm25",
                text="Text A",
                rank=2,
            ),
        ]

        fused = reciprocal_rank_fusion(dense_hits, bm25_hits, k=60, top_k=3)
        self.assertEqual(len(fused), 3)

        # Expected RRF scores:
        # A: 1/(60+1) + 1/(60+2) = 1/61 + 1/62 ≈ 0.03252248
        # C: 1/(60+1) = 1/61 ≈ 0.01639344
        # B: 1/(60+2) = 1/62 ≈ 0.01612903
        expected_score_A = (1.0 / 61.0) + (1.0 / 62.0)
        expected_score_C = 1.0 / 61.0
        expected_score_B = 1.0 / 62.0

        self.assertEqual(fused[0].qdrant_point_id, "pt_A")
        self.assertAlmostEqual(fused[0].rrf_score, expected_score_A, places=6)
        self.assertEqual(fused[0].rrf_rank, 1)
        self.assertEqual(fused[0].dense_rank, 1)
        self.assertEqual(fused[0].bm25_rank, 2)

        self.assertEqual(fused[1].qdrant_point_id, "pt_C")
        self.assertAlmostEqual(fused[1].rrf_score, expected_score_C, places=6)
        self.assertEqual(fused[1].rrf_rank, 2)
        self.assertIsNone(fused[1].dense_rank)
        self.assertEqual(fused[1].bm25_rank, 1)

        self.assertEqual(fused[2].qdrant_point_id, "pt_B")
        self.assertAlmostEqual(fused[2].rrf_score, expected_score_B, places=6)
        self.assertEqual(fused[2].rrf_rank, 3)
        self.assertEqual(fused[2].dense_rank, 2)
        self.assertIsNone(fused[2].bm25_rank)

    def test_05_end_to_end_retrieval_provenance(self):
        """Test 5: Verify full hybrid pipeline (Query -> Dense + BM25 -> RRF) with complete provenance."""
        engine = HybridRetrievalEngine()
        query = "What is the limitation period for filing an appeal?"
        results = engine.search(query=query, top_k=5, dense_top_k=10, bm25_top_k=10)

        self.assertGreater(len(results), 0, "Engine must return results")
        for res in results:
            self.assertIsInstance(res, HybridRetrievalResult)
            # Provenance requirements
            self.assertTrue(res.chunk_id, "Must have chunk_id")
            self.assertTrue(res.document_id, "Must have document_id")
            self.assertTrue(res.qdrant_point_id, "Must have qdrant_point_id")
            self.assertTrue(res.text, "Must have text")
            self.assertTrue(res.court_level, "Must have court_level")
            self.assertTrue(res.court, "Must have court")
            self.assertTrue(res.case_title, "Must have case_title")
            self.assertGreaterEqual(res.page_start, 1, "Must have valid page_start")
            self.assertGreaterEqual(res.page_end, res.page_start, "Must have valid page_end")
            self.assertTrue(res.paragraph_start, "Must have valid paragraph_start")
            self.assertGreater(res.rrf_score, 0.0, "Must have positive RRF score")
            self.assertGreaterEqual(res.rrf_rank, 1, "Must have valid RRF rank")
            self.assertIsInstance(res.metadata, dict, "Must have metadata dict")


if __name__ == "__main__":
    unittest.main()
