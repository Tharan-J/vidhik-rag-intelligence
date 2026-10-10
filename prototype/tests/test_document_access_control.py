"""
Automated Security & Access Control Test Suite: Confidential Document Storage
=============================================================================
Tests:
1. Unauthenticated access blocked.
2. Cross-matter document access strictly prohibited (Tenant/Matter isolation).
3. Path traversal attacks blocked (Directory traversal defense).
4. Missing / deleted document detection.
5. Valid authorized access succeeds with cryptographic hash verification.
6. Public static web root inspection: Confirms no uploaded PDFs exist under public/.
"""

import os
import sys
import shutil
import hashlib
import unittest
from pathlib import Path

# Add prototype root
PROTOTYPE_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = PROTOTYPE_ROOT.parent

# Test directories
PRIVATE_STORAGE_ROOT = WORKSPACE_ROOT / "frontend" / "storage" / "documents" / "matters"
PUBLIC_DOCS_ROOT = WORKSPACE_ROOT / "frontend" / "public" / "documents"


def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class DocumentStorageSecurityEngine:
    """
    Python mirror of frontend/src/lib/server/documentStorage.ts
    to execute deterministic unit tests in the backend test environment.
    """

    def __init__(self, private_root: Path):
        self.private_root = private_root
        self.private_root.mkdir(parents=True, exist_ok=True)

    def sanitize_identifier(self, input_str: str) -> str:
        if not input_str:
            return ""
        clean = (
            input_str.replace("\0", "")
            .replace("/", "_")
            .replace("\\", "_")
            .replace("..", "_")
            .strip()
        )
        return clean

    def save_uploaded_document(self, buffer: bytes, matter_id: str, doc_name: str) -> dict:
        safe_matter = self.sanitize_identifier(matter_id)
        if not safe_matter:
            raise ValueError("Invalid matter ID")
        safe_name = self.sanitize_identifier(Path(doc_name).name)

        matter_dir = (self.private_root / safe_matter).resolve()
        matter_dir.mkdir(parents=True, exist_ok=True)

        abs_path = (matter_dir / safe_name).resolve()
        if not str(abs_path).startswith(str(matter_dir)):
            raise PermissionError("Path traversal violation")

        with open(abs_path, "wb") as f:
            f.write(buffer)

        return {
            "absolute_path": str(abs_path),
            "storage_path": f"storage/documents/matters/{safe_matter}/{safe_name}",
            "sha256": compute_sha256(buffer),
            "matter_id": safe_matter,
            "document_id": safe_name,
        }

    def resolve_authorized_document(
        self,
        document_id: str,
        is_authenticated: bool,
        user_matter_id: str = None,
        requested_matter_id: str = None,
    ) -> dict:
        # 1. Unauthenticated check
        if not is_authenticated:
            return {"success": False, "error": "UNAUTHENTICATED", "details": "Authentication required."}

        effective_matter = requested_matter_id or user_matter_id

        # 2. Cross-matter access check
        if user_matter_id and effective_matter and user_matter_id != effective_matter:
            return {
                "success": False,
                "error": "ACCESS_DENIED_CROSS_MATTER",
                "details": f"User in matter {user_matter_id} cannot access matter {effective_matter}.",
            }

        # 3. Path traversal defense
        if ".." in document_id or "/" in document_id or "\\" in document_id:
            safe_doc = self.sanitize_identifier(Path(document_id).name)
        else:
            safe_doc = self.sanitize_identifier(document_id)

        safe_matter = self.sanitize_identifier(effective_matter or "")
        if not safe_matter:
            return {"success": False, "error": "DOCUMENT_NOT_FOUND", "details": "No matter specified."}

        matter_dir = (self.private_root / safe_matter).resolve()
        target_path = (matter_dir / safe_doc).resolve()

        if not str(target_path).startswith(str(matter_dir)):
            return {
                "success": False,
                "error": "ACCESS_DENIED_PATH_TRAVERSAL",
                "details": "Path traversal detected.",
            }

        if not target_path.exists():
            return {
                "success": False,
                "error": "DOCUMENT_NOT_FOUND",
                "details": f"Document not found in {safe_matter}.",
            }

        with open(target_path, "rb") as f:
            data = f.read()

        return {
            "success": True,
            "authorized_path": str(target_path),
            "sha256": compute_sha256(data),
            "document_id": safe_doc,
            "matter_id": safe_matter,
        }


class TestDocumentStorageSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = DocumentStorageSecurityEngine(PRIVATE_STORAGE_ROOT)
        cls.matter_alpha = "MAT_ALPHA_2024"
        cls.matter_beta = "MAT_BETA_2024"

        # Create sample confidential PDF content
        cls.sample_pdf_bytes = b"%PDF-1.4\n%Confidential Court Petition Content\n%%EOF"
        cls.doc_alpha = cls.engine.save_uploaded_document(
            buffer=cls.sample_pdf_bytes,
            matter_id=cls.matter_alpha,
            doc_name="Petition_Alpha.pdf",
        )

    def test_01_unauthenticated_access_denied(self):
        """Test 1: Unauthenticated request is rejected immediately."""
        res = self.engine.resolve_authorized_document(
            document_id="Petition_Alpha.pdf",
            is_authenticated=False,
            user_matter_id=self.matter_alpha,
        )
        self.assertFalse(res["success"])
        self.assertEqual(res["error"], "UNAUTHENTICATED")

    def test_02_cross_matter_access_strictly_blocked(self):
        """Test 2: User authorized for Matter Beta cannot access Matter Alpha document."""
        res = self.engine.resolve_authorized_document(
            document_id="Petition_Alpha.pdf",
            is_authenticated=True,
            user_matter_id=self.matter_beta,  # User belongs to Beta
            requested_matter_id=self.matter_alpha,  # Tries to access Alpha
        )
        self.assertFalse(res["success"])
        self.assertEqual(res["error"], "ACCESS_DENIED_CROSS_MATTER")
        self.assertIn("cannot access matter", res["details"])

    def test_03_path_traversal_attack_blocked(self):
        """Test 3: Attacker supplying directory traversal sequences is blocked."""
        # Traversal attempt: ../../etc/passwd
        res = self.engine.resolve_authorized_document(
            document_id="../../etc/passwd",
            is_authenticated=True,
            user_matter_id=self.matter_alpha,
        )
        # Should be sanitized to a harmless filename inside matter or blocked
        self.assertFalse(res["success"])
        self.assertIn(res["error"], ["DOCUMENT_NOT_FOUND", "ACCESS_DENIED_PATH_TRAVERSAL"])

    def test_04_deleted_or_missing_document_returns_not_found(self):
        """Test 4: Non-existent document returns DOCUMENT_NOT_FOUND."""
        res = self.engine.resolve_authorized_document(
            document_id="NonExistent_Brief_999.pdf",
            is_authenticated=True,
            user_matter_id=self.matter_alpha,
        )
        self.assertFalse(res["success"])
        self.assertEqual(res["error"], "DOCUMENT_NOT_FOUND")

    def test_05_valid_authorized_access_succeeds(self):
        """Test 5: Authorized user in same matter accesses document with hash match."""
        res = self.engine.resolve_authorized_document(
            document_id="Petition_Alpha.pdf",
            is_authenticated=True,
            user_matter_id=self.matter_alpha,
            requested_matter_id=self.matter_alpha,
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["matter_id"], self.matter_alpha)
        self.assertEqual(res["document_id"], "Petition_Alpha.pdf")
        self.assertEqual(res["sha256"], self.doc_alpha["sha256"])
        self.assertTrue(os.path.exists(res["authorized_path"]))

    def test_06_zero_confidential_pdfs_in_public_web_root(self):
        """Test 6: Verify that NO uploaded confidential matter PDFs reside under public/."""
        # Ensure public/documents/matters directory does NOT exist or has 0 confidential files
        public_matters = PUBLIC_DOCS_ROOT / "matters"
        if public_matters.exists():
            files = list(public_matters.glob("**/*"))
            self.assertEqual(len(files), 0, "No files must exist in public/documents/matters/!")

        # Scan all files in public/documents/ and verify none match the confidential hash
        for p in PUBLIC_DOCS_ROOT.glob("**/*"):
            if p.is_file():
                with open(p, "rb") as f:
                    file_sha = hashlib.sha256(f.read()).hexdigest()
                self.assertNotEqual(
                    file_sha,
                    self.doc_alpha["sha256"],
                    f"Confidential file leaked into public web root: {p}",
                )


if __name__ == "__main__":
    unittest.main()
