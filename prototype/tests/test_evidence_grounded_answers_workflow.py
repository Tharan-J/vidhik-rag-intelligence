"""
Phase 4 Workflow 3: Evidence-Grounded Legal Answers Comprehensive Test Suite
=============================================================================
Rigorous validation of the Vidhik Evidence-Grounded Legal Answers pipeline:
- Test A: Supported Legal Proposition (NHAI v. Hakeem - Section 34 award modification prohibition)
- Test B: Partial Support and Statutory Qualification (Borse Brothers - Section 37 & Section 5 Limitation restrictions)
- Test C: Insufficient Evidence and Honest Abstention (Negative control on absent patent gene drive doctrine)
- Test D: Contrary and Qualifying Evidence Preservation (Competing High Court / statutory distinctions)
- Test E: Citation Integrity & Coordinate Verification (Verifying passage on authentic physical court PDFs)
- Test F: Judicial-Status Distinctions (Distinguishing judicial holdings from party submissions)
- Test G: Real Application API Integration (Full schema and contract verification via FastAPI TestClient)
"""

import sys
import unittest
from pathlib import Path
from typing import Dict, Any, List

# Ensure prototype root is in PYTHONPATH
PROTOTYPE_ROOT = Path(__file__).resolve().parent.parent
if str(PROTOTYPE_ROOT) not in sys.path:
    sys.path.insert(0, str(PROTOTYPE_ROOT))

from rag.config import load_rag_config
from rag.engine import LegalRAGEngine, LegalRAGResponse
from rag.evidence import EvidenceItem, EvidenceSelector
from rag.generator import QwenGenerator, RawGenerationOutput
from rag.provenance import (
    ProvenanceResolver,
    ClaimWithProvenance,
    CitationAuthority,
    _find_source_pdf,
)
from rag.source_verifier import (
    LegalEvidenceVerifier,
    STATUS_VERIFIED_EXACT,
    STATUS_VERIFIED_NORMALIZED,
    STATUS_COORDINATE_MISMATCH,
    STATUS_PASSAGE_NOT_FOUND,
)
from api.main import create_app
from fastapi.testclient import TestClient


class TestWorkflow3EvidenceGroundedAnswers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_rag_config()
        cls.verifier = LegalEvidenceVerifier()
        cls.generator = QwenGenerator(cls.config.generator)
        cls.engine = LegalRAGEngine(config=cls.config, generator=cls.generator)

        # Independently verified source documents from repository
        cls.hakeem_pdf = _find_source_pdf("SC_2021 INSC 344_2021_5_368_407_EN.pdf")
        cls.borse_pdf = _find_source_pdf("SC_2021 INSC 194_2021_3_193_254_EN.pdf")
        cls.ajab_pdf = _find_source_pdf("HC_7_26_DLHC010427042021.pdf")

        if not cls.hakeem_pdf or not cls.hakeem_pdf.exists():
            raise RuntimeError(f"Hakeem PDF not found: {cls.hakeem_pdf}")
        if not cls.borse_pdf or not cls.borse_pdf.exists():
            raise RuntimeError(f"Borse Brothers PDF not found: {cls.borse_pdf}")

        # Real evidence items constructed from authentic indexed chunks
        cls.hakeem_evidence = EvidenceItem(
            evidence_id="E1",
            document_id="SC_2021 INSC 344_2021_5_368_407_EN.pdf",
            chunk_id="chunk_0001",
            qdrant_point_id="pt_hakeem_001",
            text=(
                "Arbitration and Conciliation Act, 1996: s.34 – Modification of award by court, permissibility – "
                "Held: Power of a court under s.34 of the Act, 1996 to “set aside” an award of an arbitrator would "
                "not include the power to modify such an award – To state that the judicial trend appears to favour "
                "an interpretation that would read into s.34 a power to modify, revise or vary the award would be to "
                "ignore the previous law contained in the 1940 Act."
            ),
            court="Supreme Court of India",
            court_level="Supreme Court",
            case_title="THE PROJECT DIRECTOR, NATIONAL HIGHWAYS NO. 45 E AND 220 NHAI v. M. HAKEEM & ANR.",
            case_number="Civil Appeal No. 2756 of 2021",
            decision_date="2021-07-20",
            year=2021,
            page_start=1,
            page_end=1,
            page_number="1",
            paragraph_id="P001_PAR001",
            sentence_id="S001_01",
            rrf_score=0.98,
            rrf_rank=1,
        )

        cls.borse_evidence = EvidenceItem(
            evidence_id="E2",
            document_id="SC_2021 INSC 194_2021_3_193_254_EN.pdf",
            chunk_id="chunk_0012",
            qdrant_point_id="pt_borse_012",
            text=(
                "Arbitration and Conciliation Act, 1996:s. 37 – Commercial Courts Act, 2015 – Appealable orders – "
                "Limitation period for filing appeal – Condonation of delay in filing appeal u/s. 37 – Held: "
                "Object of speedy disposal is sought to be achieved both under the Arbitration Act and the CC Act, "
                "for appeals filed u/s. 37 of the 1996 Act that are governed by Arts, 116 and 117 of the Limitation Act "
                "or s. 13(1A) of the CC Act – s. 13(1A) of the CC Act lays down a period of limitation of 60 days "
                "uniformly for all appeals that are preferred u/s.37 of the Act – Delay beyond 90 days, 30 days or "
                "60 days, respectively, is to be condoned by way of exception and not by way of rule"
            ),
            court="Supreme Court of India",
            court_level="Supreme Court",
            case_title="GOVERNMENT OF MAHARASHTRA v. M/S BORSE BROTHERS ENGINEERS & CONTRACTORS",
            case_number="2021 INSC 194",
            decision_date="2021-03-19",
            year=2021,
            page_start=1,
            page_end=1,
            page_number="1",
            paragraph_id="SC_PAR001",
            sentence_id="S012_01",
            rrf_score=0.92,
            rrf_rank=2,
        )

        cls.submission_evidence = EvidenceItem(
            evidence_id="E3",
            document_id="SC_2021 INSC 344_2021_5_368_407_EN.pdf",
            chunk_id="chunk_0015",
            qdrant_point_id="pt_hakeem_015",
            text=(
                "The learned Solicitor General argued that, given the object sought to be achieved by the Act, "
                "a speedy procedure was provided by which a challenge to the arbitrator’s award is then made only "
                "under Section 34 of the Arbitration Act, which, as has been held by a catena of judgments, is not "
                "a challenge on the merits of the award. The court’s limited power under the said Section is wholly "
                "unlike the power of an appellate court under the Land Acquisition Act."
            ),
            court="Supreme Court of India",
            court_level="Supreme Court",
            case_title="THE PROJECT DIRECTOR, NATIONAL HIGHWAYS NO. 45 E AND 220 NHAI v. M. HAKEEM & ANR.",
            case_number="Civil Appeal No. 2756 of 2021",
            decision_date="2021-07-20",
            year=2021,
            page_start=10,
            page_end=10,
            page_number="10",
            paragraph_id="P010_PAR002",
            sentence_id="S015_01",
            rrf_score=0.85,
            rrf_rank=3,
        )

    # =========================================================================
    # TEST CATEGORY A: SUPPORTED LEGAL PROPOSITION
    # =========================================================================
    def test_a_supported_legal_proposition_nhai_v_hakeem(self):
        """
        Category A: Real question whose answer is directly supported by a verified passage.
        Proposition: Under Section 34 of the Arbitration Act, the court cannot modify an award.
        """
        raw_claims = [
            {
                "claim": "Under Section 34 of the Arbitration and Conciliation Act, the court has no power to modify an arbitral award and is confined to setting it aside.",
                "evidence_ids": ["E1"],
                "claim_type": "judicial_finding",
                "support_level": "directly_supports",
            }
        ]

        resolved = ProvenanceResolver.resolve(
            raw_claims=raw_claims,
            evidence_items=[self.hakeem_evidence],
            verify_citations=True,
        )

        self.assertEqual(len(resolved), 1)
        c = resolved[0]
        self.assertTrue(c.is_grounded, "Claim must be grounded in evidence")
        self.assertEqual(c.claim_type, "judicial_finding")
        self.assertEqual(c.support_level, "directly_supports")
        self.assertTrue(c.citation_verified, "Citation must be verified against authentic Hakeem PDF")
        self.assertIn(c.verification_status, [STATUS_VERIFIED_EXACT, STATUS_VERIFIED_NORMALIZED])
        self.assertEqual(len(c.authorities), 1)
        self.assertEqual(c.authorities[0].court, "Supreme Court of India")

    # =========================================================================
    # TEST CATEGORY B: PARTIAL SUPPORT & QUALIFIED CLAIMS
    # =========================================================================
    def test_b_partial_support_borse_brothers_limitation(self):
        """
        Category B: Evidence supports only part of the proposition.
        Question: Can court condone delay under Section 37 appeals without limitation?
        Proposition: Section 5 applies, but is qualified as an exception requiring strict sufficient cause.
        """
        raw_claims = [
            {
                "claim": "Section 5 of the Limitation Act applies to Section 37 appeals, but only by way of exception and cannot condone delay indefinitely without proof of sufficient cause.",
                "evidence_ids": ["E2"],
                "claim_type": "judicial_finding",
                "support_level": "directly_supports",
                "qualification": "Applicable strictly as an exception within the 60-day commercial timeline.",
            }
        ]

        resolved = ProvenanceResolver.resolve(
            raw_claims=raw_claims,
            evidence_items=[self.borse_evidence],
            verify_citations=True,
        )

        self.assertEqual(len(resolved), 1)
        c = resolved[0]
        self.assertTrue(c.is_grounded)
        self.assertIsNotNone(c.qualification)
        self.assertIn("60-day", c.qualification)
        self.assertTrue(c.citation_verified, "Borse Brothers citation must resolve to authentic PDF")

    # =========================================================================
    # TEST CATEGORY C: INSUFFICIENT EVIDENCE & HONEST ABSTENTION
    # =========================================================================
    def test_c_insufficient_evidence_fail_closed_abstention(self):
        """
        Category C: Question not adequately answered by the corpus.
        Must produce an honest limitation or abstention without hallucinating legal holdings.
        """
        engine = LegalRAGEngine()

        # Topic completely absent from Indian court corpus
        absent_query = "What is the statutory royalty cap for compulsory licensing of CRISPR gene drive organisms under the Patents Act?"
        
        # When 0 evidence is selected or threshold unmet
        selector = EvidenceSelector(max_evidence=3, min_rrf_score=0.99)
        selected = selector.select([])
        self.assertEqual(len(selected), 0)

        # Engine handles zero evidence gracefully
        t0_response = engine.answer("Unprecedented extraterrestrial salvage doctrine under Space Treaty", top_k=1)
        self.assertIn(t0_response.confidence, ["insufficient_evidence", "partially_supported"])
        self.assertIn("insufficient", t0_response.limitations.lower() + t0_response.answer.lower() + t0_response.confidence.lower())

    # =========================================================================
    # TEST CATEGORY D: CONTRARY OR QUALIFYING EVIDENCE PRESERVATION
    # =========================================================================
    def test_d_contrary_or_qualifying_evidence_preservation(self):
        """
        Category D: Material contrary or qualifying evidence is preserved rather than silently suppressed.
        """
        # Create candidate with qualifying / contrary holding
        qualifying_evidence = EvidenceItem(
            evidence_id="E4",
            document_id="SC_2021 INSC 344_2021_5_368_407_EN.pdf",
            chunk_id="chunk_0020",
            qdrant_point_id="pt_hakeem_020",
            text="Several High Court decisions had previously modified awards under Section 34, but this Court holds those decisions were rendered per incuriam.",
            court="Supreme Court of India",
            court_level="Supreme Court",
            case_title="NHAI v. M. Hakeem",
            case_number="CA 2756/2021",
            decision_date="2021-07-20",
            year=2021,
            page_start=20,
            page_end=21,
            page_number="20-21",
            paragraph_id="P020_PAR001",
            sentence_id="S020_01",
            rrf_score=0.88,
            rrf_rank=4,
        )

        raw_claims = [
            {
                "claim": "Prior High Court decisions that modified arbitral awards under Section 34 were overruled as contrary to the statutory scheme.",
                "evidence_ids": ["E4"],
                "claim_type": "judicial_finding",
                "support_level": "contradicts_or_qualifies",
                "qualification": "Pre-2021 High Court jurisprudence had conflicting interpretations.",
            }
        ]

        resolved = ProvenanceResolver.resolve(
            raw_claims=raw_claims,
            evidence_items=[qualifying_evidence],
            verify_citations=False,
        )

        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0].support_level, "contradicts_or_qualifies")
        self.assertIn("conflicting", resolved[0].qualification.lower())

    # =========================================================================
    # TEST CATEGORY E: CITATION INTEGRITY & COORDINATE VERIFICATION
    # =========================================================================
    def test_e_citation_integrity_and_coordinate_mismatch_detection(self):
        """
        Category E: Verify citation resolves to correct page and detects coordinate mismatches.
        """
        # 1. Exact match on correct page
        manifest = self.verifier.get_or_build_manifest(self.hakeem_pdf)
        p1_text = manifest.pages[0].raw_text
        self.assertGreater(len(p1_text), 50)

        # Snippet from Page 1
        snippet = "THE PROJECT DIRECTOR" if "THE PROJECT DIRECTOR" in p1_text else p1_text[:50].strip()

        res_correct = self.verifier.verify_passage(
            passage_text=snippet,
            reported_page=1,
            pdf_path=self.hakeem_pdf,
            manifest=manifest,
        )
        self.assertIn(res_correct.verification_status, [STATUS_VERIFIED_EXACT, STATUS_VERIFIED_NORMALIZED])
        self.assertEqual(res_correct.verified_page, 1)

        # 2. Coordinate mismatch: claim the Page 1 passage is on Page 35
        res_mismatch = self.verifier.verify_passage(
            passage_text=snippet,
            reported_page=35,
            pdf_path=self.hakeem_pdf,
            manifest=manifest,
        )
        self.assertEqual(res_mismatch.verification_status, STATUS_COORDINATE_MISMATCH)
        self.assertEqual(res_mismatch.verified_page, 1)
        self.assertEqual(res_mismatch.reported_page, 35)

    # =========================================================================
    # TEST CATEGORY F: JUDICIAL-STATUS DISTINCTIONS
    # =========================================================================
    def test_f_judicial_status_distinctions_party_submission_vs_finding(self):
        """
        Category F: Allegations and party arguments must not be conflated with judicial findings.
        """
        raw_claims = [
            {
                "claim": "The court held that Section 34 prohibits modification of arbitral awards.",
                "evidence_ids": ["E1"],
                "claim_type": "judicial_finding",
                "support_level": "directly_supports",
            },
            {
                "claim": "The respondents submitted that Section 34 should be construed broadly to avoid injustice.",
                "evidence_ids": ["E3"],
                "claim_type": "party_submission",
                "support_level": "directly_supports",
            },
        ]

        resolved = ProvenanceResolver.resolve(
            raw_claims=raw_claims,
            evidence_items=[self.hakeem_evidence, self.submission_evidence],
            verify_citations=False,
        )

        self.assertEqual(len(resolved), 2)
        # Verify judicial finding is distinct from party submission
        self.assertEqual(resolved[0].claim_type, "judicial_finding")
        self.assertEqual(resolved[1].claim_type, "party_submission")
        self.assertNotEqual(resolved[0].claim_type, resolved[1].claim_type)

    # =========================================================================
    # TEST CATEGORY G: REAL APPLICATION API INTEGRATION
    # =========================================================================
    def test_g_real_application_api_contract_and_evidence_inspection(self):
        """
        Category G: Execute request through FastAPI app TestClient and verify the full contract.
        """
        app = create_app(engine=self.engine)
        client = TestClient(app)

        response = client.post(
            "/api/v1/query",
            json={
                "query": "Under Section 34 of the Arbitration and Conciliation Act, can the court modify an award?",
                "top_k": 3,
                "max_evidence": 2,
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Contract assertions
        self.assertIn("query", data)
        self.assertIn("answer", data)
        self.assertIn("claims", data)
        self.assertIn("evidence", data)
        self.assertIn("confidence", data)
        self.assertIn("limitations", data)
        self.assertIn("contrary_evidence", data)
        self.assertIn("execution_time_seconds", data)

        self.assertIsInstance(data["claims"], list)
        self.assertIsInstance(data["evidence"], list)
        self.assertGreater(len(data["evidence"]), 0)

        # Inspect evidence contract
        ev0 = data["evidence"][0]
        self.assertIn("evidence_id", ev0)
        self.assertIn("court", ev0)
        self.assertIn("case_title", ev0)
        self.assertIn("document_id", ev0)
        self.assertIn("text", ev0)

        # Inspect claim contract
        if data["claims"]:
            cl0 = data["claims"][0]
            self.assertIn("claim", cl0)
            self.assertIn("evidence_ids", cl0)
            self.assertIn("claim_type", cl0)
            self.assertIn("support_level", cl0)
            self.assertIn("citation_verified", cl0)
            self.assertIn("verification_status", cl0)


if __name__ == "__main__":
    unittest.main()
