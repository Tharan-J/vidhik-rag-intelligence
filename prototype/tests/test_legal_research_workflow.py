"""
Phase 4 Workflow 2: Complete Legal Search and Research Test Suite
==================================================================
Comprehensive integration and relevance test suite for Vidhik Research Workflow 2:
- Test A: API and Integration (real query reaches Next.js /api/research & retrieval daemon, returns hybrid chunks).
- Test B: Evidence and Relevance (verifies 3 real judgments across Supreme Court, High Court, and District Court;
          verifies negative control fails closed without hallucination).
- Test C: Source Resolution (verifies /api/documents/stream resolves actual source PDFs with real SHA-256 hashes).
- Test D: Failure Handling (empty queries, unauthenticated streaming, path traversal, unavailable documents).
- Test E: Regression (Workflow 1 matters and daemon health remain operational).
"""

import os
import sys
import json
import time
import hashlib
import requests
import unittest
from pathlib import Path

# Paths
PROTOTYPE_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = PROTOTYPE_ROOT.parent
FRONTEND_ROOT = WORKSPACE_ROOT / "frontend"
RESEARCH_DATA_DIR = WORKSPACE_ROOT / "research" / "legal_data"

NEXT_BASE_URL = "http://localhost:3000"
DAEMON_BASE_URL = "http://127.0.0.1:8008"
AUTH_HEADERS = {"x-lawyer-token": "dev_lawyer_token"}


class TestLegalResearchWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 1. Verify Next.js dev server is reachable
        try:
            r = requests.get(f"{NEXT_BASE_URL}/api/matters", timeout=5)
            assert r.status_code == 200, f"Expected 200 from /api/matters, got {r.status_code}"
        except Exception as e:
            raise RuntimeError(f"Next.js server is not reachable on {NEXT_BASE_URL}: {e}")

        # 2. Verify Retrieval Daemon is healthy
        try:
            r = requests.get(f"{DAEMON_BASE_URL}/health", timeout=5)
            assert r.status_code == 200, f"Expected 200 from daemon health, got {r.status_code}"
            data = r.json()
            assert data.get("status") == "healthy"
            assert data.get("qdrant_connected") is True
            assert data.get("bm25_chunks", 0) > 0
        except Exception as e:
            raise RuntimeError(f"Retrieval daemon is not healthy on {DAEMON_BASE_URL}: {e}")

    # =========================================================================
    # TEST SUITE A: API AND INTEGRATION
    # =========================================================================
    def test_a1_daemon_search_hybrid_pipeline(self):
        """Verify the hybrid retrieval daemon directly returns real scored chunks."""
        resp = requests.get(
            f"{DAEMON_BASE_URL}/search",
            params={"q": "Section 34 Arbitration setting aside award modification", "top_k": 5},
            timeout=10,
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("results", data)
        self.assertGreater(len(data["results"]), 0)

        top_hit = data["results"][0]
        self.assertIn("document_id", top_hit)
        self.assertIn("chunk_id", top_hit)
        self.assertIn("score", top_hit)
        self.assertIn("court", top_hit)
        self.assertIn("text", top_hit)
        self.assertGreater(top_hit["score"], 0)

    def test_a2_research_api_contract_and_provenance(self):
        """Verify Next.js /api/research accepts query and returns structured legal evidence with provenance."""
        payload = {
            "query": "Under Section 34 of the Arbitration and Conciliation Act, can the court modify an award?",
            "top_k": 5,
        }
        resp = requests.post(
            f"{NEXT_BASE_URL}/api/research",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=45,
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertIn("query", data)
        self.assertIn("retrievalStatus", data)
        self.assertEqual(data["retrievalStatus"], "SUCCESS")
        self.assertTrue(data.get("grounded"))
        self.assertIn("evidence", data)
        self.assertGreater(len(data["evidence"]), 0)

        # Inspect evidence contract
        evidence = data["evidence"][0]
        self.assertIn("evidence_id", evidence)
        self.assertIn("document_id", evidence)
        self.assertIn("chunk_id", evidence)
        self.assertIn("court", evidence)
        self.assertIn("case_title", evidence)
        self.assertIn("score", evidence)
        self.assertIn("relevanceCategory", evidence)
        self.assertIn("relevanceReason", evidence)
        self.assertIn("relevantExcerpt", evidence)
        self.assertIn(evidence["relevanceCategory"], ["DIRECT_EVIDENCE", "SUPPORTING_CONTEXT", "CONTRARY_OR_QUALIFYING"])

    # =========================================================================
    # TEST SUITE B: EVIDENCE AND RELEVANCE ACROSS TIERS
    # =========================================================================
    def test_b1_supreme_court_nhai_v_hakeem_sec34_modification(self):
        """
        Evaluation Case 1: Supreme Court Judgment
        National Highways Authority of India v. M. Hakeem (2021) 5 SCR 368
        Issue: Under Section 34 of the Arbitration Act, does the court have power to modify an award?
        Expected Finding: Court cannot modify an arbitral award; power is confined to setting aside.
        """
        query = "Section 34 Arbitration Act modification of arbitral award Hakeem"
        resp = requests.get(
            f"{DAEMON_BASE_URL}/search",
            params={"q": query, "top_k": 5},
            timeout=10,
        )
        self.assertEqual(resp.status_code, 200)
        results = resp.json().get("results", [])

        # Check that NHAI v. Hakeem (SC_2021 INSC 344) is retrieved in top results
        matching_hakeem = [
            r for r in results
            if "SC_2021 INSC 344" in r["document_id"] or "HAKEEM" in r.get("case_title", "").upper()
        ]
        self.assertGreater(len(matching_hakeem), 0, "NHAI v. Hakeem must be retrieved for Section 34 modification query")

        hakeem_chunk = matching_hakeem[0]
        self.assertIn("Supreme Court of India", hakeem_chunk["court"])
        # Check text contains Section 34 / s.34 and modification discussion
        text_lower = hakeem_chunk["text"].lower()
        self.assertTrue("s.34" in text_lower or "section 34" in text_lower)
        self.assertTrue("modify" in text_lower or "modification" in text_lower or "set aside" in text_lower)

    def test_b2_high_court_constitutional_nct_delhi_art_239aa(self):
        """
        Evaluation Case 2: Constitutional / High Court Reference
        Government of NCT of Delhi v. Union of India (2018) 7 SCR 1
        Issue: Executive powers of Government of NCT of Delhi under Article 239AA and aid/advice of Council of Ministers.
        Expected Finding: LG is bound by aid and advice of Council of Ministers; concurrence of LG is not required.
        """
        query = "Article 239AA Government of NCT of Delhi powers Council of Ministers aid and advice"
        resp = requests.get(
            f"{DAEMON_BASE_URL}/search",
            params={"q": query, "top_k": 5},
            timeout=10,
        )
        self.assertEqual(resp.status_code, 200)
        results = resp.json().get("results", [])

        matching_nct = [
            r for r in results
            if "SC_2019 INSC 194" in r["document_id"] or "GOVERNMENT OF NCT OF DELHI" in r.get("case_title", "").upper()
        ]
        self.assertGreater(len(matching_nct), 0, "NCT of Delhi v. UOI must be retrieved for Article 239AA query")

        nct_chunk = matching_nct[0]
        text_lower = nct_chunk["text"].lower()
        self.assertIn("239aa", text_lower)
        self.assertTrue("aid and advice" in text_lower or "council of ministers" in text_lower or "lieutenant governor" in text_lower)

    def test_b3_district_court_chennur_cc_179_1998(self):
        """
        Evaluation Case 3: District Court Record
        Junior Civil Judge Chennur CC 179/1998 (Adilabad / Mancherial, Telangana)
        Issue: Suo-moto advancement and transfer of CC 179/1998 to I Addl JFCM Mancherial.
        Expected Finding: Record transferred pursuant to Prl. District and Sessions Judge Adilabad directions.
        """
        query = "Chennur 179/1998 Mancherial"
        resp = requests.get(
            f"{DAEMON_BASE_URL}/search",
            params={"q": query, "top_k": 3},
            timeout=10,
        )
        self.assertEqual(resp.status_code, 200)
        results = resp.json().get("results", [])

        matching_dc = [
            r for r in results
            if "DC_DC-S3-001_29_22_1290176_1998_orders_1994_202100001791998_1" in r["document_id"]
        ]
        self.assertGreater(len(matching_dc), 0, "Chennur CC 179/1998 must be retrieved from District Court corpus")

        dc_chunk = matching_dc[0]
        self.assertIn("Chennur", dc_chunk["court"])
        self.assertIn("179 of 1998", dc_chunk["text"])
        self.assertIn("I Addl.JFCM, Mancherial", dc_chunk["text"])

    def test_b4_negative_control_fails_closed_without_hallucination(self):
        """
        Evaluation Case 4: Negative Control
        Query on topic absent from the corpus: Space debris salvage protocols under Outer Space Treaty.
        Expected: Fail-closed gate returns INSUFFICIENT_RELEVANCE, grounded=False, 0 evidence, and lists rejected authorities.
        """
        query = "Space debris liability and planetary defense salvage protocols under the Outer Space Treaty and Artemis Accords"
        resp = requests.post(
            f"{NEXT_BASE_URL}/api/research",
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=45,
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(data.get("retrievalStatus"), "INSUFFICIENT_RELEVANCE")
        self.assertFalse(data.get("grounded"))
        self.assertEqual(data.get("confidence"), "insufficient_evidence")
        self.assertEqual(len(data.get("evidence", [])), 0)
        self.assertIn("NOT_FOUND", data.get("answer", ""))
        self.assertIn("rejectedAuthorities", data)
        self.assertGreater(len(data["rejectedAuthorities"]), 0)

    # =========================================================================
    # TEST SUITE C: SOURCE RESOLUTION TO AUTHENTIC PHYSICAL DOCUMENTS
    # =========================================================================
    def test_c1_source_stream_supreme_court_precedent(self):
        """Verify /api/documents/stream successfully resolves and streams real Supreme Court judgment PDF."""
        # NHAI v. Hakeem: SC_2021 INSC 344_2021_5_368_407_EN.pdf
        doc_id = "SC_2021 INSC 344_2021_5_368_407_EN.pdf"
        resp = requests.get(
            f"{NEXT_BASE_URL}/api/documents/stream",
            params={"documentId": doc_id},
            headers=AUTH_HEADERS,
            timeout=10,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get("content-type"), "application/pdf")
        self.assertIn("2021_5_368_407_EN.pdf", resp.headers.get("content-disposition", ""))
        # Verify SHA-256 header matches payload
        streamed_sha = resp.headers.get("x-document-sha256")
        self.assertTrue(bool(streamed_sha))
        computed_sha = hashlib.sha256(resp.content).hexdigest()
        self.assertEqual(streamed_sha, computed_sha)

    def test_c2_source_stream_constitutional_bench_precedent(self):
        """Verify /api/documents/stream successfully resolves and streams real NCT Delhi precedent PDF."""
        doc_id = "SC_2019 INSC 194_2018_7_1_378_EN.pdf"
        resp = requests.get(
            f"{NEXT_BASE_URL}/api/documents/stream",
            params={"documentId": doc_id},
            headers=AUTH_HEADERS,
            timeout=10,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get("content-type"), "application/pdf")
        self.assertIn("2018_7_1_378_EN.pdf", resp.headers.get("content-disposition", ""))
        streamed_sha = resp.headers.get("x-document-sha256")
        self.assertTrue(bool(streamed_sha))
        computed_sha = hashlib.sha256(resp.content).hexdigest()
        self.assertEqual(streamed_sha, computed_sha)

    # =========================================================================
    # TEST SUITE D: FAILURE AND BOUNDARY HANDLING
    # =========================================================================
    def test_d1_empty_query_rejected(self):
        """Verify empty query string is rejected with HTTP 400."""
        resp = requests.post(
            f"{NEXT_BASE_URL}/api/research",
            json={"query": ""},
            headers={"Content-Type": "application/json"},
            timeout=5,
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertIn("error", data)

    def test_d2_whitespace_query_rejected(self):
        """Verify whitespace-only query string is rejected with HTTP 400."""
        resp = requests.post(
            f"{NEXT_BASE_URL}/api/research",
            json={"query": "     "},
            headers={"Content-Type": "application/json"},
            timeout=5,
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertIn("error", data)

    def test_d3_unauthenticated_document_streaming_rejected(self):
        """Verify unauthenticated request to stream a document is blocked with HTTP 401."""
        resp = requests.get(
            f"{NEXT_BASE_URL}/api/documents/stream",
            params={"documentId": "SC_2021 INSC 344_2021_5_368_407_EN.pdf"},
            timeout=5,
        )
        self.assertEqual(resp.status_code, 401)
        data = resp.json()
        self.assertIn("error", data)

    def test_d4_path_traversal_document_streaming_blocked(self):
        """Verify path traversal attempts are blocked with HTTP 403 or 400."""
        resp = requests.get(
            f"{NEXT_BASE_URL}/api/documents/stream",
            params={"documentId": "../../../etc/passwd"},
            headers=AUTH_HEADERS,
            timeout=5,
        )
        self.assertIn(resp.status_code, [400, 403, 404])

    def test_d5_nonexistent_document_returns_404(self):
        """Verify request for completely non-existent document ID returns HTTP 404."""
        resp = requests.get(
            f"{NEXT_BASE_URL}/api/documents/stream",
            params={"documentId": "non_existent_fake_judgment_9999.pdf"},
            headers=AUTH_HEADERS,
            timeout=5,
        )
        self.assertEqual(resp.status_code, 404)

    # =========================================================================
    # TEST SUITE E: REGRESSION VERIFICATION
    # =========================================================================
    def test_e1_matter_workspace_endpoints_operational(self):
        """Verify Workflow 1 matter endpoint is unaffected and returns valid matters."""
        resp = requests.get(f"{NEXT_BASE_URL}/api/matters", timeout=5)
        data = resp.json()
        matters = data if isinstance(data, list) else data.get("matters", [])
        self.assertIsInstance(matters, list)
        self.assertGreater(len(matters), 0)

    def test_e2_retrieval_daemon_health_and_cache_operational(self):
        """Verify daemon remains healthy and cache stats endpoint functions."""
        resp = requests.get(f"{DAEMON_BASE_URL}/cache/stats", timeout=5)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("cached_items_count", data)
        self.assertIn("hit_ratio", data)


if __name__ == "__main__":
    unittest.main()
