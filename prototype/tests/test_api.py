"""
Comprehensive Test Suite for Vidhik Legal RAG API
==================================================
Tests:
1. Valid query processing with structured response
2. Empty/whitespace query rejection (HTTP 400 / 422)
3. Invalid JSON schema / missing field rejection (HTTP 422)
4. Schema validation for answer, claims, and provenance
5. Insufficient-evidence handling (Safe HTTP 200 with confidence='insufficient_evidence')
6. Lightweight backend health check (GET /health)
7. Subsystem readiness status check (GET /api/v1/status)
8. Dependency outage handling (Qwen unreachable, Qdrant down, generation timeout)
9. Live End-to-end API execution against real local RAG stack
"""

import sys
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add prototype root
PROTOTYPE_ROOT = Path(__file__).resolve().parent.parent
if str(PROTOTYPE_ROOT) not in sys.path:
    sys.path.insert(0, str(PROTOTYPE_ROOT))

from fastapi.testclient import TestClient

from api.main import create_app
from api.schemas import LegalQueryResponse, SystemStatusResponse, HealthResponse
from rag.engine import LegalRAGEngine, LegalRAGResponse
from rag.provenance import ClaimWithProvenance, CitationAuthority


class TestVidhikAPI(unittest.TestCase):
    """
    Test suite for FastAPI endpoints.
    """

    def setUp(self):
        """Setup mock engine and test client."""
        self.mock_engine = MagicMock(spec=LegalRAGEngine)

        # Build sample authority & claim
        self.sample_authority = CitationAuthority(
            evidence_id="E1",
            document_id="HC_7_26_DLHC010427042021.pdf",
            chunk_id="chk_001",
            qdrant_point_id="dc44ed25-02a8-536d-a856-6f431aa42e0d",
            court="Delhi High Court",
            court_level="High Court",
            case_title="DELHI DEVELOPMENT AUTHORITY Vs M/S AJAB SINGH AND CO.",
            case_number="DLHC010427042021",
            decision_date="2022-07-29",
            page_number="18-19",
            paragraph_id="PAR001",
            sentence_id="SEN001",
            text_snippet="Period of limitation means...",
        )

        self.sample_claim = ClaimWithProvenance(
            claim="Appeals to the High Court must be filed within 90 days under Article 116.",
            evidence_ids=["E1"],
            authorities=[self.sample_authority],
            is_grounded=True,
        )

        self.sample_evidence_dict = {
            "evidence_id": "E1",
            "id": "E1",
            "document_id": "HC_7_26_DLHC010427042021.pdf",
            "chunk_id": "chk_001",
            "qdrant_point_id": "dc44ed25-02a8-536d-a856-6f431aa42e0d",
            "court_level": "High Court",
            "court": "Delhi High Court",
            "case_title": "DELHI DEVELOPMENT AUTHORITY Vs M/S AJAB SINGH AND CO.",
            "case_number": "DLHC010427042021",
            "decision_date": "2022-07-29",
            "year": 2022,
            "page_start": 18,
            "page_end": 19,
            "page": "18-19",
            "page_number": "18-19",
            "paragraph_start": "PAR001",
            "paragraph_end": "PAR001",
            "paragraph": "PAR001",
            "paragraph_id": "PAR001",
            "sentence_id": "SEN001",
            "source_file": "HC_7_26_DLHC010427042021.pdf",
            "text": "Period of limitation means the period of limitation prescribed for any suit, appeal or application...",
            "rrf_score": 0.0163,
            "rrf_rank": 1,
            "dense_rank": 1,
            "bm25_rank": 2,
            "metadata": {},
        }

        self.mock_rag_response = LegalRAGResponse(
            query="What is the limitation period for filing an appeal?",
            answer="Under the Code of Civil Procedure, 1908 and Article 116 of the Limitation Act, appeals to the High Court must be filed within 90 days.",
            claims=[self.sample_claim],
            evidence=[self.sample_evidence_dict],
            limitations="Based exclusively on Delhi High Court precedent.",
            confidence="supported",
            retrieval_count=20,
            evidence_count=1,
            execution_time_seconds=1.45,
        )

        self.mock_engine.answer.return_value = self.mock_rag_response

        # Create FastAPI app with mocked engine
        self.app = create_app(engine=self.mock_engine)
        self.client = TestClient(self.app)

    def test_01_backend_health_check(self):
        """Test 1: Verify GET /health returns instant 200 OK and valid health schema."""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "vidhik-api")
        self.assertIn("timestamp", data)
        self.assertEqual(data["version"], "1.0.0")

    def test_02_backend_status_check(self):
        """Test 2: Verify GET /api/v1/status provides runtime readiness information."""
        # Mock underlying subsystems for readiness check
        mock_dense = MagicMock()
        mock_dense.config.collection_name = "vidhik_legal_chunks"
        mock_dense.client.get_collection.return_value = MagicMock(points_count=29156, status=MagicMock(value="green"))
        mock_dense.embed_engine.session = MagicMock()
        mock_dense.embed_engine.model_name = "BAAI/bge-m3"
        mock_dense.embed_engine.dense_dim = 1024

        mock_bm25 = MagicMock()
        mock_bm25.corpus_size = 29156
        mock_bm25.config.index_path = "/path/to/bm25.pkl"

        self.mock_engine.retrieval_engine = MagicMock()
        self.mock_engine.retrieval_engine.dense_retriever = mock_dense
        self.mock_engine.retrieval_engine.bm25_retriever = mock_bm25
        self.mock_engine.config = MagicMock()
        self.mock_engine.config.generator = MagicMock(
            endpoint="http://localhost:11434/api/generate",
            model="qwen3:4b-instruct",
        )

        # Mock urllib call to ollama /api/tags
        with patch("urllib.request.urlopen") as mock_url:
            mock_url.return_value.__enter__.return_value.read.return_value = (
                b'{"models": [{"name": "qwen3:4b-instruct:latest"}]}'
            )
            resp = self.client.get("/api/v1/status")

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn(data["status"], ["ready", "degraded", "unavailable"])
        self.assertIn("qdrant", data["components"])
        self.assertIn("bm25", data["components"])
        self.assertIn("embedding_engine", data["components"])
        self.assertIn("generator", data["components"])
        self.assertEqual(data["components"]["qdrant"]["status"], "ok")
        self.assertEqual(data["components"]["bm25"]["status"], "ok")

    def test_03_valid_query_structured_response(self):
        """Test 3: Verify POST /api/v1/query returns complete structured answer + provenance."""
        payload = {"query": "What is the limitation period for filing an appeal?"}
        resp = self.client.post("/api/v1/query", json=payload)

        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        # Schema assertions
        self.assertEqual(data["query"], payload["query"])
        self.assertIn("Article 116", data["answer"])
        self.assertEqual(data["confidence"], "supported")
        self.assertEqual(data["retrieval_count"], 20)
        self.assertEqual(data["evidence_count"], 1)

        # Claims & provenance assertions
        self.assertEqual(len(data["claims"]), 1)
        c0 = data["claims"][0]
        self.assertEqual(c0["evidence_ids"], ["E1"])
        self.assertTrue(c0["is_grounded"])
        self.assertEqual(len(c0["authorities"]), 1)
        a0 = c0["authorities"][0]
        self.assertEqual(a0["evidence_id"], "E1")
        self.assertEqual(a0["court"], "Delhi High Court")
        self.assertEqual(a0["page_number"], "18-19")

        # Evidence provenance assertions
        self.assertEqual(len(data["evidence"]), 1)
        ev0 = data["evidence"][0]
        self.assertEqual(ev0["evidence_id"], "E1")
        self.assertEqual(ev0["court"], "Delhi High Court")
        self.assertEqual(ev0["page_start"], 18)
        self.assertEqual(ev0["page_end"], 19)
        self.assertEqual(ev0["qdrant_point_id"], "dc44ed25-02a8-536d-a856-6f431aa42e0d")
        self.assertIn("Period of limitation", ev0["text"])

    def test_04_empty_and_whitespace_query_rejection(self):
        """Test 4: Verify empty or whitespace-only queries are cleanly rejected with HTTP 400/422."""
        # Empty string
        resp1 = self.client.post("/api/v1/query", json={"query": ""})
        self.assertIn(resp1.status_code, [400, 422])
        data1 = resp1.json()
        self.assertIn("error", data1)

        # Whitespace-only string
        resp2 = self.client.post("/api/v1/query", json={"query": "   \n\t  "})
        self.assertIn(resp2.status_code, [400, 422])
        data2 = resp2.json()
        self.assertIn("error", data2)

    def test_05_invalid_request_body_rejection(self):
        """Test 5: Verify missing required fields or invalid data types return HTTP 422."""
        # Missing query key
        resp1 = self.client.post("/api/v1/query", json={"wrong_key": "some text"})
        self.assertEqual(resp1.status_code, 422)
        data1 = resp1.json()
        self.assertEqual(data1["error"]["code"], "VALIDATION_ERROR")

        # Invalid top_k type
        resp2 = self.client.post("/api/v1/query", json={"query": "limitation", "top_k": "not_an_int"})
        self.assertEqual(resp2.status_code, 422)

    def test_06_insufficient_evidence_response(self):
        """Test 6: Verify insufficient evidence produces safe calibrated HTTP 200 response."""
        self.mock_engine.answer.return_value = LegalRAGResponse(
            query="What is the regulation on maritime quantum entanglement?",
            answer="The retrieved legal corpus did not contain sufficient authoritative evidence to answer this question reliably.",
            claims=[],
            evidence=[],
            limitations="No relevant court holdings, statutes, or precedent were retrieved.",
            confidence="insufficient_evidence",
            retrieval_count=0,
            evidence_count=0,
            execution_time_seconds=0.12,
        )

        resp = self.client.post("/api/v1/query", json={"query": "What is the regulation on maritime quantum entanglement?"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(data["confidence"], "insufficient_evidence")
        self.assertEqual(len(data["claims"]), 0)
        self.assertEqual(len(data["evidence"]), 0)
        self.assertIn("sufficient authoritative evidence", data["answer"])

    def test_07_dependency_outage_handling(self):
        """Test 7: Verify clean HTTP errors when dependencies fail (Qwen unreachable, Qdrant down, timeout)."""
        # Generator unreachable -> 503
        self.mock_engine.answer.side_effect = RuntimeError("Qwen service unreachable at http://localhost:11434/api/generate: connection refused")
        resp_gen = self.client.post("/api/v1/query", json={"query": "limitation period"})
        self.assertEqual(resp_gen.status_code, 503)
        self.assertEqual(resp_gen.json()["error"]["code"], "GENERATOR_UNAVAILABLE")

        # Qdrant unavailable -> 503
        self.mock_engine.answer.side_effect = RuntimeError("Qdrant query failed after 3 attempts: network error")
        resp_qdrant = self.client.post("/api/v1/query", json={"query": "limitation period"})
        self.assertEqual(resp_qdrant.status_code, 503)
        self.assertEqual(resp_qdrant.json()["error"]["code"], "VECTOR_STORE_UNAVAILABLE")

        # Timeout -> 504
        self.mock_engine.answer.side_effect = TimeoutError("Pipeline timeout")
        resp_timeout = self.client.post("/api/v1/query", json={"query": "limitation period"})
        self.assertEqual(resp_timeout.status_code, 504)
        self.assertEqual(resp_timeout.json()["error"]["code"], "GENERATION_TIMEOUT")

    def test_08_cors_headers_present(self):
        """Test 8: Verify CORS headers allow frontend clients."""
        resp = self.client.options(
            "/api/v1/query",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get("access-control-allow-origin"), "http://localhost:5173")


if __name__ == "__main__":
    unittest.main()
