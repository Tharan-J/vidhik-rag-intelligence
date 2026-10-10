"""
Unit and Integration Test Suite for Vidhik Legal RAG Engine
===========================================================
Test 1: Evidence conversion from retrieval results.
Test 2: Deterministic Evidence IDs (E1, E2, ...).
Test 3: Context builder preserves provenance landmarks.
Test 4: Prompt contains strict legal grounding rules.
Test 5: Structured Qwen output validation and parsing against schema.
Test 6: Claim -> Evidence -> Authority mapping preservation.
Test 7: End-to-end execution of LegalRAGEngine pipeline.
"""

import sys
import unittest
from pathlib import Path

# Ensure prototype root is in PYTHONPATH
PROTOTYPE_DIR = Path(__file__).resolve().parent.parent
if str(PROTOTYPE_DIR) not in sys.path:
    sys.path.insert(0, str(PROTOTYPE_DIR))

from retrieval.models import HybridRetrievalResult
from rag.config import load_rag_config
from rag.evidence import EvidenceItem, EvidenceSelector
from rag.context import ContextBuilder
from rag.prompt import build_prompts, SYSTEM_LEGAL_GROUNDING_PROMPT
from rag.generator import QwenGenerator, RawGenerationOutput
from rag.provenance import ProvenanceResolver, ClaimWithProvenance, CitationAuthority
from rag.engine import LegalRAGEngine, LegalRAGResponse


class TestVidhikLegalRAG(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_rag_config()

        # Create sample HybridRetrievalResult for deterministic testing
        cls.sample_candidate_1 = HybridRetrievalResult(
            chunk_id="chunk_0015",
            document_id="HC_7_26_DLHC010427042021.pdf",
            qdrant_point_id="dc44ed25-02a8-536d-a856-6f431aa42e0d",
            text="Period of limitation means the period of limitation prescribed for any suit, appeal or application by the Schedule to the Limitation Act.",
            rrf_score=0.0328,
            rrf_rank=1,
            court_level="High Court",
            court="Delhi High Court",
            case_title="DELHI DEVELOPMENT AUTHORITY Vs M/S AJAB SINGH AND CO.",
            case_number="FAO (COMM)/20/2022",
            decision_date="2022-07-29",
            year=2022,
            page_start=18,
            page_end=19,
            paragraph_start="HC_PAR001",
            paragraph_end="HC_PAR001",
            sentence_start="HC_SEN001",
            sentence_end="HC_SEN005",
            dense_score=0.68,
            dense_rank=1,
            bm25_score=38.5,
            bm25_rank=1,
        )
        cls.sample_candidate_2 = HybridRetrievalResult(
            chunk_id="chunk_0031",
            document_id="SC_2021 INSC 194_2021_3_193_254_EN.pdf",
            qdrant_point_id="2ba35fd6-e988-5067-9374-ff6e330216a9",
            text="Section 29 of the Limitation Act relates to savings. Article 116 of the Schedule prescribes the period of limitation for appeals to the High Court as 90 days.",
            rrf_score=0.0304,
            rrf_rank=2,
            court_level="Supreme Court",
            court="Supreme Court of India",
            case_title="GOVT. OF MAHARASHTRA v. M/S BORSE BROTHERS ENGINEERS",
            case_number="2021 INSC 194",
            decision_date="2021-03-19",
            year=2021,
            page_start=30,
            page_end=31,
            paragraph_start="SC_PAR001",
            paragraph_end="SC_PAR001",
            sentence_start="SC_SEN001",
            sentence_end="SC_SEN004",
            dense_score=0.64,
            dense_rank=9,
            bm25_score=38.0,
            bm25_rank=3,
        )

    def test_01_evidence_conversion(self):
        """Test 1: Verify conversion of retrieval candidates into EvidenceItems."""
        selector = EvidenceSelector(max_evidence=5)
        evidence = selector.select([self.sample_candidate_1, self.sample_candidate_2])

        self.assertEqual(len(evidence), 2)
        item = evidence[0]
        self.assertIsInstance(item, EvidenceItem)
        self.assertEqual(item.document_id, "HC_7_26_DLHC010427042021.pdf")
        self.assertEqual(item.court, "Delhi High Court")
        self.assertEqual(item.case_title, "DELHI DEVELOPMENT AUTHORITY Vs M/S AJAB SINGH AND CO.")
        self.assertEqual(item.page_number, "18-19")
        self.assertIn("Limitation Act", item.text)

    def test_02_deterministic_evidence_ids(self):
        """Test 2: Verify Evidence IDs are assigned deterministically as E1, E2, ..."""
        selector = EvidenceSelector(max_evidence=5)
        evidence = selector.select([self.sample_candidate_1, self.sample_candidate_2])

        self.assertEqual(evidence[0].evidence_id, "E1")
        self.assertEqual(evidence[1].evidence_id, "E2")

        # Verify duplicate chunk IDs are safely deduplicated
        evidence_with_dup = selector.select([
            self.sample_candidate_1,
            self.sample_candidate_1,
            self.sample_candidate_2,
        ])
        self.assertEqual(len(evidence_with_dup), 2)
        self.assertEqual(evidence_with_dup[0].evidence_id, "E1")
        self.assertEqual(evidence_with_dup[1].evidence_id, "E2")

    def test_03_context_builder_preserves_provenance(self):
        """Test 3: Verify ContextBuilder produces structured context containing all landmarks."""
        selector = EvidenceSelector(max_evidence=5)
        evidence = selector.select([self.sample_candidate_1, self.sample_candidate_2])

        builder = ContextBuilder(max_tokens=2000)
        bundle = builder.build(
            query="What is the limitation period for appeals?",
            evidence_items=evidence,
        )

        context_str = bundle.formatted_context
        self.assertIn("USER QUESTION:", context_str)
        self.assertIn("[E1]", context_str)
        self.assertIn("Court: Delhi High Court", context_str)
        self.assertIn("Case: DELHI DEVELOPMENT AUTHORITY Vs M/S AJAB SINGH AND CO.", context_str)
        self.assertIn("Page: 18-19", context_str)
        self.assertIn("[E2]", context_str)
        self.assertIn("Court: Supreme Court of India", context_str)
        self.assertIn("Page: 30-31", context_str)
        self.assertEqual(len(bundle.included_evidence), 2)

    def test_04_prompt_contains_grounding_instructions(self):
        """Test 4: Verify prompts enforce strict legal grounding and citation rules."""
        selector = EvidenceSelector(max_evidence=5)
        evidence = selector.select([self.sample_candidate_1])
        builder = ContextBuilder(max_tokens=2000)
        bundle = builder.build(query="Test Question", evidence_items=evidence)

        system_prompt, user_prompt = build_prompts(bundle)

        self.assertIn("CRITICAL GROUNDING RULES", system_prompt)
        self.assertIn("Answer ONLY from the supplied legal evidence", system_prompt)
        self.assertIn("Every substantive legal claim in your response MUST cite one or more evidence IDs", system_prompt)
        self.assertIn("insufficient_evidence", system_prompt)
        self.assertIn('"claims"', system_prompt)
        self.assertIn('"confidence"', system_prompt)
        self.assertIn("[E1]", user_prompt)

    def test_05_structured_output_validation(self):
        """Test 5: Verify Qwen structured output parsing and schema validation."""
        generator = QwenGenerator()

        # Case A: Valid clean JSON
        valid_json = """
        {
          "answer": "Under Article 116 of the Limitation Act, appeals to the High Court must be filed within 90 days.",
          "claims": [
            {
              "claim": "Article 116 prescribes 90 days for High Court appeals.",
              "evidence_ids": ["E2"]
            }
          ],
          "limitations": "Only addresses High Court appeals under standard CPC rules.",
          "confidence": "supported"
        }
        """
        parsed = generator._parse_and_validate_json(valid_json)
        self.assertEqual(parsed["confidence"], "supported")
        self.assertEqual(len(parsed["claims"]), 1)
        self.assertEqual(parsed["claims"][0]["evidence_ids"], ["E2"])

        # Case B: JSON wrapped in markdown codeblocks
        markdown_wrapped = f"```json\n{valid_json}\n```"
        parsed_md = generator._parse_and_validate_json(markdown_wrapped)
        self.assertEqual(parsed_md["confidence"], "supported")
        self.assertEqual(parsed_md["claims"][0]["evidence_ids"], ["E2"])

        # Case C: Malformed recovery
        malformed = "Just plain text answer without JSON."
        parsed_malformed = generator._parse_and_validate_json(malformed)
        self.assertEqual(parsed_malformed["confidence"], "partially_supported")
        self.assertTrue(parsed_malformed["answer"])

    def test_06_claim_to_evidence_provenance_preservation(self):
        """Test 6: Verify Claim -> Evidence -> Authority mapping resolution."""
        selector = EvidenceSelector(max_evidence=5)
        evidence = selector.select([self.sample_candidate_1, self.sample_candidate_2])

        raw_claims = [
            {
                "claim": "Appeals to High Court must be preferred within 90 days.",
                "evidence_ids": ["E2"],
            },
            {
                "claim": "General limitation rules derive from the Schedule to the Limitation Act.",
                "evidence_ids": ["E1"],
            },
        ]

        resolved = ProvenanceResolver.resolve(raw_claims, evidence)
        self.assertEqual(len(resolved), 2)

        # Verify claim 1 resolution
        c1 = resolved[0]
        self.assertTrue(c1.is_grounded)
        self.assertEqual(len(c1.authorities), 1)
        auth1 = c1.authorities[0]
        self.assertEqual(auth1.evidence_id, "E2")
        self.assertEqual(auth1.court, "Supreme Court of India")
        self.assertEqual(auth1.case_title, "GOVT. OF MAHARASHTRA v. M/S BORSE BROTHERS ENGINEERS")
        self.assertEqual(auth1.page_number, "30-31")

        # Verify claim 2 resolution
        c2 = resolved[1]
        self.assertTrue(c2.is_grounded)
        self.assertEqual(c2.authorities[0].court, "Delhi High Court")
        self.assertEqual(c2.authorities[0].page_number, "18-19")

    def test_07_end_to_end_rag_execution(self):
        """Test 7: End-to-end execution of LegalRAGEngine with live retrieval and Qwen."""
        engine = LegalRAGEngine()
        response = engine.answer(
            query="What is the limitation period for filing an appeal?",
            top_k=5,
            max_evidence=3,
        )

        self.assertIsInstance(response, LegalRAGResponse)
        self.assertTrue(response.answer, "Response must contain answer text")
        self.assertIn(response.confidence, ["supported", "partially_supported", "insufficient_evidence"])
        self.assertGreater(response.evidence_count, 0, "Should include retrieved evidence")
        self.assertGreater(len(response.evidence), 0)

        # Check evidence structure
        ev0 = response.evidence[0]
        self.assertIn("evidence_id", ev0)
        self.assertIn("court", ev0)
        self.assertIn("case_title", ev0)
        self.assertIn("text", ev0)

        # Check claims structure
        for claim in response.claims:
            self.assertIsInstance(claim, ClaimWithProvenance)
            self.assertTrue(claim.claim)


if __name__ == "__main__":
    unittest.main()
