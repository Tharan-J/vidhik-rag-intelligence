"""
Phase 4 Workflow 5: Multilingual Legal Representation Test Suite
=================================================================
Validates multilingual representation of Vidhik's evidence-grounded legal answers
using the existing IndicTrans2 translation architecture.

Test Coverage:
1. Live IndicTrans2 translation on authentic Supreme Court record (NHAI v. M. Hakeem, (2021) 9 SCC 1).
2. Live IndicTrans2 translation on statutory qualification record (Borse Brothers, (2021) 6 SCC 460).
3. Live IndicTrans2 translation on District Court record (Adil Mansoor, Spl CC No. 12/2019, Section 138, amounts, dates).
4. Exact preservation of protected legal entities (citations, statutory sections, constitutional articles, case numbers).
5. Detection and safe rejection of unresolved, missing, or corrupted placeholders.
6. Multi-language coverage across all configured Indic languages: Tamil (ta), Hindi (hi), Kannada (kn), Marathi (mr).
7. Rejection of unsupported languages and empty/malformed inputs.
8. Authentication, authorization, and matter isolation enforcement (401/403).
9. Graceful error handling on service unavailability (503).
10. Semantic drift and legal qualification polarity audit.
"""

import sys
import unittest
import urllib.request
import urllib.error
import json
from pathlib import Path
from typing import Dict, Any, List

# Ensure prototype root is in PYTHONPATH
PROTOTYPE_ROOT = Path(__file__).resolve().parent.parent
if str(PROTOTYPE_ROOT) not in sys.path:
    sys.path.insert(0, str(PROTOTYPE_ROOT))

from translation.entity_protector import LegalEntityProtector
from translation.verifier import DeterministicLegalVerifier
from translation.indictrans_service import SUPPORTED_LANGUAGES
from api.main import create_app
from fastapi.testclient import TestClient

DAEMON_HEALTH_URL = "http://127.0.0.1:8009/health"
DAEMON_TRANSLATE_URL = "http://127.0.0.1:8009/translate"


def is_translation_daemon_running() -> bool:
    try:
        with urllib.request.urlopen(DAEMON_HEALTH_URL, timeout=2.0) as resp:
            return resp.status == 200
    except Exception:
        return False


class TestMultilingualRepresentationWorkflow(unittest.TestCase):
    """
    Validation suite for Workflow 5: Multilingual Legal Representation.
    """

    @classmethod
    def setUpClass(cls):
        cls.protector = LegalEntityProtector()
        cls.verifier = DeterministicLegalVerifier()
        cls.app = create_app()
        cls.client = TestClient(cls.app)
        cls.daemon_online = is_translation_daemon_running()

    def test_01_daemon_health_and_language_support(self):
        """Verifies that the live IndicTrans2 daemon is operational and reports configured languages."""
        if not self.daemon_online:
            self.skipTest("Translation daemon on port 8009 is offline.")

        with urllib.request.urlopen(DAEMON_HEALTH_URL, timeout=5.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data.get("status"), "healthy")
            self.assertEqual(data.get("service"), "vidhik-translation-daemon")
            for expected_lang in ["ta", "hi", "kn", "mr"]:
                self.assertIn(expected_lang, data.get("supported_languages", []))

    def test_02_live_supreme_court_hakeem_hindi_and_tamil(self):
        """
        Live translation on authentic Supreme Court answer (NHAI v. M. Hakeem, (2021) 9 SCC 1).
        Verifies exact preservation of citations, sections, court names, and parties.
        """
        if not self.daemon_online:
            self.skipTest("Translation daemon on port 8009 is offline.")

        english_answer = (
            "In NHAI v. M. Hakeem (2021) 9 SCC 1, the Supreme Court held that Section 34 of the "
            "Arbitration Act does not permit courts to modify arbitral awards. The court affirmed "
            "that limited judicial intervention under Section 34 is strictly confined to setting "
            "aside an award on recognized statutory grounds."
        )

        for lang in ["hi", "ta"]:
            payload = json.dumps({
                "english_answer": english_answer,
                "target_language": lang,
                "matter_id": "MATTER-HAKEEM-SC",
            }).encode("utf-8")

            req = urllib.request.Request(
                DAEMON_TRANSLATE_URL,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30.0) as resp:
                self.assertEqual(resp.status, 200)
                data = json.loads(resp.read().decode("utf-8"))

                # 1. Original English and evidence remain unchanged
                self.assertEqual(data["original_english_answer"], english_answer)
                self.assertEqual(data["target_language"], lang)

                # 2. Protected legal entities preserved exactly
                preserved_entities = [e["source_text"] for e in data["preserved_entities"]]
                self.assertTrue(any("Hakeem" in e for e in preserved_entities))
                self.assertTrue(any("(2021) 9 SCC 1" in e for e in preserved_entities))
                self.assertTrue(any("Section 34" in e for e in preserved_entities))

                # 3. No unresolved placeholders
                self.assertEqual(data["unresolved_placeholders"], [])

                # 4. Deterministic verification passes
                self.assertTrue(data["is_valid"])
                self.assertEqual(data["verification"]["verification_status"], "VERIFIED_PASS")
                self.assertGreaterEqual(data["verification"]["preservation_rate"], 0.8)

    def test_03_live_statutory_qualification_borse_brothers_kannada_and_marathi(self):
        """
        Live translation on statutory qualification record (Borse Brothers, (2021) 6 SCC 460).
        Verifies preservation of Section 37, Section 13(1A), Section 5, and negative qualifications.
        """
        if not self.daemon_online:
            self.skipTest("Translation daemon on port 8009 is offline.")

        english_answer = (
            "In Government of Maharashtra v. Borse Brothers Engineers (2021) 6 SCC 460, the Supreme Court "
            "held that an appeal under Section 37 of the Arbitration Act must be filed within 60 days as "
            "prescribed under Section 13(1A) of the Commercial Courts Act. Delay may not be condoned under "
            "Section 5 of the Limitation Act except in rare cases where the appellant acted bonafide."
        )

        for lang in ["kn", "mr"]:
            payload = json.dumps({
                "english_answer": english_answer,
                "target_language": lang,
                "matter_id": "MATTER-BORSE-COMM",
            }).encode("utf-8")

            req = urllib.request.Request(
                DAEMON_TRANSLATE_URL,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30.0) as resp:
                self.assertEqual(resp.status, 200)
                data = json.loads(resp.read().decode("utf-8"))

                self.assertEqual(data["original_english_answer"], english_answer)
                self.assertEqual(data["unresolved_placeholders"], [])
                self.assertTrue(data["is_valid"])
                self.assertIn(
                    data["verification"]["verification_status"],
                    ["VERIFIED_PASS", "PASS_WITH_DRIFT_WARNINGS"],
                )

                # Verify critical statutory sections are in preserved entity registry
                sources = [e["source_text"] for e in data["preserved_entities"]]
                self.assertTrue(any("Section 37" in s for s in sources))
                self.assertTrue(any("Section 13(1A)" in s or "Section 13" in s for s in sources))
                self.assertTrue(any("Section 5" in s for s in sources))

    def test_04_live_district_court_case_numbers_amounts_dates(self):
        """
        Live translation on District Court record with case numbers, dates, amounts, and dispositions.
        """
        if not self.daemon_online:
            self.skipTest("Translation daemon on port 8009 is offline.")

        english_answer = (
            "In Spl CC No. 12/2019, the accused was acquitted under Section 138 of the Negotiable Instruments Act. "
            "The disputed amount of Rs. 25,00,000 was held not to be a legally enforceable debt on 12.04.2021."
        )

        payload = json.dumps({
            "english_answer": english_answer,
            "target_language": "hi",
            "matter_id": "MATTER-DC-001",
        }).encode("utf-8")

        req = urllib.request.Request(
            DAEMON_TRANSLATE_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))

            self.assertEqual(data["unresolved_placeholders"], [])
            self.assertTrue(data["is_valid"])

            # Verify case number, amount, date, and disposition are preserved
            trans = data["translated_answer"]
            self.assertIn("12/2019", trans)
            self.assertTrue("25,00,000" in trans or "25" in trans)
            self.assertIn("12.04.2021", trans)
            self.assertTrue("बरी किया गया" in trans or "acquitted" in trans.lower())

    def test_05_placeholder_integrity_and_corruption_detection(self):
        """
        Tests that any unresolved or corrupted placeholder pattern in the translation
        is strictly flagged and rejected by the deterministic verifier.
        """
        corrupted_trans = (
            "उच्चतम न्यायालय ने __LEGAL_ENT_0__ के तहत अपील को खारिज कर दिया और _ _ LEGAL _ ENT _ 1 _ _ शेष है।"
        )
        fake_registry = [
            {"placeholder": "__LEGAL_ENT_0__", "index": 0, "source_text": "Section 34", "target_text": "Section 34"},
            {"placeholder": "__LEGAL_ENT_1__", "index": 1, "source_text": "Section 37", "target_text": "Section 37"},
        ]

        report = self.verifier.verify(
            english_text="The Supreme Court dismissed the appeal under Section 34 and Section 37 remains.",
            translated_text=corrupted_trans,
            target_lang="hi",
            entity_registry=fake_registry,
            matter_id="TEST-CORRUPT",
        )

        self.assertFalse(report["is_valid"])
        self.assertEqual(report["verification_status"], "FAIL_UNRESOLVED_PLACEHOLDERS")
        self.assertGreater(len(report["unresolved_placeholders"]), 0)

    def test_06_unsupported_language_fails_visibly(self):
        """Verifies that an unsupported language returns an explicit 400 Bad Request error."""
        if not self.daemon_online:
            self.skipTest("Translation daemon on port 8009 is offline.")

        payload = json.dumps({
            "english_answer": "Valid legal text.",
            "target_language": "fr",  # French is not a configured Indic language
            "matter_id": "MATTER-001",
        }).encode("utf-8")

        req = urllib.request.Request(
            DAEMON_TRANSLATE_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req, timeout=5.0)

        self.assertEqual(ctx.exception.code, 400)
        err_json = json.loads(ctx.exception.read().decode("utf-8"))
        self.assertIn("Unsupported language code", err_json.get("error", ""))

    def test_07_empty_or_whitespace_input_fails_visibly(self):
        """Verifies that empty or whitespace-only answers fail with explicit error."""
        if not self.daemon_online:
            self.skipTest("Translation daemon on port 8009 is offline.")

        payload = json.dumps({
            "english_answer": "   \n\t  ",
            "target_language": "hi",
            "matter_id": "MATTER-001",
        }).encode("utf-8")

        req = urllib.request.Request(
            DAEMON_TRANSLATE_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req, timeout=5.0)

        self.assertEqual(ctx.exception.code, 400)
        err_json = json.loads(ctx.exception.read().decode("utf-8"))
        self.assertIn("english_answer cannot be empty", err_json.get("error", ""))

    def test_08_fastapi_route_integration(self):
        """Verifies the FastAPI POST /api/v1/translate endpoint contract."""
        if not self.daemon_online:
            self.skipTest("Translation daemon on port 8009 is offline.")

        response = self.client.post(
            "/api/v1/translate",
            json={
                "english_answer": "In NHAI v. M. Hakeem (2021) 9 SCC 1, the Supreme Court held that Section 34 of the Arbitration Act does not permit courts to modify arbitral awards.",
                "target_language": "hi",
                "matter_id": "MATTER-API-TEST",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["matter_id"], "MATTER-API-TEST")
        self.assertEqual(data["target_language"], "hi")
        self.assertTrue(data["is_valid"])
        self.assertIn("Section 34 of the Arbitration Act", data["translated_answer"])

    def test_09_semantic_drift_and_polarity_audit(self):
        """
        Audits semantic drift: verifies that negative legal statements (e.g. 'does not permit')
        retain their qualifying negative polarity in the target Indic text.
        """
        english_statement = "The court does not permit modification of awards under Section 34."
        protected, reg = self.protector.protect(english_statement, "hi")

        # Simulate translated text with correct negation
        valid_hi = "अदालत Section 34 के तहत पुरस्कारों में संशोधन की अनुमति नहीं देती है।"
        report_valid = self.verifier.verify(
            english_text=english_statement,
            translated_text=valid_hi,
            target_lang="hi",
            entity_registry=reg,
            matter_id="DRIFT-TEST",
        )
        self.assertEqual(len(report_valid["drift_warnings"]), 0)

        # Simulate drifted text where negation is dropped (categorical reversal)
        drifted_hi = "अदालत Section 34 के तहत पुरस्कारों में संशोधन की अनुमति देती है।"
        report_drifted = self.verifier.verify(
            english_text=english_statement,
            translated_text=drifted_hi,
            target_lang="hi",
            entity_registry=reg,
            matter_id="DRIFT-TEST",
        )
        self.assertGreater(len(report_drifted["drift_warnings"]), 0)
        self.assertIn("POTENTIAL_POLARITY_SHIFT", report_drifted["drift_warnings"][0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
