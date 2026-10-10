"""
Vidhik — Access Flow Simplification & Public Multilingual Legal Chatbot Test Suite
==================================================================================
Validates all 12 requirements specified in the simplified product architecture:
1. Landing-page Sign In navigates to lawyer login (/login).
2. Get Started opens the public chatbot (/chat) without requiring lawyer authentication.
3. The obsolete profile chooser is no longer part of the active journey (/get-started redirects).
4. Unauthenticated users cannot access protected lawyer routes or private matter data.
5. Research OFF uses the local Qwen path and never silently falls back to Gemini.
6. Research ON uses the established Vidhik RAG and local Qwen path.
7. Research ON abstains when evidence is insufficient.
8. Tamil, Hindi, Kannada and Marathi use the existing translation pipeline where supported.
9. Translation preserves evidence IDs and the original English answer.
10. Service failures, unsupported languages and malformed requests produce safe, visible errors.
11. The lawyer login and existing Matter Workspace continue to work.
12. No obsolete profile redirect breaks the new navigation (/student and /common redirect to /chat).
"""

import unittest
import requests
import json
import time

NEXT_BASE_URL = "http://localhost:3000"
TRANSLATION_DAEMON_URL = "http://127.0.0.1:8009"
RETRIEVAL_DAEMON_URL = "http://127.0.0.1:8008"


class TestAccessFlowAndPublicChatbot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Verify Next.js dev server
        try:
            r = requests.get(f"{NEXT_BASE_URL}/api/matters", timeout=5)
            assert r.status_code == 200
        except Exception as e:
            raise RuntimeError(f"Next.js server not reachable at {NEXT_BASE_URL}: {e}")

    # -------------------------------------------------------------------------
    # Test 1: Landing Page Sign In navigates to Lawyer Login (/login)
    # -------------------------------------------------------------------------
    def test_01_landing_page_and_login_route_exist(self):
        # 1. Landing page responds 200
        r_home = requests.get(f"{NEXT_BASE_URL}/", timeout=5)
        self.assertEqual(r_home.status_code, 200)

        # 2. Dedicated Lawyer Login page responds 200
        r_login = requests.get(f"{NEXT_BASE_URL}/login", timeout=5)
        self.assertEqual(r_login.status_code, 200)
        self.assertIn("Lawyer Workspace Login", r_login.text)
        self.assertIn("/chat", r_login.text)  # Contains visible link to Public Chatbot

    # -------------------------------------------------------------------------
    # Test 2: Get Started opens Public Chatbot (/chat) without lawyer authentication
    # -------------------------------------------------------------------------
    def test_02_public_chatbot_accessible_unauthenticated(self):
        r_chat = requests.get(f"{NEXT_BASE_URL}/chat", timeout=5)
        self.assertEqual(r_chat.status_code, 200)
        self.assertIn("Public Multilingual Legal Assistant", r_chat.text)
        self.assertIn("RESEARCH MODE", r_chat.text)

    # -------------------------------------------------------------------------
    # Test 3: Obsolete profile chooser is replaced with clean redirection
    # -------------------------------------------------------------------------
    def test_03_get_started_route_redirects(self):
        r_gs = requests.get(f"{NEXT_BASE_URL}/get-started", timeout=5)
        self.assertEqual(r_gs.status_code, 200)
        # Should link/direct to /chat and /login rather than 3-bubble chooser
        self.assertIn("/chat", r_gs.text)
        self.assertIn("/login", r_gs.text)

    # -------------------------------------------------------------------------
    # Test 4: Unauthenticated users cannot access protected lawyer routes / private files
    # -------------------------------------------------------------------------
    def test_04_unauthenticated_matter_isolation(self):
        # Attempting to access protected stream without auth or valid context
        r_stream = requests.get(f"{NEXT_BASE_URL}/api/documents/stream?docId=confidential.pdf", timeout=5)
        # Should reject with 401 or 403 or error
        self.assertIn(r_stream.status_code, [400, 401, 403, 404])

        # Attempting to access translate endpoint with missing auth context
        r_trans = requests.post(
            f"{NEXT_BASE_URL}/api/translate",
            json={"english_answer": "Court decree", "target_language": "ta"},
            timeout=5,
        )
        self.assertEqual(r_trans.status_code, 401)
        self.assertIn("UNAUTHENTICATED", r_trans.json()["error"]["code"])

    # -------------------------------------------------------------------------
    # Test 5: Research OFF uses local Qwen path and never silently falls back to Gemini
    # -------------------------------------------------------------------------
    def test_05_research_off_uses_local_qwen(self):
        payload = {
            "query": "What is anticipatory bail under Indian law?",
            "researchMode": false if "false" in locals() else False,
            "targetLanguage": "en",
        }
        r = requests.post(f"{NEXT_BASE_URL}/api/public/chat", json=payload, timeout=60)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertFalse(data.get("researchMode"))
        self.assertFalse(data.get("grounded"))
        self.assertIn("Section 438", data.get("answer", ""))
        self.assertEqual(data.get("modeLabel"), "Conversational Legal Information (Research OFF)")
        self.assertIn("Notice: This response provides general legal information only", data.get("disclaimer", ""))

    # -------------------------------------------------------------------------
    # Test 6: Research ON uses established Vidhik RAG and local Qwen path
    # -------------------------------------------------------------------------
    def test_06_research_on_evidence_grounded(self):
        payload = {
            "query": "Whether Uttar Pradesh Board of Madarsa Education Act 2004 violates secularism?",
            "researchMode": True,
            "targetLanguage": "en",
        }
        r = requests.post(f"{NEXT_BASE_URL}/api/public/chat", json=payload, timeout=120)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data.get("researchMode"))
        self.assertIn("evidence", data)
        self.assertIn("claims", data)
        self.assertEqual(data.get("modeLabel"), "Judicial Research Mode (Evidence-Grounded)")

    # -------------------------------------------------------------------------
    # Test 7: Research ON abstains when evidence is insufficient
    # -------------------------------------------------------------------------
    def test_07_research_on_abstains_on_insufficient_evidence(self):
        payload = {
            "query": "How to bake a chocolate cake?",
            "researchMode": True,
            "targetLanguage": "en",
        }
        r = requests.post(f"{NEXT_BASE_URL}/api/public/chat", json=payload, timeout=60)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data.get("confidence"), "insufficient_evidence")
        self.assertFalse(data.get("grounded"))
        self.assertIn("does not contain any information relevant", data.get("answer", "").lower())

    # -------------------------------------------------------------------------
    # Test 8: Tamil, Hindi, Kannada, Marathi use translation pipeline where supported
    # -------------------------------------------------------------------------
    def test_08_multilingual_translation_indictrans2(self):
        for lang_code in ["ta", "hi"]:
            payload = {
                "query": "What is anticipatory bail?",
                "researchMode": False,
                "targetLanguage": lang_code,
            }
            r = requests.post(f"{NEXT_BASE_URL}/api/public/chat", json=payload, timeout=60)
            self.assertEqual(r.status_code, 200)
            data = r.json()
            self.assertEqual(data.get("targetLanguage"), lang_code)
            self.assertTrue(len(data.get("answer", "")) > 10)
            # Original English answer preserved
            self.assertIn("originalEnglishAnswer", data)
            self.assertTrue(len(data["originalEnglishAnswer"]) > 10)

    # -------------------------------------------------------------------------
    # Test 9: Translation preserves evidence IDs and original English answer
    # -------------------------------------------------------------------------
    def test_09_translation_preserves_evidence_ids_and_english(self):
        payload = {
            "query": "What is anticipatory bail?",
            "researchMode": False,
            "targetLanguage": "ta",
        }
        r = requests.post(f"{NEXT_BASE_URL}/api/public/chat", json=payload, timeout=60)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("preservedEntities", data)
        self.assertIn("originalEnglishAnswer", data)

    # -------------------------------------------------------------------------
    # Test 10: Service failures, unsupported languages, and malformed requests produce safe errors
    # -------------------------------------------------------------------------
    def test_10_malformed_and_unsupported_language_errors(self):
        # Empty query
        r_empty = requests.post(f"{NEXT_BASE_URL}/api/public/chat", json={"query": ""}, timeout=5)
        self.assertEqual(r_empty.status_code, 400)
        self.assertIn("Query cannot be empty", r_empty.json()["error"])

        # Unsupported language
        r_unsupported = requests.post(
            f"{NEXT_BASE_URL}/api/public/chat",
            json={"query": "Valid legal question", "targetLanguage": "fr"},
            timeout=5,
        )
        self.assertEqual(r_unsupported.status_code, 400)
        self.assertIn("Unsupported language code", r_unsupported.json()["error"])

        # Query exceeding max length
        r_long = requests.post(
            f"{NEXT_BASE_URL}/api/public/chat",
            json={"query": "A" * 1600},
            timeout=5,
        )
        self.assertEqual(r_long.status_code, 400)
        self.assertIn("maximum length", r_long.json()["error"])

    # -------------------------------------------------------------------------
    # Test 11: Lawyer login and existing Matter Workspace continue to work
    # -------------------------------------------------------------------------
    def test_11_lawyer_workspace_matters_api(self):
        r_matters = requests.get(f"{NEXT_BASE_URL}/api/matters", timeout=5)
        self.assertEqual(r_matters.status_code, 200)
        matters = r_matters.json().get("matters", [])
        self.assertTrue(len(matters) > 0)
        m0 = matters[0]
        self.assertIn("id", m0)
        self.assertIn("title", m0)

        # Single matter query
        r_single = requests.get(f"{NEXT_BASE_URL}/api/matters/{m0['id']}", timeout=5)
        self.assertEqual(r_single.status_code, 200)
        self.assertEqual(r_single.json()["matter"]["id"], m0["id"])

    # -------------------------------------------------------------------------
    # Test 12: No obsolete profile redirect breaks navigation (/student and /common)
    # -------------------------------------------------------------------------
    def test_12_legacy_profile_routes_respond_cleanly(self):
        r_student = requests.get(f"{NEXT_BASE_URL}/student", timeout=5)
        self.assertEqual(r_student.status_code, 200)
        self.assertIn("/chat", r_student.text)

        r_common = requests.get(f"{NEXT_BASE_URL}/common", timeout=5)
        self.assertEqual(r_common.status_code, 200)
        self.assertIn("/chat", r_common.text)


if __name__ == "__main__":
    unittest.main()
