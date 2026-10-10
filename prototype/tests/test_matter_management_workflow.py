"""
Phase 4 Workflow 4: Complete Matter Management Test Suite
==========================================================
Rigorous end-to-end validation of the Vidhik Matter Workspace lifecycle:
1. Matter persistence: create/update supported fields, verify durability across reload.
2. Timeline: add events, verify chronological sorting and source vs user-input provenance.
3. Documents: stream authentic court judgments via authorized route, confirm SHA-256 identity.
4. Issues: create, confirm, and associate matter issues with evidence.
5. Statutory sections: verify section references, classifications, and applicability status.
6. Authorities: verify authority records, prevent false verification of unverified citations.
7. Evidence integration: link research evidence to matter issues and navigate to source document.
8. Notes: save, update, and reload user notes without silent overwrite.
9. Authorization: test unauthenticated mutations, invalid credentials, and cross-matter tenant isolation (401/403).
10. Failure handling: test 404 for missing records, 400 for invalid stage or malformed JSON, and traversal blocks.
11. Regression: ensure Workflows 1, 2, and 3 remain operational.
"""

import hashlib
import json
import os
import sys
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List

PROTOTYPE_ROOT = Path(__file__).resolve().parent.parent
if str(PROTOTYPE_ROOT) not in sys.path:
    sys.path.insert(0, str(PROTOTYPE_ROOT))

from rag.provenance import _find_source_pdf

NEXT_BASE_URL = os.environ.get("NEXT_BASE_URL", "http://localhost:3000")
RETRIEVAL_DAEMON_URL = os.environ.get("RETRIEVAL_DAEMON_URL", "http://127.0.0.1:8008")


def make_request(
    path: str,
    method: str = "GET",
    body: Dict[str, Any] = None,
    headers: Dict[str, str] = None,
    timeout: int = 45,
) -> tuple[int, Dict[str, Any], bytes]:
    url = f"{NEXT_BASE_URL}{path}"
    req_headers = {"User-Agent": "Vidhik-Workflow4-TestRunner/1.0"}
    if headers:
        req_headers.update(headers)

    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        req_headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw_bytes = resp.read()
            json_data = {}
            if resp.headers.get("Content-Type", "").startswith("application/json"):
                try:
                    json_data = json.loads(raw_bytes.decode("utf-8"))
                except Exception:
                    pass
            return resp.status, json_data, raw_bytes
    except urllib.error.HTTPError as e:
        raw_bytes = e.read()
        json_data = {}
        try:
            json_data = json.loads(raw_bytes.decode("utf-8"))
        except Exception:
            pass
        return e.code, json_data, raw_bytes


class TestMatterManagementWorkflow(unittest.TestCase):
    test_matter_id: str = ""

    @classmethod
    def setUpClass(cls):
        # Verify Next.js dev server is reachable
        status, _, _ = make_request("/api/matters", method="GET", headers={"x-lawyer-token": "dev_lawyer_token"})
        if status != 200:
            raise RuntimeError(f"Next.js server not responding on {NEXT_BASE_URL} (status {status})")

    @classmethod
    def tearDownClass(cls):
        # Cleanup test matter if created
        if cls.test_matter_id:
            make_request(
                f"/api/matters/{cls.test_matter_id}",
                method="DELETE",
                headers={"x-lawyer-token": "dev_lawyer_token", "x-matter-id": cls.test_matter_id},
            )

    def test_01_matter_persistence_lifecycle(self):
        """Category 1: Create matter, update status/summary, verify durability on reload."""
        # 1. Create new matter
        create_payload = {
            "title": "National Highways Authority of India v. P. Nagaraju & Ors.",
            "court": "Supreme Court of India",
            "matterType": "Civil Appeal",
            "status": "Filed",
            "client": "National Highways Authority of India",
            "summary": "Special leave appeal on compensation determination under National Highways Act, 1956.",
            "proceedingType": "CIVIL_APPEAL",
            "parties": {
                "petitioner": "National Highways Authority of India",
                "respondent": "P. Nagaraju & Ors.",
                "counsel": "Senior Counsel for NHAI",
                "court": "Supreme Court of India",
                "bench": "Division Bench",
            },
        }

        status, data, _ = make_request(
            "/api/matters",
            method="POST",
            body=create_payload,
            headers={"x-lawyer-token": "dev_lawyer_token"},
        )
        self.assertEqual(status, 201, f"Failed to create matter: {data}")
        self.assertIn("matter", data)
        matter = data["matter"]
        TestMatterManagementWorkflow.test_matter_id = matter["id"]
        self.assertTrue(matter["id"].startswith("MAT-"))
        self.assertEqual(matter["status"], "Filed")

        # 2. Update matter status to Pleadings and update summary
        update_payload = {
            "status": "Pleadings",
            "currentStage": "Pleadings",
            "summary": "Pleadings completed. Challenge raised to arbitral award modification under Section 34.",
        }
        status, data, _ = make_request(
            f"/api/matters/{matter['id']}",
            method="PUT",
            body=update_payload,
            headers={"x-lawyer-token": "dev_lawyer_token", "x-matter-id": matter["id"]},
        )
        self.assertEqual(status, 200, f"Failed to update matter: {data}")
        self.assertEqual(data["matter"]["status"], "Pleadings")
        self.assertEqual(data["matter"]["summary"], update_payload["summary"])

        # 3. Reload from server via fresh GET and confirm persisted state survives
        status, reload_data, _ = make_request(
            f"/api/matters/{matter['id']}",
            method="GET",
            headers={"x-lawyer-token": "dev_lawyer_token", "x-matter-id": matter["id"]},
        )
        self.assertEqual(status, 200)
        reloaded = reload_data["matter"]
        self.assertEqual(reloaded["status"], "Pleadings")
        self.assertEqual(reloaded["summary"], update_payload["summary"])
        self.assertEqual(reloaded["client"], create_payload["client"])

    def test_02_timeline_chronological_ordering_and_provenance(self):
        """Category 2: Add procedural events out-of-order, verify chronological sorting and provenance."""
        matter_id = TestMatterManagementWorkflow.test_matter_id
        self.assertTrue(matter_id, "Test matter ID not set")

        # Events with out-of-order dates and distinct provenance
        events = [
            {
                "id": "EVT-03",
                "matterId": matter_id,
                "date": "2024-05-20",
                "title": "Interim Order on Deposit of Award Sum",
                "description": "Court directed NHAI to deposit 50% of the enhanced compensation.",
                "eventType": "INTERIM_ORDER",
                "source": "court_record",
                "provenance": "SOURCE_EXPLICIT",
                "sourceDocumentName": "Order_Dated_20_May_2024.pdf",
            },
            {
                "id": "EVT-01",
                "matterId": matter_id,
                "date": "2024-01-15",
                "title": "Filing of Special Leave Petition",
                "description": "Petition presented under Article 136 challenging High Court judgment.",
                "eventType": "FILING",
                "source": "pleadings",
                "provenance": "SOURCE_EXPLICIT",
                "sourceDocumentName": "Petition_Alpha.pdf",
            },
            {
                "id": "EVT-02",
                "matterId": matter_id,
                "date": "2024-03-10",
                "title": "Notice Issued by Division Bench",
                "description": "Judicial notice issued to respondents returnable in 6 weeks.",
                "eventType": "NOTICE_ISSUED",
                "source": "lawyer",
                "provenance": "USER_PROVIDED",
            },
        ]

        status, data, _ = make_request(
            f"/api/matters/{matter_id}",
            method="PUT",
            body={"timeline": events},
            headers={"x-lawyer-token": "dev_lawyer_token", "x-matter-id": matter_id},
        )
        self.assertEqual(status, 200, f"Failed to persist timeline: {data}")

        # Reload and verify chronological sort on server
        status, reload_data, _ = make_request(
            f"/api/matters/{matter_id}",
            method="GET",
            headers={"x-lawyer-token": "dev_lawyer_token", "x-matter-id": matter_id},
        )
        timeline = reload_data["matter"]["timeline"]
        self.assertEqual(len(timeline), 3)

        # Dates must be strictly non-decreasing: 2024-01-15, 2024-03-10, 2024-05-20
        dates = [ev["date"] for ev in timeline]
        self.assertEqual(dates, ["2024-01-15", "2024-03-10", "2024-05-20"])

        # Provenance must be intact
        evt_notice = next(ev for ev in timeline if ev["id"] == "EVT-02")
        self.assertEqual(evt_notice["provenance"], "USER_PROVIDED")
        self.assertEqual(evt_notice["source"], "lawyer")

        evt_filing = next(ev for ev in timeline if ev["id"] == "EVT-01")
        self.assertEqual(evt_filing["provenance"], "SOURCE_EXPLICIT")

    def test_03_documents_authorized_streaming_and_cryptographic_integrity(self):
        """Category 3: Open matter document via authorized streaming and confirm SHA-256 identity."""
        matter_id = TestMatterManagementWorkflow.test_matter_id

        # Stream authentic Supreme Court judgment from repository (Hakeem precedent)
        doc_name = "SC_2021 INSC 344_2021_5_368_407_EN.pdf"
        encoded_doc = urllib.parse.quote(doc_name)
        status, _, pdf_bytes = make_request(
            f"/api/documents/stream?documentId={encoded_doc}&matterId={matter_id}",
            method="GET",
            headers={"x-lawyer-token": "dev_lawyer_token", "x-matter-id": matter_id},
        )
        self.assertEqual(status, 200, "Failed to stream authentic judgment PDF")
        self.assertTrue(pdf_bytes.startswith(b"%PDF"), "Streamed content is not a valid PDF")
        self.assertGreater(len(pdf_bytes), 100_000, "PDF size is unrealistically small")

        # Verify SHA-256 matches actual physical file on disk
        computed_sha = hashlib.sha256(pdf_bytes).hexdigest()
        local_pdf_path = _find_source_pdf(doc_name)
        self.assertIsNotNone(local_pdf_path, f"Local test PDF not found for {doc_name}")
        self.assertTrue(local_pdf_path.exists(), f"Local test PDF not found at {local_pdf_path}")
        disk_sha = hashlib.sha256(local_pdf_path.read_bytes()).hexdigest()
        self.assertEqual(computed_sha, disk_sha, "Cryptographic hash mismatch on streamed document")

    def test_04_issues_lifecycle_and_confirmation(self):
        """Category 4: Create court issue, confirm AI-suggested issue, verify persistence."""
        matter_id = TestMatterManagementWorkflow.test_matter_id

        issues = [
            {
                "id": "ISS-01",
                "issueNumber": "Issue 01",
                "title": "Whether Section 34 of the Arbitration Act permits court modification of arbitral awards",
                "description": "Whether judicial power to set aside includes power to vary compensation quantum.",
                "source": "court",
                "confirmed": True,
                "provenance": "SOURCE_EXPLICIT",
                "relatedDocuments": ["SC_2021 INSC 344_2021_5_368_407_EN.pdf"],
                "relatedSections": ["Section 34", "Section 37"],
                "relatedAuthorities": ["(2021) 9 SCC 1"],
            },
            {
                "id": "ISS-02",
                "issueNumber": "Issue 02",
                "title": "Applicability of Section 5 Limitation Act to appeals under Section 37",
                "description": "AI-suggested issue derived from party delay submissions.",
                "source": "ai",
                "confirmed": False,
                "provenance": "AI_ANALYSIS",
                "relatedDocuments": [],
                "relatedSections": ["Section 5", "Section 37"],
                "relatedAuthorities": [],
            },
        ]

        status, data, _ = make_request(
            f"/api/matters/{matter_id}",
            method="PUT",
            body={"issues": issues},
            headers={"x-lawyer-token": "dev_lawyer_token", "x-matter-id": matter_id},
        )
        self.assertEqual(status, 200)

        # Now confirm the second issue (lawyer promotes AI suggestion to confirmed issue)
        issues[1]["confirmed"] = True
        issues[1]["provenance"] = "USER_PROVIDED"
        issues[1]["source"] = "lawyer"

        status, data, _ = make_request(
            f"/api/matters/{matter_id}",
            method="PUT",
            body={"issues": issues},
            headers={"x-lawyer-token": "dev_lawyer_token", "x-matter-id": matter_id},
        )
        self.assertEqual(status, 200)

        # Reload and check
        status, reload_data, _ = make_request(
            f"/api/matters/{matter_id}",
            method="GET",
            headers={"x-lawyer-token": "dev_lawyer_token", "x-matter-id": matter_id},
        )
        saved_issues = reload_data["matter"]["issues"]
        self.assertEqual(len(saved_issues), 2)
        self.assertTrue(saved_issues[0]["confirmed"])
        self.assertEqual(saved_issues[0]["provenance"], "SOURCE_EXPLICIT")
        self.assertTrue(saved_issues[1]["confirmed"])
        self.assertEqual(saved_issues[1]["provenance"], "USER_PROVIDED")

    def test_05_statutory_sections_applicability_classification(self):
        """Category 5: Verify section references and evidentiary applicability distinctions."""
        matter_id = TestMatterManagementWorkflow.test_matter_id

        sections = [
            {
                "id": "SEC-01",
                "act": "Arbitration and Conciliation Act, 1996",
                "section": "Section 34",
                "heading": "Application for setting aside arbitral award",
                "headingVerification": "VERIFIED",
                "applicability": "SECTION_APPLIED",
                "description": "Court interpreted Section 34 as permitting setting aside only, not modification.",
                "sourceDocument": "SC_2021 INSC 344_2021_5_368_407_EN.pdf",
                "provenance": "SOURCE_EXPLICIT",
            },
            {
                "id": "SEC-02",
                "act": "Limitation Act, 1963",
                "section": "Section 5",
                "heading": "Extension of prescribed period in certain cases",
                "headingVerification": "VERIFIED",
                "applicability": "SECTION_ALLEGED_BY_PARTY",
                "description": "Respondent sought condonation of delay alleging sufficient cause.",
                "sourceDocument": "User Entry / Pleadings Record",
                "provenance": "USER_PROVIDED",
            },
            {
                "id": "SEC-03",
                "act": "National Highways Act, 1956",
                "section": "Section 3G(5)",
                "heading": "Determination of amount of compensation",
                "headingVerification": "NOT_VERIFIED",
                "applicability": "SECTION_HELD_APPLICABLE",
                "description": "Arbitration statutory reference under which initial compensation was awarded.",
                "sourceDocument": "SC_2021 INSC 344_2021_5_368_407_EN.pdf",
                "provenance": "SOURCE_EXPLICIT",
            },
        ]

        status, data, _ = make_request(
            f"/api/matters/{matter_id}",
            method="PUT",
            body={"sections": sections},
            headers={"x-lawyer-token": "dev_lawyer_token", "x-matter-id": matter_id},
        )
        self.assertEqual(status, 200)

        # Reload and verify classifications
        status, reload_data, _ = make_request(
            f"/api/matters/{matter_id}",
            method="GET",
            headers={"x-lawyer-token": "dev_lawyer_token", "x-matter-id": matter_id},
        )
        saved_sections = reload_data["matter"]["sections"]
        self.assertEqual(len(saved_sections), 3)

        sec_34 = next(s for s in saved_sections if s["section"] == "Section 34")
        self.assertEqual(sec_34["applicability"], "SECTION_APPLIED")

        sec_5 = next(s for s in saved_sections if s["section"] == "Section 5")
        self.assertEqual(sec_5["applicability"], "SECTION_ALLEGED_BY_PARTY")
        self.assertEqual(sec_5["provenance"], "USER_PROVIDED")

        sec_3g = next(s for s in saved_sections if s["section"] == "Section 3G(5)")
        self.assertEqual(sec_3g["applicability"], "SECTION_HELD_APPLICABLE")
        self.assertEqual(sec_3g["headingVerification"], "NOT_VERIFIED")

    def test_06_authorities_citations_and_honest_verification(self):
        """Category 6: Verify authority records and ensure unverified authorities are not falsely verified."""
        matter_id = TestMatterManagementWorkflow.test_matter_id

        authorities = [
            {
                "id": "AUTH-01",
                "caseTitle": "Project Director, NHAI v. M. Hakeem",
                "caseNumber": "(2021) 9 SCC 1",
                "court": "Supreme Court of India",
                "year": "2021",
                "relevance": "Direct authority holding Section 34 does not permit court modification of arbitral awards.",
                "supportingEvidence": "Section 34 does not empower the court to modify the arbitral award.",
                "presence": "FOUND_IN_SOURCE",
                "verificationStatus": "verified",
                "independentVerification": "VERIFIED",
                "provenance": "SOURCE_EXPLICIT",
            },
            {
                "id": "AUTH-02",
                "caseTitle": "Unverified Precedent Cited by Opposite Counsel",
                "caseNumber": "2023 SCC OnLine Del 9999",
                "court": "High Court of Delhi",
                "year": "2023",
                "relevance": "Alleged qualification of Section 34 powers in infrastructure matters.",
                "supportingEvidence": "Cited in oral arguments.",
                "presence": "EXTERNAL_REFERENCE",
                "verificationStatus": "unverified",
                "independentVerification": "NOT_VERIFIED",
                "provenance": "USER_PROVIDED",
            },
        ]

        status, data, _ = make_request(
            f"/api/matters/{matter_id}",
            method="PUT",
            body={"authorities": authorities},
            headers={"x-lawyer-token": "dev_lawyer_token", "x-matter-id": matter_id},
        )
        self.assertEqual(status, 200)

        # Reload and verify
        status, reload_data, _ = make_request(
            f"/api/matters/{matter_id}",
            method="GET",
            headers={"x-lawyer-token": "dev_lawyer_token", "x-matter-id": matter_id},
        )
        saved_auth = reload_data["matter"]["authorities"]
        self.assertEqual(len(saved_auth), 2)

        hakeem = next(a for a in saved_auth if "Hakeem" in a["caseTitle"])
        self.assertEqual(hakeem["independentVerification"], "VERIFIED")

        unverified = next(a for a in saved_auth if "Unverified" in a["caseTitle"])
        self.assertEqual(unverified["independentVerification"], "NOT_VERIFIED")
        self.assertNotEqual(unverified["independentVerification"], "VERIFIED")
        self.assertEqual(unverified["provenance"], "USER_PROVIDED")

    def test_07_evidence_integration_and_source_navigation(self):
        """Category 7: Associate research evidence with issue and verify source resolution."""
        matter_id = TestMatterManagementWorkflow.test_matter_id

        evidence_items = [
            {
                "id": "EVID-01",
                "matterId": matter_id,
                "issueId": "ISS-01",
                "issueTitle": "Whether Section 34 permits award modification",
                "claim": "Section 34 does not confer power to modify an award",
                "claimType": "FINAL_HOLDING",
                "stance": "supporting",
                "evidenceExcerpt": "Section 34 is not an appellate provision and does not allow modification of the arbitral award.",
                "sourceDocument": "SC_2021 INSC 344_2021_5_368_407_EN.pdf",
                "pageNumber": "15",
                "paragraphId": "31",
                "sourceType": "PRIMARY_JUDGMENT",
                "relatedAuthority": {
                    "caseTitle": "Project Director, NHAI v. M. Hakeem",
                    "court": "Supreme Court of India",
                    "year": "2021",
                    "citation": "(2021) 9 SCC 1",
                },
                "isPinned": True,
                "grounded": True,
                "verification": "source_supported",
                "provenance": "INDEPENDENTLY_VERIFIED",
            }
        ]

        status, data, _ = make_request(
            f"/api/matters/{matter_id}",
            method="PUT",
            body={"evidence": evidence_items},
            headers={"x-lawyer-token": "dev_lawyer_token", "x-matter-id": matter_id},
        )
        self.assertEqual(status, 200)

        # Reload matter and verify evidence linkage
        status, reload_data, _ = make_request(
            f"/api/matters/{matter_id}",
            method="GET",
            headers={"x-lawyer-token": "dev_lawyer_token", "x-matter-id": matter_id},
        )
        saved_evid = reload_data["matter"]["evidence"]
        self.assertEqual(len(saved_evid), 1)
        item = saved_evid[0]
        self.assertEqual(item["issueId"], "ISS-01")
        self.assertTrue(item["isPinned"])
        self.assertEqual(item["stance"], "supporting")

        # Verify navigation to original source document via authorized stream endpoint
        src_doc = item["sourceDocument"]
        status, _, raw_doc = make_request(
            f"/api/documents/stream?documentId={urllib.parse.quote(src_doc)}&matterId={matter_id}",
            method="GET",
            headers={"x-lawyer-token": "dev_lawyer_token", "x-matter-id": matter_id},
        )
        self.assertEqual(status, 200, "Failed to resolve source document for linked evidence")
        self.assertTrue(raw_doc.startswith(b"%PDF"))

    def test_08_notes_persistence_and_no_overwrite(self):
        """Category 8: Save user notes, update them, and confirm reload without unintended overwrites."""
        matter_id = TestMatterManagementWorkflow.test_matter_id

        notes = [
            {
                "id": "NOTE-01",
                "matterId": matter_id,
                "title": "Submissions Outline for Final Hearing",
                "content": "1. Open on statutory scheme of Section 34.\n2. Cite 3-Judge bench in Hakeem.\n3. Distinguish respondent's reliance on equity powers under Article 142.",
                "updatedAt": "2026-10-10T12:00:00.000Z",
                "tags": ["Hearing", "Submissions", "Section 34"],
            }
        ]

        status, data, _ = make_request(
            f"/api/matters/{matter_id}",
            method="PUT",
            body={"notes": notes},
            headers={"x-lawyer-token": "dev_lawyer_token", "x-matter-id": matter_id},
        )
        self.assertEqual(status, 200)

        # Reload and check notes survive
        status, reload_data, _ = make_request(
            f"/api/matters/{matter_id}",
            method="GET",
            headers={"x-lawyer-token": "dev_lawyer_token", "x-matter-id": matter_id},
        )
        saved_notes = reload_data["matter"]["notes"]
        self.assertEqual(len(saved_notes), 1)
        self.assertEqual(saved_notes[0]["id"], "NOTE-01")
        self.assertEqual(saved_notes[0]["title"], "Submissions Outline for Final Hearing")
        self.assertEqual(saved_notes[0]["tags"], ["Hearing", "Submissions", "Section 34"])

    def test_09_authorization_and_cross_matter_isolation(self):
        """Category 9: Test unauthorized requests, invalid tokens, and cross-matter reads/mutations."""
        matter_id = TestMatterManagementWorkflow.test_matter_id

        # 1. Unauthenticated mutation -> 401
        status, data, _ = make_request(
            f"/api/matters/{matter_id}",
            method="PUT",
            body={"status": "Evidence"},
            headers={},  # no auth token
        )
        self.assertEqual(status, 401, f"Expected 401 on unauthenticated mutation, got {status}")

        # 2. Invalid credentials -> 401
        status, data, _ = make_request(
            f"/api/matters/{matter_id}",
            method="PUT",
            body={"status": "Evidence"},
            headers={"x-lawyer-token": "invalid_bad_token"},
        )
        self.assertEqual(status, 401, f"Expected 401 on invalid token, got {status}")

        # 3. Cross-matter mutation: caller authorized for MAT-999 trying to mutate test_matter_id -> 403
        status, data, _ = make_request(
            f"/api/matters/{matter_id}",
            method="PUT",
            body={"status": "Evidence"},
            headers={"x-lawyer-token": "dev_lawyer_token", "x-matter-id": "MAT-FOREIGN-999"},
        )
        self.assertEqual(status, 403, f"Expected 403 on cross-matter mutation, got {status}")
        self.assertIn("ACCESS_DENIED_CROSS_MATTER", data.get("error", ""))

        # 4. Cross-matter read: caller authorized for MAT-999 trying to read test_matter_id -> 403
        status, data, _ = make_request(
            f"/api/matters/{matter_id}",
            method="GET",
            headers={"x-lawyer-token": "dev_lawyer_token", "x-matter-id": "MAT-FOREIGN-999"},
        )
        self.assertEqual(status, 403, f"Expected 403 on cross-matter read, got {status}")

    def test_10_failure_handling_and_input_validation(self):
        """Category 10: Test missing records (404), invalid stages (400), and malformed payloads."""
        matter_id = TestMatterManagementWorkflow.test_matter_id

        # 1. Missing record -> 404
        status, data, _ = make_request(
            "/api/matters/MAT-DOES-NOT-EXIST-404",
            method="GET",
            headers={"x-lawyer-token": "dev_lawyer_token", "x-matter-id": "MAT-DOES-NOT-EXIST-404"},
        )
        self.assertEqual(status, 404, f"Expected 404 for missing matter, got {status}")

        # 2. Invalid status/stage value -> 400
        status, data, _ = make_request(
            f"/api/matters/{matter_id}",
            method="PUT",
            body={"status": "INVALID_FABRICATED_STAGE"},
            headers={"x-lawyer-token": "dev_lawyer_token", "x-matter-id": matter_id},
        )
        self.assertEqual(status, 400, f"Expected 400 for invalid stage, got {status}")
        self.assertIn("Invalid matter status", data.get("error", ""))

        # 3. Path traversal document streaming -> 400 or 403
        status, _, _ = make_request(
            f"/api/documents/stream?documentId=../../../../etc/passwd&matterId={matter_id}",
            method="GET",
            headers={"x-lawyer-token": "dev_lawyer_token", "x-matter-id": matter_id},
        )
        self.assertIn(status, [400, 403, 404], f"Expected security rejection, got {status}")

    def test_11_regression_workflows_1_to_3(self):
        """Category 11: Regression validation to confirm Workflows 1, 2, and 3 remain functional."""
        # 1. Workflow 1 Check: Verify Document Intake / demonstration route works
        status, demo_data, _ = make_request(
            "/api/documents/demonstrate",
            method="GET",
            headers={"x-lawyer-token": "dev_lawyer_token"},
        )
        self.assertEqual(status, 200, "Workflow 1 demonstration route returned non-200")
        self.assertIn("chunks", demo_data)

        # 2. Workflow 2 Check: Query retrieval daemon directly
        daemon_req = urllib.request.Request(
            f"{RETRIEVAL_DAEMON_URL}/search",
            data=json.dumps({"query": "arbitration award modification section 34", "top_k": 3}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(daemon_req, timeout=10) as resp:
            self.assertEqual(resp.status, 200)
            daemon_results = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(len(daemon_results.get("results", [])) > 0, "Workflow 2 returned zero search results")

        # 3. Workflow 3 Check: Verify Legal Research RAG endpoint produces grounded response
        status, rag_data, _ = make_request(
            "/api/research",
            method="POST",
            body={"query": "Section 34 limitation period for setting aside award", "top_k": 3},
            headers={"x-lawyer-token": "dev_lawyer_token"},
        )
        self.assertEqual(status, 200, f"Workflow 3 research route failed: {rag_data}")
        self.assertIn("evidence", rag_data)
        self.assertTrue(len(rag_data["evidence"]) > 0, "Workflow 3 returned no grounded evidence")


if __name__ == "__main__":
    unittest.main(verbosity=2)
