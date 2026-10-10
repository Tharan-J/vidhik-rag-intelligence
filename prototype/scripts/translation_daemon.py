#!/usr/bin/env python3
"""
Vidhik Multilingual Legal Translation Daemon
=============================================
HTTP service wrapping the IndicTrans2 model and LegalTranslationPipeline.
Runs on internal port 8009.

Endpoints:
- POST /translate : Protected multilingual legal translation with deterministic verification.
- GET  /health    : Readiness and device status probe.
- GET  /languages : List of supported Indian languages.
"""

import sys
import os
import json
import time
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# Ensure prototype root is in PYTHONPATH
PROTOTYPE_ROOT = Path(__file__).resolve().parent.parent
if str(PROTOTYPE_ROOT) not in sys.path:
    sys.path.insert(0, str(PROTOTYPE_ROOT))

from translation.pipeline import LegalTranslationPipeline
from translation.indictrans_service import SUPPORTED_LANGUAGES

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8009

print("=" * 70)
print(f"STARTING VIDHIK LEGAL TRANSLATION DAEMON ON PORT {PORT}")
print("=" * 70)

# Initialize pipeline once on server boot
try:
    pipeline = LegalTranslationPipeline()
    print("[TranslationDaemon] LegalTranslationPipeline initialized and ready.")
except Exception as e:
    print(f"[TranslationDaemon] Error initializing pipeline: {e}")
    pipeline = None

class TranslationRequestHandler(BaseHTTPRequestHandler):
    """Handles HTTP requests for legal translation."""

    def _send_json(self, status_code: int, data: dict):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, x-lawyer-token, x-matter-id")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send_json(200, {"status": "ok"})

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/health":
            if pipeline is None:
                self._send_json(503, {
                    "status": "unhealthy",
                    "error": "Pipeline initialization failed",
                })
            else:
                self._send_json(200, {
                    "status": "healthy",
                    "service": "vidhik-translation-daemon",
                    "model": pipeline.service.model_path,
                    "device": pipeline.service.device,
                    "supported_languages": list(SUPPORTED_LANGUAGES.keys()),
                })
        elif path == "/languages":
            self._send_json(200, {
                "languages": [
                    {"code": code, "name": meta["name"], "flores_code": meta["code"]}
                    for code, meta in SUPPORTED_LANGUAGES.items()
                ]
            })
        else:
            self._send_json(404, {"error": "Endpoint not found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path != "/translate":
            self._send_json(404, {"error": "Endpoint not found"})
            return

        if pipeline is None:
            self._send_json(503, {"error": "Translation service is currently unavailable."})
            return

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length == 0:
                self._send_json(400, {"error": "Empty request body"})
                return

            body = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(body)

            english_answer = data.get("english_answer", "")
            target_language = data.get("target_language", "")
            matter_id = data.get("matter_id", "GLOBAL")
            evidence = data.get("evidence", [])
            claims = data.get("claims", [])

            if not english_answer or not english_answer.strip():
                self._send_json(400, {"error": "english_answer cannot be empty."})
                return

            if not target_language or not target_language.strip():
                self._send_json(400, {"error": "target_language is required."})
                return

            # Execute translation through pipeline
            result = pipeline.translate_legal_answer(
                english_answer=english_answer,
                target_language=target_language,
                matter_id=matter_id,
                evidence=evidence,
                claims=claims,
            )

            self._send_json(200, result)

        except ValueError as ve:
            self._send_json(400, {"error": str(ve)})
        except Exception as e:
            self._send_json(500, {"error": f"Internal translation error: {str(e)}"})

def run_daemon():
    server_address = ("127.0.0.1", PORT)
    httpd = ThreadingHTTPServer(server_address, TranslationRequestHandler)
    print(f"[TranslationDaemon] Serving on http://127.0.0.1:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[TranslationDaemon] Stopping server.")
        httpd.server_close()

if __name__ == "__main__":
    run_daemon()
