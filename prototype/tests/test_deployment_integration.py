"""
Vidhik Deployment Integration Test Suite
========================================
Comprehensive verification covering:
1. Laptop AI Gateway (/health, /api/embed, auth protection, input validation).
2. Render Retrieval API startup (zero eager BGE-M3 model loading, within 512MB RAM tier).
3. BM25 Lexical Retrieval with existing 29,156-chunk mapping.
4. BGE-M3 1024-d Embedding validation (dimension, numeric validity, L2 normalization).
5. Hybrid Retrieval with Reciprocal Rank Fusion (k=60) and Qdrant Cloud.
6. Graceful degradation to BM25-only when laptop gateway is unreachable.
7. Explicit degraded indicators ('bm25_degraded', 'embedding_gateway_unavailable').
8. IndicTrans2 entity protection & restoration in legal translation.
9. Secret isolation (no gateway token leakage in responses).
"""

import sys
import os
import math
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure prototype root is in PYTHONPATH
PROTOTYPE_ROOT = Path(__file__).resolve().parent.parent
if str(PROTOTYPE_ROOT) not in sys.path:
    sys.path.insert(0, str(PROTOTYPE_ROOT))

from fastapi.testclient import TestClient

# Import modules to test
from scripts.laptop_ai_gateway import app as gateway_app, get_embedding_engine
from retrieval.dense import DenseRetriever, GatewayEmbeddingUnavailableError
from retrieval.bm25 import BM25Retriever
from retrieval.models import RetrievalResult, HybridRetrievalResult
from retrieval.fusion import reciprocal_rank_fusion
from retrieval.engine import HybridRetrievalEngine
from translation.entity_protector import LegalEntityProtector
from translation.pipeline import LegalTranslationPipeline


class TestLaptopAIGateway(unittest.TestCase):
    """Unit and functional tests for the Laptop AI Gateway."""

    def setUp(self):
        self.test_token = "vidhik-test-secret-token"
        gateway_app.state.gateway_token = self.test_token
        self.client = TestClient(gateway_app)

    def test_01_health_endpoint_public(self):
        """GET /health must be accessible unauthenticated and report individual upstream readiness."""
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("status", data)
        self.assertIn("embedding", data)
        self.assertIn("ollama", data)
        self.assertIn("indictrans2", data)
        self.assertTrue(data["auth_required"])
        self.assertEqual(data["embedding"]["dimension"], 1024)
        self.assertEqual(data["embedding"]["model"], "BAAI/bge-m3")

    def test_02_auth_rejection_missing_token(self):
        """Protected endpoints must reject requests with missing token (HTTP 401)."""
        res = self.client.post("/api/embed", json={"text": "test query"})
        self.assertEqual(res.status_code, 401)
        data = res.json()
        self.assertEqual(data.get("detail", {}).get("error"), "UNAUTHORIZED")

    def test_03_auth_rejection_invalid_token(self):
        """Protected endpoints must reject invalid token (HTTP 401)."""
        res = self.client.post(
            "/api/embed",
            headers={"Authorization": "Bearer wrong-token"},
            json={"text": "test query"},
        )
        self.assertEqual(res.status_code, 401)

    def test_04_auth_acceptance_bearer_and_custom_header(self):
        """Protected endpoints must accept valid Bearer or x-gateway-token header."""
        # 1. Bearer header
        res1 = self.client.post(
            "/api/embed",
            headers={"Authorization": f"Bearer {self.test_token}"},
            json={"text": "arbitration section 34 limitation"},
        )
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1.json().get("dimension"), 1024)

        # 2. x-gateway-token header
        res2 = self.client.post(
            "/api/embed",
            headers={"x-gateway-token": self.test_token},
            json={"text": "bail under section 438"},
        )
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json().get("dimension"), 1024)

    def test_05_embed_input_validation(self):
        """POST /api/embed must validate input schemas and character limits."""
        headers = {"Authorization": f"Bearer {self.test_token}"}

        # Empty body
        r_empty = self.client.post("/api/embed", headers=headers, json={})
        self.assertEqual(r_empty.status_code, 400)

        # Whitespace text
        r_ws = self.client.post("/api/embed", headers=headers, json={"text": "   "})
        self.assertEqual(r_ws.status_code, 400)

        # Batch too large (> 32)
        r_large_batch = self.client.post("/api/embed", headers=headers, json={"texts": ["query"] * 35})
        self.assertEqual(r_large_batch.status_code, 400)

    def test_06_embedding_vector_dimensions_and_numeric_validity(self):
        """Returned embedding vector must have strictly 1024 finite float values."""
        headers = {"Authorization": f"Bearer {self.test_token}"}
        res = self.client.post(
            "/api/embed",
            headers=headers,
            json={"text": "Supreme Court of India limitation period Article 116"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        vec = data["embedding"]
        self.assertEqual(len(vec), 1024)
        self.assertTrue(all(isinstance(x, float) and not math.isnan(x) and not math.isinf(x) for x in vec))

        # Check L2 normalization (norm should be ~1.0)
        norm = math.sqrt(sum(x * x for x in vec))
        self.assertAlmostEqual(norm, 1.0, places=3)

    def test_07_batch_embedding_endpoint(self):
        """POST /api/embed must support batch 'texts' input."""
        headers = {"Authorization": f"Bearer {self.test_token}"}
        queries = ["query 1 legal issue", "query 2 arbitration clause", "query 3 court decree"]
        res = self.client.post(
            "/api/embed",
            headers=headers,
            json={"texts": queries},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["count"], 3)
        self.assertEqual(len(data["embeddings"]), 3)
        for emb in data["embeddings"]:
            self.assertEqual(len(emb), 1024)


class TestRenderRetrievalAPI(unittest.TestCase):
    """Tests verifying Render retrieval service and degraded mode operation."""

    def test_08_render_startup_no_eager_bge_m3_loading(self):
        """Verifies that retrieval_daemon can be imported without loading BGE-M3 into memory."""
        import scripts.retrieval_daemon as rd
        # Ensure that local embed engine was NOT eagerly loaded at module level
        self.assertIsNone(rd._local_embed_engine)
        self.assertTrue(rd.RETRIEVER.is_loaded)
        self.assertEqual(rd.RETRIEVER.corpus_size, 29156)

    def test_09_bm25_lexical_retrieval(self):
        """BM25 search returns relevant legal documents from the 29,156 chunk corpus."""
        retriever = BM25Retriever()
        results = retriever.search(query="limitation for filing an appeal under section 34", top_k=5)
        self.assertGreater(len(results), 0)
        for hit in results:
            self.assertTrue(hit.chunk_id)
            self.assertTrue(hit.document_id)
            self.assertTrue(hit.text)
            self.assertGreater(hit.score, 0.0)

    def test_10_dense_retriever_gateway_client(self):
        """DenseRetriever uses remote gateway when configured without local model."""
        retriever = DenseRetriever(
            gateway_url="http://mock-gateway:8010",
            gateway_token="mock-token",
            remote_mode=True,
            embed_engine=None,
        )
        self.assertTrue(retriever.remote_mode)
        self.assertIsNone(retriever.embed_engine)

        # Mock gateway HTTP response
        mock_vec = [0.03125] * 1024
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"embedding": mock_vec, "dimension": 1024}

        with patch("httpx.Client.post", return_value=mock_resp) as mock_post:
            vec = retriever.encode_query("statutory limitation period")
            self.assertEqual(len(vec), 1024)
            self.assertEqual(vec, mock_vec)
            mock_post.assert_called_once()

    def test_11_dense_retriever_gateway_unreachable_exception(self):
        """DenseRetriever raises GatewayEmbeddingUnavailableError when gateway is unreachable."""
        retriever = DenseRetriever(
            gateway_url="http://127.0.0.1:59999",
            gateway_token="mock-token",
            remote_mode=True,
            embed_engine=None,
        )
        with self.assertRaises(GatewayEmbeddingUnavailableError):
            retriever.encode_query("test legal query")

    def test_12_retrieval_daemon_degraded_bm25_mode(self):
        """Retrieval daemon gracefully falls back to BM25-only when gateway is unavailable."""
        import scripts.retrieval_daemon as rd
        handler = rd.FastRetrievalHandler.__new__(rd.FastRetrievalHandler)

        # Force gateway unavailable simulation
        with patch.object(rd, "AI_GATEWAY_URL", "http://127.0.0.1:59999"):
            with patch.object(rd, "EMBEDDING_MODE", "gateway"):
                res = handler.execute_hybrid_search("limitation period for filing appeal", top_k=3)
                self.assertEqual(res["retrieval_mode"], "bm25_degraded")
                self.assertTrue(res["degraded"])
                self.assertEqual(res["degraded_reason"], "embedding_gateway_unavailable")
                self.assertGreater(len(res["results"]), 0)
                for item in res["results"]:
                    self.assertIn("evidence_id", item)
                    self.assertIn("text", item)
                    self.assertIn("case_title", item)

    def test_13_rrf_fusion_ranking_and_provenance(self):
        """Reciprocal rank fusion fuses dense and BM25 candidate lists preserving provenance."""
        dense_hits = [
            RetrievalResult(
                chunk_id="chunk_1",
                document_id="DOC_A",
                score=0.88,
                retrieval_method="dense",
                text="Text of chunk 1",
                qdrant_point_id="pt_1",
                rank=1,
                metadata={"court": "Supreme Court of India", "case_title": "Case A"},
            ),
            RetrievalResult(
                chunk_id="chunk_2",
                document_id="DOC_B",
                score=0.75,
                retrieval_method="dense",
                text="Text of chunk 2",
                qdrant_point_id="pt_2",
                rank=2,
                metadata={"court": "Delhi High Court", "case_title": "Case B"},
            ),
        ]
        bm25_hits = [
            RetrievalResult(
                chunk_id="chunk_2",
                document_id="DOC_B",
                score=14.2,
                retrieval_method="bm25",
                text="Text of chunk 2",
                qdrant_point_id="pt_2",
                rank=1,
            ),
            RetrievalResult(
                chunk_id="chunk_3",
                document_id="DOC_C",
                score=11.1,
                retrieval_method="bm25",
                text="Text of chunk 3",
                qdrant_point_id="pt_3",
                rank=2,
            ),
        ]

        fused = reciprocal_rank_fusion(dense_hits, bm25_hits, k=60, top_k=3)
        self.assertEqual(len(fused), 3)

        # chunk_2 appeared in both dense rank 2 and BM25 rank 1 -> should have highest RRF score
        self.assertEqual(fused[0].chunk_id, "chunk_2")
        self.assertAlmostEqual(
            fused[0].rrf_score,
            (1.0 / (60 + 2)) + (1.0 / (60 + 1)),
            places=5,
        )


class TestTranslationAndEntityPreservation(unittest.TestCase):
    """Tests verifying IndicTrans2 entity protection and translation contracts."""

    def test_14_legal_entity_protection(self):
        """Verifies that citations, statutes, and case names are protected with placeholders."""
        protector = LegalEntityProtector()
        legal_text = (
            "In Supreme Court of India in 2021 INSC 194, under Section 34 of the Arbitration and Conciliation Act, 1996, "
            "the limitation period is 90 days."
        )
        protected_text, registry = protector.protect(legal_text, "ta")
        self.assertGreater(len(registry), 0)

        # Placeholders must be present
        self.assertTrue(any("⟦" in protected_text or "§" in protected_text or "ENT_" in str(registry) for _ in [1]))

        # Exact restoration
        restored_text, audit, unresolved = protector.restore(protected_text, registry)
        self.assertEqual(unresolved, [])
        self.assertIn("Section 34", restored_text)
        self.assertIn("2021 INSC 194", restored_text)
        self.assertIn("Arbitration and Conciliation Act, 1996", restored_text)


class TestSecretIsolation(unittest.TestCase):
    """Tests ensuring gateway secrets and tokens are never leaked to client bundles or public endpoints."""

    def test_15_public_health_does_not_leak_token(self):
        """Gateway /health reports auth_required bool, never the raw token string."""
        gateway_app.state.gateway_token = "super-secret-production-token-12345"
        client = TestClient(gateway_app)
        res = client.get("/health")
        self.assertEqual(res.status_code, 200)
        body_text = res.text
        self.assertNotIn("super-secret-production-token-12345", body_text)
        self.assertTrue(res.json()["auth_required"])

    def test_16_retrieval_daemon_health_does_not_leak_qdrant_key(self):
        """Retrieval daemon /health reports qdrant_connected bool, never QDRANT_API_KEY."""
        import scripts.retrieval_daemon as rd
        handler = rd.FastRetrievalHandler.__new__(rd.FastRetrievalHandler)
        mock_wfile = MagicMock()
        written_data = []
        mock_wfile.write.side_effect = lambda b: written_data.append(b.decode("utf-8"))
        handler.wfile = mock_wfile
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.send_cors_headers = MagicMock()
        handler.end_headers = MagicMock()
        handler.path = "/health"

        handler.do_GET()
        full_output = "".join(written_data)
        self.assertIn('"status": "healthy"', full_output)
        self.assertNotIn(rd.QDRANT_API_KEY or "nonexistent", full_output if rd.QDRANT_API_KEY else '""')


if __name__ == "__main__":
    unittest.main()
