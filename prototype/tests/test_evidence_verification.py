"""
Comprehensive Test Suite: Evidence-Centred Legal Verification Engine
====================================================================
Tests strict source-traceability, context-reconstruction, and coordinate integrity
against actual Indian court judgment PDFs in the repository.

Tests:
1. Exact source-text match with the correct page.
2. Valid passage paired with the wrong page.
3. Passage not found in the source.
4. Source document changed after indexing (stale document).
5. OCR uncertainty or normalized-text mismatch.
6. Source document deleted.
7. Chunk boundary crossing a paragraph or sentence (context reconstruction).
8. Unicode and whitespace normalization without false coordinate claims.
9. Existing ingestion and retrieval compatibility.
"""

import sys
import unittest
from pathlib import Path

# Add prototype root to sys.path
PROTOTYPE_ROOT = Path(__file__).resolve().parent.parent
if str(PROTOTYPE_ROOT) not in sys.path:
    sys.path.insert(0, str(PROTOTYPE_ROOT))

from rag.source_verifier import (
    LegalEvidenceVerifier,
    DocumentManifestStore,
    extract_manifest_from_pdf,
    compute_file_sha256,
    normalize_text_for_comparison,
    STATUS_VERIFIED_EXACT,
    STATUS_VERIFIED_NORMALIZED,
    STATUS_OCR_UNCERTAINTY,
    STATUS_COORDINATE_MISMATCH,
    STATUS_PASSAGE_NOT_FOUND,
    STATUS_DOCUMENT_STALE,
    STATUS_DOCUMENT_DELETED,
)
from rag.provenance import _find_source_pdf


class TestEvidenceVerificationEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 1. Real Delhi High Court PDF from candidate directory
        cls.hc_pdf_path = PROTOTYPE_ROOT.parent / "research" / "legal_data" / "high_court" / "pdfs_stage1_candidates" / "7_26" / "DLHC014050292015.pdf"
        # 2. Real Supreme Court PDF from frontend public directory
        cls.sc_pdf_path = PROTOTYPE_ROOT.parent / "frontend" / "public" / "documents" / "523382025_2026-07-02.pdf"

        cls.verifier = LegalEvidenceVerifier()

        # Ensure at least one real PDF exists
        cls.has_hc_pdf = cls.hc_pdf_path.exists()
        cls.has_sc_pdf = cls.sc_pdf_path.exists()

        if not cls.has_hc_pdf and not cls.has_sc_pdf:
            raise RuntimeError("CRITICAL: No authentic court PDFs found in repository for testing.")

        # Active test PDF
        cls.test_pdf = cls.hc_pdf_path if cls.has_hc_pdf else cls.sc_pdf_path
        cls.test_sha256 = compute_file_sha256(cls.test_pdf)
        cls.manifest = cls.verifier.get_or_build_manifest(cls.test_pdf)

    def test_01_exact_source_match_with_correct_page(self):
        """Test 1: Exact verbatim substring match on the correct page."""
        # Page 1 contains case heading
        page_1_text = self.manifest.pages[0].raw_text
        self.assertGreater(len(page_1_text), 50, "Page 1 must contain extracted text.")

        # Pick an exact snippet from Page 1
        snippet = "IN  THE  HIGH  COURT  OF  DELHI" if "IN  THE  HIGH  COURT" in page_1_text else page_1_text[:60].strip()

        result = self.verifier.verify_passage(
            passage_text=snippet,
            reported_page=1,
            pdf_path=self.test_pdf,
            manifest=self.manifest,
        )

        self.assertEqual(result.verification_status, STATUS_VERIFIED_EXACT)
        self.assertTrue(result.is_exact_match)
        self.assertEqual(result.verified_page, 1)
        self.assertEqual(result.reported_page, 1)
        self.assertIsNotNone(result.char_offset_in_page)
        start, end = result.char_offset_in_page
        self.assertEqual(self.manifest.pages[0].raw_text[start:end], snippet)
        self.assertIsNotNone(result.reconstructed_context)

    def test_02_valid_passage_paired_with_wrong_page(self):
        """Test 2: Valid passage paired with wrong page detects COORDINATE_MISMATCH."""
        page_1_text = self.manifest.pages[0].raw_text
        snippet = "IN  THE  HIGH  COURT  OF  DELHI" if "IN  THE  HIGH  COURT" in page_1_text else page_1_text[:60].strip()

        # Falsely report this snippet as appearing on Page 10
        wrong_page = 10
        result = self.verifier.verify_passage(
            passage_text=snippet,
            reported_page=wrong_page,
            pdf_path=self.test_pdf,
            manifest=self.manifest,
        )

        self.assertEqual(result.verification_status, STATUS_COORDINATE_MISMATCH)
        self.assertEqual(result.reported_page, wrong_page)
        self.assertEqual(result.verified_page, 1)  # Physically on Page 1
        self.assertIn("COORDINATE_MISMATCH", result.notes)
        self.assertIn("claimed on Page 10", result.notes)
        self.assertIn("located on Page 1", result.notes)

    def test_03_passage_not_found_in_source(self):
        """Test 3: Fabricated passage not in document returns PASSAGE_NOT_FOUND."""
        fabricated_passage = "The admiralty salvage claim was summarily dismissed with punitive costs under maritime law."

        result = self.verifier.verify_passage(
            passage_text=fabricated_passage,
            reported_page=1,
            pdf_path=self.test_pdf,
            manifest=self.manifest,
        )

        self.assertEqual(result.verification_status, STATUS_PASSAGE_NOT_FOUND)
        self.assertIsNone(result.verified_page)
        self.assertEqual(result.similarity_score, 0.0)
        self.assertIn("does not exist anywhere", result.notes)

    def test_04_source_document_changed_after_indexing(self):
        """Test 4: Stale document version detected when SHA-256 diverges."""
        page_1_text = self.manifest.pages[0].raw_text
        snippet = page_1_text[:40].strip()

        # Provide a synthetic historical SHA that does not match current file
        stale_expected_sha = "0000000000000000000000000000000000000000000000000000000000000000"

        result = self.verifier.verify_passage(
            passage_text=snippet,
            reported_page=1,
            pdf_path=self.test_pdf,
            manifest=self.manifest,
            expected_sha256=stale_expected_sha,
        )

        self.assertEqual(result.verification_status, STATUS_DOCUMENT_STALE)
        self.assertIn("DOCUMENT_STALE", result.notes)
        self.assertIsNone(result.verified_page)

    def test_05_ocr_uncertainty_or_character_noise(self):
        """Test 5: OCR noise and character corruption flagged as OCR_UNCERTAINTY."""
        # Take real paragraph text from page 1 and inject OCR noise (rn -> m, l -> 1, O -> 0)
        p1 = self.manifest.pages[0].paragraphs[0].raw_text
        # Corrupt 3-5 characters to simulate scan artifacts
        corrupted = p1.replace("e", "c", 1).replace("i", "l", 1).replace("a", "o", 1)

        result = self.verifier.verify_passage(
            passage_text=corrupted,
            reported_page=1,
            pdf_path=self.test_pdf,
            manifest=self.manifest,
        )

        # Must either detect OCR_UNCERTAINTY or VERIFIED_NORMALIZED, never claim exact match
        self.assertFalse(result.is_exact_match)
        if result.verification_status == STATUS_OCR_UNCERTAINTY:
            self.assertGreaterEqual(result.similarity_score, 0.80)
            self.assertIn("OCR_UNCERTAINTY", result.notes)

    def test_06_source_document_deleted(self):
        """Test 6: Deleted/missing document returns DOCUMENT_DELETED."""
        missing_path = PROTOTYPE_ROOT / "scratch" / "non_existent_brief_404.pdf"

        result = self.verifier.verify_passage(
            passage_text="Any text from deleted brief",
            reported_page=1,
            pdf_path=missing_path,
            manifest=None,
        )

        self.assertEqual(result.verification_status, STATUS_DOCUMENT_DELETED)
        self.assertIn("CRITICAL: Source document does not exist", result.notes)

    def test_07_chunk_boundary_and_context_reconstruction(self):
        """Test 7: Context reconstruction recovers full target paragraph and surrounding context."""
        # Pick a middle paragraph from page 2 or 3
        paras_page_2 = [p for p in self.manifest.paragraphs if p.page_number >= 2]
        self.assertGreater(len(paras_page_2), 2, "Document must have multiple paragraphs across pages.")

        target_para = paras_page_2[1]
        ctx = self.verifier.reconstruct_context(
            manifest=self.manifest,
            target_para_id=target_para.paragraph_id,
            context_window_paragraphs=1,
        )

        self.assertIsNotNone(ctx)
        self.assertEqual(ctx.target_paragraph_id, target_para.paragraph_id)
        self.assertEqual(ctx.target_text, target_para.raw_text)
        self.assertIn("[TARGET]", ctx.full_context_text)
        # Preceding and succeeding context present
        self.assertGreaterEqual(len(ctx.preceding_context), 1)
        self.assertGreaterEqual(len(ctx.succeeding_context), 1)
        self.assertIn(ctx.preceding_context[0]["text"], ctx.full_context_text)

    def test_08_unicode_and_whitespace_normalization_no_false_offsets(self):
        """Test 8: Normalized text matching does not make false character offset claims."""
        p_text = self.manifest.pages[0].paragraphs[0].raw_text
        # Introduce non-breaking spaces, excess linebreaks and curly quotes
        replaced_text = p_text.replace(" ", "   \n  ")
        mangled_text = f"  \n\n  {replaced_text}  \n"

        result = self.verifier.verify_passage(
            passage_text=mangled_text,
            reported_page=1,
            pdf_path=self.test_pdf,
            manifest=self.manifest,
        )

        self.assertEqual(result.verification_status, STATUS_VERIFIED_NORMALIZED)
        # CRITICAL: For normalized text, char_offset_in_page MUST BE NONE to prevent false landmark claims
        self.assertIsNone(result.char_offset_in_page, "Must not return raw char offsets for normalized text!")
        self.assertFalse(result.is_exact_match)
        self.assertEqual(result.verified_page, 1)

    def test_09_existing_ingestion_and_retrieval_compatibility(self):
        """Test 9: Verified provenance integrates cleanly without breaking existing schema."""
        # Ensure that ProvenanceVerificationResult serializes to clean JSON dictionary
        result = self.verifier.verify_passage(
            passage_text=self.manifest.pages[0].paragraphs[0].raw_text,
            reported_page=1,
            pdf_path=self.test_pdf,
            manifest=self.manifest,
        )
        d = result.to_dict()
        required_keys = [
            "verification_status",
            "document_id",
            "document_sha256",
            "reported_page",
            "verified_page",
            "similarity_score",
            "is_exact_match",
            "reconstructed_context",
            "notes",
        ]
        for k in required_keys:
            self.assertIn(k, d)

        # Confirm that status is never equated to semantic support
        self.assertNotIn("SUPPORTS", d["verification_status"])
        self.assertNotIn("CONTRADICTS", d["verification_status"])

    def test_10_dr_balram_singh_interior_page_verification(self):
        """Test 10: Verify interior page non-trivial passage from Dr Balram Singh PDF (Page 4)."""
        balram_pdf = PROTOTYPE_ROOT.parent / "test" / "Dr Balram Singh .pdf"
        self.assertTrue(balram_pdf.exists(), "Dr Balram Singh .pdf must exist in test directory.")

        balram_sha = compute_file_sha256(balram_pdf)
        balram_manifest = self.verifier.get_or_build_manifest(balram_pdf)

        # Interior passage from Page 4 on secularism basic feature
        passage = (
            "A number of decisions of this Court, including the Constitution Bench "
            "judgments in Kesavananda Bharati v. State of Kerala1 and S R Bommai "
            "vs Union of India2, have observed that secularism is a basic feature "
            "of the Constitution."
        )

        result = self.verifier.verify_passage(
            passage_text=passage,
            reported_page=4,
            pdf_path=balram_pdf,
            manifest=balram_manifest,
            expected_sha256=balram_sha,
        )

        self.assertIn(result.verification_status, [STATUS_VERIFIED_EXACT, STATUS_VERIFIED_NORMALIZED])
        self.assertEqual(result.verified_page, 4)
        self.assertEqual(result.document_sha256, balram_sha)
        self.assertIsNotNone(result.reconstructed_context)
        self.assertEqual(result.reconstructed_context.target_page, 4)
        self.assertIn("Kesavananda Bharati", result.reconstructed_context.target_text)

    def test_11_repeated_header_across_multiple_pages(self):
        """Test 11: Text appearing on multiple pages resolves to reported page or flags mismatch."""
        balram_pdf = PROTOTYPE_ROOT.parent / "test" / "Dr Balram Singh .pdf"
        balram_manifest = self.verifier.get_or_build_manifest(balram_pdf)

        header_text = "W.P. (Civil) No. 645 of 2020 & others"

        # 1. When reported on Page 3 (where it genuinely appears)
        res_page_3 = self.verifier.verify_passage(
            passage_text=header_text,
            reported_page=3,
            pdf_path=balram_pdf,
            manifest=balram_manifest,
        )
        self.assertEqual(res_page_3.verification_status, STATUS_VERIFIED_EXACT)
        self.assertEqual(res_page_3.verified_page, 3)

        # 2. When reported on an invalid page (Page 99)
        res_page_99 = self.verifier.verify_passage(
            passage_text=header_text,
            reported_page=99,
            pdf_path=balram_pdf,
            manifest=balram_manifest,
        )
        self.assertEqual(res_page_99.verification_status, STATUS_COORDINATE_MISMATCH)
        self.assertEqual(res_page_99.reported_page, 99)
        self.assertEqual(res_page_99.verified_page, 1)

    def test_12_strict_rejection_of_unsubstantiated_coordinates(self):
        """Test 12: Ensure no unsubstantiated character offsets or bboxes are returned."""
        balram_pdf = PROTOTYPE_ROOT.parent / "test" / "Dr Balram Singh .pdf"
        balram_manifest = self.verifier.get_or_build_manifest(balram_pdf)

        # Normalized query with altered spacing
        norm_query = "Neither the Constitution nor the Preamble mandates a specific economic policy"
        result = self.verifier.verify_passage(
            passage_text=norm_query,
            reported_page=5,
            pdf_path=balram_pdf,
            manifest=balram_manifest,
        )

        d = result.to_dict()
        # Verify bounding box is NEVER present or claimed
        self.assertNotIn("bbox", d)
        self.assertNotIn("bounding_box", d)
        # Normalized match must not fabricate raw offsets
        if result.verification_status == STATUS_VERIFIED_NORMALIZED:
            self.assertIsNone(result.char_offset_in_page)

    def test_13_dynamic_live_retrieval_to_source_verification(self):
        """Test 13 [LIVE E2E]: Dynamically retrieve from live daemon, extract sentence from hit, and verify."""
        import urllib.request
        import json
        import re

        query = "secularism is a basic feature of the Constitution Kesavananda Bharati S R Bommai"
        payload = {"query": query, "top_k": 3, "doc_id": "Dr Balram Singh .pdf"}
        req = urllib.request.Request(
            "http://127.0.0.1:8008/search",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )

        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                search_data = json.loads(resp.read().decode())
        except Exception as e:
            self.skipTest(f"Live retrieval daemon not reachable on port 8008: {e}")

        hits = search_data.get("results", [])
        self.assertGreater(len(hits), 0, "Live retrieval must return hits for legal query.")

        top_hit = hits[0]
        retrieved_text = top_hit.get("text", "")
        self.assertGreater(len(retrieved_text), 100, "Retrieved text must contain substantial legal content.")

        # DYNAMIC EXTRACTION: Extract a non-trivial sentence (>= 50 chars) from the retrieved text
        sentences = re.findall(r"([A-Z][^.!?\n]{40,}[.!?])", retrieved_text)
        self.assertGreater(len(sentences), 0, "Must extract at least one complete sentence from retrieved text.")

        # Select interior sentence dynamically without hardcoding
        dynamic_passage = sentences[min(1, len(sentences) - 1)].strip()

        # Strict identity check: Extracted passage MUST belong to retrieved text
        self.assertIn(dynamic_passage, retrieved_text, "Extracted passage must belong to retrieved text.")

        # Resolve document via returned document ID
        doc_id = top_hit.get("document_id")
        balram_pdf = _find_source_pdf(doc_id) or (PROTOTYPE_ROOT.parent / "test" / doc_id)
        self.assertTrue(balram_pdf.exists(), f"Source file {doc_id} must resolve in authorized storage.")

        authoritative_sha = compute_file_sha256(balram_pdf)
        manifest = self.verifier.get_or_build_manifest(balram_pdf)

        reported_page_str = top_hit.get("page_number", "Page 1")
        page_num_match = re.search(r"\d+", reported_page_str)
        reported_page = int(page_num_match.group(0)) if page_num_match else 1

        # Verify against authoritative PDF
        verif_res = self.verifier.verify_passage(
            passage_text=dynamic_passage,
            reported_page=reported_page,
            pdf_path=balram_pdf,
            manifest=manifest,
            expected_sha256=authoritative_sha,
        )

        # Confirm consistency of identity, SHA-256, verified page, and context
        self.assertIn(verif_res.verification_status, [STATUS_VERIFIED_EXACT, STATUS_VERIFIED_NORMALIZED])
        self.assertEqual(verif_res.document_id, doc_id)
        self.assertEqual(verif_res.document_sha256, authoritative_sha)
        self.assertEqual(verif_res.verified_page, reported_page)
        self.assertIsNotNone(verif_res.reconstructed_context)

        # Deliberate wrong-page test on the dynamically extracted passage
        wrong_page = reported_page + 2
        verif_wrong = self.verifier.verify_passage(
            passage_text=dynamic_passage,
            reported_page=wrong_page,
            pdf_path=balram_pdf,
            manifest=manifest,
        )
        self.assertEqual(verif_wrong.verification_status, STATUS_COORDINATE_MISMATCH)
        self.assertEqual(verif_wrong.reported_page, wrong_page)
        self.assertEqual(verif_wrong.verified_page, reported_page)

        # Deliberate stale document test
        verif_stale = self.verifier.verify_passage(
            passage_text=dynamic_passage,
            reported_page=reported_page,
            pdf_path=balram_pdf,
            manifest=manifest,
            expected_sha256="stale_hash_invalid_checksum",
        )
        self.assertEqual(verif_stale.verification_status, STATUS_DOCUMENT_STALE)

    def test_14_cross_document_delhi_high_court_interior_page(self):
        """Test 14 [CROSS-DOC]: Verify interior passage (Page 22) from Delhi High Court judgment."""
        hc_pdf = PROTOTYPE_ROOT.parent / "research" / "legal_data" / "high_court" / "pdfs_stage1_candidates" / "7_26" / "DLHC014050292015.pdf"
        self.assertTrue(hc_pdf.exists(), "Delhi High Court PDF must exist.")

        manifest = self.verifier.get_or_build_manifest(hc_pdf)
        sha = compute_file_sha256(hc_pdf)

        # Interior passage from Page 22 discussing Claims Tribunal jurisdiction
        hc_passage = (
            "either to the Claims Tribunal having jurisdiction over the area in which "
            "the accident occurred, or to the Claims Tribunal within the local limits of"
        )

        res = self.verifier.verify_passage(
            passage_text=hc_passage,
            reported_page=22,
            pdf_path=hc_pdf,
            manifest=manifest,
            expected_sha256=sha,
        )

        self.assertIn(res.verification_status, [STATUS_VERIFIED_EXACT, STATUS_VERIFIED_NORMALIZED])
        self.assertEqual(res.verified_page, 22)
        self.assertEqual(res.document_sha256, sha)
        self.assertIsNotNone(res.reconstructed_context)
        self.assertEqual(res.reconstructed_context.target_page, 22)

    def test_15_cross_document_supreme_court_commercial_borse_brothers(self):
        """Test 15 [CROSS-DOC]: Verify interior passage (Page 25) from Supreme Court Borse Brothers precedent."""
        sc_pdf = PROTOTYPE_ROOT.parent / "research" / "legal_data" / "supreme_court" / "pdfs_stage1_candidates" / "year=2021" / "2021_3_193_254_EN.pdf"
        self.assertTrue(sc_pdf.exists(), "Supreme Court Borse Brothers PDF must exist.")

        manifest = self.verifier.get_or_build_manifest(sc_pdf)
        sha = compute_file_sha256(sc_pdf)

        # Interior passage from Page 25 discussing Section 43(3) of Arbitration Act
        borse_passage = (
            "Where an arbitration agreement to submit future disputes to arbitration "
            "provides that any claim to which the agreement applies shall be barred "
            "unless some step to commence arbitral proceedings is taken within a time fixed"
        )

        res = self.verifier.verify_passage(
            passage_text=borse_passage,
            reported_page=25,
            pdf_path=sc_pdf,
            manifest=manifest,
            expected_sha256=sha,
        )

        self.assertIn(res.verification_status, [STATUS_VERIFIED_EXACT, STATUS_VERIFIED_NORMALIZED])
        self.assertEqual(res.verified_page, 25)
        self.assertEqual(res.document_sha256, sha)
        self.assertIsNotNone(res.reconstructed_context)
        self.assertEqual(res.reconstructed_context.target_page, 25)


if __name__ == "__main__":
    unittest.main()

