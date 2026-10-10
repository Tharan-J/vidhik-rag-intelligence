"""
Phase 4 Workflow 1: End-to-End Document Intake -> Matter Workspace Test Suite
=============================================================================
Required automated tests:
1. Valid PDF upload and successful matter creation.
2. Invalid file type and malformed PDF rejection.
3. Missing or ambiguous metadata without fabricated values.
4. Extraction failure with an accurate UI/API status.
5. Retry or duplicate-submission handling.
6. Document hash and identity preservation.
7. Unauthorized access rejection.
8. Cross-matter document access rejection.
9. No public static access to confidential documents.
10. Successful navigation to the correct matter after processing.
11. Matter and document persistence across a reload.
12. Regression of existing workspace and evidence-verification functionality.
"""

import os
import sys
import json
import time
import shutil
import hashlib
import requests
import unittest
from pathlib import Path

# Paths
PROTOTYPE_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = PROTOTYPE_ROOT.parent
FRONTEND_ROOT = WORKSPACE_ROOT / "frontend"
EXTRACTED_MATTERS_PATH = FRONTEND_ROOT / "src" / "lib" / "data" / "extracted_matters.json"
PRIVATE_STORAGE_ROOT = FRONTEND_ROOT / "storage" / "documents" / "matters"
PUBLIC_DOCS_ROOT = FRONTEND_ROOT / "public" / "documents"
RESEARCH_DATA_DIR = WORKSPACE_ROOT / "research" / "legal_data"

NEXT_BASE_URL = "http://localhost:3000"
DAEMON_BASE_URL = "http://127.0.0.1:8008"


def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class TestDocumentIntakeWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Verify Next.js dev server is reachable
        try:
            r = requests.get(f"{NEXT_BASE_URL}/api/matters", timeout=5)
            assert r.status_code == 200
        except Exception as e:
            raise RuntimeError(f"Next.js server is not reachable on {NEXT_BASE_URL}: {e}")

        # Verify Retrieval Daemon is healthy
        try:
            r = requests.get(f"{DAEMON_BASE_URL}/health", timeout=5)
            assert r.status_code == 200
        except Exception as e:
            raise RuntimeError(f"Retrieval daemon is not healthy on {DAEMON_BASE_URL}: {e}")

        # Authentic sample PDF for ingestion tests
        # We can use Dr Balram Singh .pdf or Borse Brothers if available
        cls.real_pdf_path = RESEARCH_DATA_DIR / "Dr Balram Singh .pdf"
        if not cls.real_pdf_path.exists():
            # Fallback to test directory
            cls.real_pdf_path = WORKSPACE_ROOT / "test" / "Dr Balram Singh .pdf"

        assert cls.real_pdf_path.exists(), f"Authentic source PDF not found at {cls.real_pdf_path}"
        with open(cls.real_pdf_path, "rb") as f:
            cls.real_pdf_bytes = f.read()
        cls.real_pdf_hash = compute_sha256(cls.real_pdf_bytes)

        cls.created_matter_ids = []

    @classmethod
    def tearDownClass(cls):
        # Clean up any test matters created during the run to preserve repository cleanliness
        if cls.created_matter_ids and EXTRACTED_MATTERS_PATH.exists():
            try:
                with open(EXTRACTED_MATTERS_PATH, "r", encoding="utf-8") as f:
                    matters = json.load(f)
                cleaned = [m for m in matters if m.get("id") not in cls.created_matter_ids]
                with open(EXTRACTED_MATTERS_PATH, "w", encoding="utf-8") as f:
                    json.dump(cleaned, f, indent=2)
            except Exception as e:
                print(f"Warning cleaning test matters: {e}")

        # Clean up test directories in storage
        for mid in cls.created_matter_ids:
            target = PRIVATE_STORAGE_ROOT / mid
            if target.exists():
                shutil.rmtree(target, ignore_errors=True)

    # -------------------------------------------------------------------------
    # TEST 1: Valid PDF upload and successful matter creation
    # -------------------------------------------------------------------------
    def test_01_valid_pdf_upload_and_matter_creation(self):
        """End-to-End: Valid PDF upload parses, ingests, saves confidentially, and creates matter."""
        files = {
            "file": ("Balram_Singh_Writ.pdf", self.real_pdf_bytes, "application/pdf")
        }
        data = {
            "customTitle": "Dr Balram Singh Union of India Writ",
            "clientName": "Dr. Balram Singh"
        }

        res = requests.post(f"{NEXT_BASE_URL}/api/matters/ingest", files=files, data=data, timeout=60)
        self.assertEqual(res.status_code, 200, f"Ingestion failed: {res.text}")

        res_json = res.json()
        self.assertTrue(res_json.get("success"))
        matter = res_json.get("matter")
        matter_id = res_json.get("matterId")

        self.assertIsNotNone(matter)
        self.assertTrue(matter_id.startswith("MAT-"))
        self.created_matter_ids.append(matter_id)

        # Check document attached
        docs = matter.get("documents", [])
        self.assertGreaterEqual(len(docs), 1)
        doc = docs[0]
        self.assertEqual(doc.get("name"), "Balram_Singh_Writ.pdf")
        self.assertEqual(doc.get("extractionStatus"), "completed")
        self.assertEqual(doc.get("provenance"), "SOURCE_EXPLICIT")

        # Step B checks: Storage path outside web root, SHA-256 match
        self.assertIn("storagePath", doc)
        self.assertTrue(doc["storagePath"].startswith("storage/documents/matters/"))
        self.assertNotIn("public", doc["storagePath"])
        self.assertEqual(doc.get("sha256"), self.real_pdf_hash)

        # Verify physical file existence in private storage
        stored_file = FRONTEND_ROOT / doc["storagePath"]
        self.assertTrue(stored_file.exists(), f"Stored file does not exist at {stored_file}")

    # -------------------------------------------------------------------------
    # TEST 2: Invalid file type and malformed PDF rejection
    # -------------------------------------------------------------------------
    def test_02_invalid_file_type_and_malformed_pdf_rejection(self):
        """Rejection tests for non-PDFs and corrupt/malformed PDF streams."""
        # 2a: Unsupported file type (.exe)
        files = {"file": ("malicious.exe", b"MZ\x90\x00\x03\x00\x00\x00", "application/octet-stream")}
        res = requests.post(f"{NEXT_BASE_URL}/api/matters/ingest", files=files, timeout=10)
        self.assertEqual(res.status_code, 400)
        self.assertIn("UNSUPPORTED_FILE_TYPE", res.json().get("error", ""))

        # 2b: Malformed PDF without %PDF- magic bytes
        files = {"file": ("corrupted.pdf", b"This is not a PDF document at all.", "application/pdf")}
        res = requests.post(f"{NEXT_BASE_URL}/api/matters/ingest", files=files, timeout=10)
        self.assertEqual(res.status_code, 422)
        self.assertIn("MALFORMED_PDF", res.json().get("error", ""))

        # 2c: Empty file
        files = {"file": ("empty.pdf", b"", "application/pdf")}
        res = requests.post(f"{NEXT_BASE_URL}/api/matters/ingest", files=files, timeout=10)
        self.assertEqual(res.status_code, 422)

    # -------------------------------------------------------------------------
    # TEST 3: Missing or ambiguous metadata without fabricated values
    # -------------------------------------------------------------------------
    def test_03_missing_or_ambiguous_metadata_no_fabrication(self):
        """Metadata safeguards: Ambiguous/missing fields remain unknown; no filing date guessing."""
        files = {
            "file": ("Balram_Singh_Writ.pdf", self.real_pdf_bytes, "application/pdf")
        }
        # Ingest without client hint
        res = requests.post(f"{NEXT_BASE_URL}/api/matters/ingest", files=files, timeout=60)
        self.assertEqual(res.status_code, 200)
        matter = res.json().get("matter")

        # Field-level provenance check
        field_prov = matter.get("fieldProvenance", {})
        self.assertIn("filingDate", field_prov)

        # Filing date should be null or NOT_FOUND unless explicitly in source
        filing_val = field_prov["filingDate"].get("value")
        filing_prov = field_prov["filingDate"].get("provenance")
        self.assertIn(filing_prov, ["NOT_FOUND", "SOURCE_EXPLICIT"])
        if filing_val:
            # Filing date must NOT be fabricated from case number year (e.g. 2024-01-01)
            self.assertFalse(filing_val.endswith("-01-01"))

        # Client must NOT be petitioner/appellant; should be NOT_FOUND if not provided
        self.assertIn(field_prov.get("client", {}).get("provenance"), ["NOT_FOUND", "USER_PROVIDED"])

    # -------------------------------------------------------------------------
    # TEST 4: Extraction failure with an accurate UI/API status
    # -------------------------------------------------------------------------
    def test_04_extraction_failure_accurate_status(self):
        """Extraction failure returns 422 recoverable error without corrupt matter record."""
        # Valid PDF header but zero text
        empty_pdf_bytes = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
        files = {"file": ("zero_text_order.pdf", empty_pdf_bytes, "application/pdf")}

        res = requests.post(f"{NEXT_BASE_URL}/api/matters/ingest", files=files, timeout=15)
        self.assertEqual(res.status_code, 422)
        res_json = res.json()
        self.assertEqual(res_json.get("extractionStatus"), "failed")
        self.assertTrue(res_json.get("recoverable"))

        # Invariant: No corrupt matter record saved to extracted_matters.json
        failed_mid = res_json.get("matterId")
        if failed_mid and EXTRACTED_MATTERS_PATH.exists():
            with open(EXTRACTED_MATTERS_PATH, "r", encoding="utf-8") as f:
                matters = json.load(f)
            matching = [m for m in matters if m.get("id") == failed_mid]
            self.assertEqual(len(matching), 0, "Corrupt matter record must not be saved on extraction failure!")

    # -------------------------------------------------------------------------
    # TEST 5: Retry or duplicate-submission handling
    # -------------------------------------------------------------------------
    def test_05_retry_or_duplicate_submission_handling(self):
        """Submitting the same document twice returns existing matter without duplicate records."""
        # First submission
        files = {"file": ("Balram_Singh_Writ.pdf", self.real_pdf_bytes, "application/pdf")}
        res1 = requests.post(f"{NEXT_BASE_URL}/api/matters/ingest", files=files, timeout=60)
        self.assertEqual(res1.status_code, 200)
        m1 = res1.json()

        # Second submission with identical bytes (simulating double click or network retry)
        files2 = {"file": ("Balram_Singh_Writ.pdf", self.real_pdf_bytes, "application/pdf")}
        res2 = requests.post(f"{NEXT_BASE_URL}/api/matters/ingest", files=files2, timeout=60)
        self.assertEqual(res2.status_code, 200)
        m2 = res2.json()

        self.assertTrue(m2.get("isDuplicateRetry"))
        self.assertEqual(m1.get("matterId"), m2.get("matterId"))

        # Verify no duplicate entry in extracted_matters.json
        with open(EXTRACTED_MATTERS_PATH, "r", encoding="utf-8") as f:
            matters = json.load(f)
        occurrences = [m for m in matters if m.get("id") == m1.get("matterId")]
        self.assertEqual(len(occurrences), 1, "There must be exactly 1 matter record for this document.")

    # -------------------------------------------------------------------------
    # TEST 6: Document hash and identity preservation
    # -------------------------------------------------------------------------
    def test_06_document_hash_and_identity_preservation(self):
        """Stored document retains exact SHA-256 hash and valid document identity."""
        files = {"file": ("Balram_Singh_Writ.pdf", self.real_pdf_bytes, "application/pdf")}
        res = requests.post(f"{NEXT_BASE_URL}/api/matters/ingest", files=files, timeout=60)
        matter = res.json().get("matter")
        doc = matter["documents"][0]

        # Verify disk contents match hash
        target_path = FRONTEND_ROOT / doc["storagePath"]
        with open(target_path, "rb") as f:
            disk_bytes = f.read()
        disk_hash = compute_sha256(disk_bytes)

        self.assertEqual(disk_hash, self.real_pdf_hash)
        self.assertEqual(doc.get("sha256"), self.real_pdf_hash)
        self.assertTrue(doc.get("id").startswith("DOC-"))

    # -------------------------------------------------------------------------
    # TEST 7: Unauthorized access rejection
    # -------------------------------------------------------------------------
    def test_07_unauthorized_access_rejection(self):
        """Streaming endpoint rejects unauthenticated access attempts."""
        # Unauthenticated request (no auth headers, no matter header)
        res = requests.get(f"{NEXT_BASE_URL}/api/documents/stream?docId=Balram_Singh_Writ.pdf")
        self.assertEqual(res.status_code, 401)
        self.assertIn("UNAUTHORIZED", res.json().get("error", ""))

    # -------------------------------------------------------------------------
    # TEST 8: Cross-matter document access rejection
    # -------------------------------------------------------------------------
    def test_08_cross_matter_document_access_rejection(self):
        """User authorized for Matter A cannot stream documents belonging to Matter B."""
        headers = {
            "x-matter-id": "MAT-2026-999_ATTACKER",
            "x-user-id": "adversary_lawyer"
        }
        params = {
            "docId": "Balram_Singh_Writ.pdf",
            "matterId": "MAT-2026-001"  # Different matter
        }
        res = requests.get(f"{NEXT_BASE_URL}/api/documents/stream", headers=headers, params=params)
        self.assertEqual(res.status_code, 403)
        self.assertIn("Cross-matter", res.json().get("error", ""))

    # -------------------------------------------------------------------------
    # TEST 9: No public static access to confidential documents
    # -------------------------------------------------------------------------
    def test_09_no_public_static_access_to_confidential_documents(self):
        """Confidential matter PDFs are never stored under public/ web root."""
        public_matters = PUBLIC_DOCS_ROOT / "matters"
        if public_matters.exists():
            files = list(public_matters.glob("**/*"))
            self.assertEqual(len(files), 0, "No files must exist in public/documents/matters/")

        # Scan all public directory files to ensure real_pdf_hash never leaked
        for p in FRONTEND_ROOT.glob("public/**/*"):
            if p.is_file():
                with open(p, "rb") as f:
                    file_sha = hashlib.sha256(f.read()).hexdigest()
                self.assertNotEqual(
                    file_sha,
                    self.real_pdf_hash,
                    f"Confidential file leaked into public web root: {p}"
                )

    # -------------------------------------------------------------------------
    # TEST 10: Successful navigation to correct matter after processing
    # -------------------------------------------------------------------------
    def test_10_successful_navigation_to_matter_workspace(self):
        """Matter record is immediately retrievable via matter workspace API route."""
        files = {"file": ("Balram_Singh_Writ.pdf", self.real_pdf_bytes, "application/pdf")}
        res = requests.post(f"{NEXT_BASE_URL}/api/matters/ingest", files=files, timeout=60)
        matter_id = res.json().get("matterId")

        # Query matter by ID (workspace load route)
        workspace_res = requests.get(f"{NEXT_BASE_URL}/api/matters/{matter_id}")
        self.assertEqual(workspace_res.status_code, 200)
        workspace_data = workspace_res.json()
        self.assertEqual(workspace_data.get("matter", {}).get("id"), matter_id)

    # -------------------------------------------------------------------------
    # TEST 11: Matter and document persistence across reload
    # -------------------------------------------------------------------------
    def test_11_matter_and_document_persistence_across_reload(self):
        """Matter and documents survive simulated server reboot / reload of JSON store."""
        files = {"file": ("Balram_Singh_Writ.pdf", self.real_pdf_bytes, "application/pdf")}
        res = requests.post(f"{NEXT_BASE_URL}/api/matters/ingest", files=files, timeout=60)
        matter_id = res.json().get("matterId")

        # Read JSON file directly from disk (bypassing any in-memory route cache)
        with open(EXTRACTED_MATTERS_PATH, "r", encoding="utf-8") as f:
            matters = json.load(f)

        found = next((m for m in matters if m.get("id") == matter_id), None)
        self.assertIsNotNone(found, f"Matter {matter_id} did not persist to disk!")
        self.assertEqual(len(found.get("documents", [])), 1)
        self.assertEqual(found["documents"][0].get("sha256"), self.real_pdf_hash)

    # -------------------------------------------------------------------------
    # TEST 12: Regression of existing workspace and evidence-verification functionality
    # -------------------------------------------------------------------------
    def test_12_regression_workspace_and_evidence_verification(self):
        """Evidence verification and daemon health remain 100% operational."""
        # 1. Daemon health check
        health_res = requests.get(f"{DAEMON_BASE_URL}/health")
        self.assertEqual(health_res.status_code, 200)
        health_json = health_res.json()
        self.assertEqual(health_json.get("status"), "healthy")
        self.assertTrue(health_json.get("qdrant_connected"))

        # 2. Existing matters list endpoint
        matters_res = requests.get(f"{NEXT_BASE_URL}/api/matters")
        self.assertEqual(matters_res.status_code, 200)
        matters_data = matters_res.json()
        self.assertGreaterEqual(len(matters_data.get("matters", [])), 1)

        # 3. Evidence verify route test
        verify_payload = {
            "documentId": "Dr Balram Singh .pdf",
            "matterId": "PUBLIC_CORPUS",
            "passageText": "Writ Petition (Civil) No. 202 of 2024",
            "reportedPage": 1
        }
        v_res = requests.post(
            f"{NEXT_BASE_URL}/api/evidence/verify",
            json=verify_payload,
            headers={"x-matter-id": "PUBLIC_CORPUS", "authorization": "Bearer test-lawyer-token"}
        )
        self.assertEqual(v_res.status_code, 200, f"Evidence verify failed: {v_res.text}")
        v_json = v_res.json()
        self.assertTrue(v_json.get("success"))


if __name__ == "__main__":
    unittest.main()
