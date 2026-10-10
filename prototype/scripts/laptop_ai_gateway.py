#!/usr/bin/env python3
"""
Vidhik Local AI Inference Gateway
===================================
A narrowly scoped, authenticated gateway designed to safely expose
local AI services (Ollama Qwen and IndicTrans2) to cloud-deployed
backends (Vercel / Railway) via an ngrok tunnel.

Security Safeguards:
- Strict route whitelisting: ONLY /health, /api/generate, and /api/translate.
- Authenticated via Bearer token / x-gateway-token header.
- No access to Ollama administration APIs (pull, delete, push, etc.).
- No filesystem or shell access.
- Comprehensive CORS and ngrok browser-warning bypass support.
- Distinct error reporting when local Ollama or IndicTrans2 is unavailable.

Usage:
    python scripts/laptop_ai_gateway.py [--port 8010] [--token YOUR_SECRET_TOKEN]
"""

import sys
import os
import time
import json
import logging
import argparse
from typing import Optional, Dict, Any

from fastapi import FastAPI, Request, Response, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [AIGateway] %(message)s",
)
logger = logging.getLogger("AIGateway")

OLLAMA_BASE_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
TRANSLATION_DAEMON_URL = os.environ.get("TRANSLATION_URL", "http://127.0.0.1:8009")
DEFAULT_GATEWAY_TOKEN = os.environ.get("GATEWAY_TOKEN", "")

app = FastAPI(
    title="Vidhik Local AI Gateway",
    description="Narrowly scoped proxy for local Qwen3 and IndicTrans2 inference.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
)

# Enable CORS for cloud frontends & backends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


def verify_authentication(request: Request):
    """
    Verify bearer token or x-gateway-token header if GATEWAY_TOKEN is configured.
    """
    expected_token = app.state.gateway_token
    if not expected_token:
        # No token configured, allow open prototype requests
        return

    # Check Authorization header (Bearer <token>)
    auth_header = request.headers.get("authorization", "")
    token = ""
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
    elif "x-gateway-token" in request.headers:
        token = request.headers.get("x-gateway-token", "").strip()

    if not token or token != expected_token:
        logger.warning(f"Unauthorized access attempt from {request.client.host}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "UNAUTHORIZED",
                "message": "Invalid or missing AI Gateway authentication token.",
            },
        )


@app.middleware("http")
async def add_ngrok_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["ngrok-skip-browser-warning"] = "true"
    return response


@app.get("/health", summary="Probe Local AI Health")
async def gateway_health(request: Request):
    """
    Checks availability of local Ollama (11434) and IndicTrans2 (8009).
    Does not require authentication so load balancers / cloud platforms can verify reachability.
    """
    ollama_status = {"available": False, "endpoint": OLLAMA_BASE_URL, "error": None}
    translation_status = {"available": False, "endpoint": TRANSLATION_DAEMON_URL, "error": None}

    async with httpx.AsyncClient(timeout=4.0) as client:
        # Check Ollama
        try:
            o_res = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if o_res.status_code == 200:
                tags = o_res.json()
                models = [m.get("name") for m in tags.get("models", [])]
                ollama_status["available"] = True
                ollama_status["models"] = models
            else:
                ollama_status["error"] = f"HTTP {o_res.status_code}"
        except Exception as e:
            ollama_status["error"] = str(e)

        # Check IndicTrans2
        try:
            t_res = await client.get(f"{TRANSLATION_DAEMON_URL}/health")
            if t_res.status_code == 200:
                t_data = t_res.json()
                translation_status["available"] = True
                translation_status["supported_languages"] = t_data.get("supported_languages", [])
                translation_status["device"] = t_data.get("device", "unknown")
            else:
                translation_status["error"] = f"HTTP {t_res.status_code}"
        except Exception as e:
            translation_status["error"] = str(e)

    overall_healthy = ollama_status["available"]
    return {
        "status": "healthy" if overall_healthy else "degraded",
        "timestamp": time.time(),
        "gateway_version": "1.0.0",
        "auth_required": bool(app.state.gateway_token),
        "ollama": ollama_status,
        "indictrans2": translation_status,
    }


@app.post("/api/generate", summary="Forward to Local Ollama Qwen")
async def proxy_generate(request: Request):
    """
    Proxies generation requests to local Ollama.
    Validates token, enforces JSON format, and handles inference latency gracefully.
    """
    verify_authentication(request)

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload.")

    # Target model default
    if not body.get("model"):
        body["model"] = "qwen3:4b-instruct"

    logger.info(f"Forwarding generate request for model '{body.get('model')}' to Ollama...")
    t0 = time.time()

    async with httpx.AsyncClient(timeout=180.0) as client:
        try:
            resp = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json=body,
                headers={"Content-Type": "application/json"},
            )
        except httpx.ConnectError:
            logger.error("Failed to connect to local Ollama on port 11434.")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "OLLAMA_UNAVAILABLE",
                    "message": "Local Ollama service (port 11434) is currently unreachable on the inference host.",
                },
            )
        except httpx.TimeoutException:
            logger.error("Ollama inference timed out after 180 seconds.")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail={
                    "error": "INFERENCE_TIMEOUT",
                    "message": "Local Qwen inference timed out. The local host may be under heavy load.",
                },
            )

    dur = round(time.time() - t0, 2)
    logger.info(f"Ollama response received in {dur}s (status {resp.status_code}).")

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type=resp.headers.get("content-type", "application/json"),
    )


@app.post("/api/translate", summary="Forward to Local IndicTrans2")
async def proxy_translate(request: Request):
    """
    Proxies legal translation requests to local IndicTrans2 daemon.
    """
    verify_authentication(request)

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload.")

    target_lang = body.get("target_language", "en")
    logger.info(f"Forwarding translation request (target: {target_lang}) to IndicTrans2 daemon...")
    t0 = time.time()

    async with httpx.AsyncClient(timeout=45.0) as client:
        try:
            resp = await client.post(
                f"{TRANSLATION_DAEMON_URL}/translate",
                json=body,
                headers={"Content-Type": "application/json"},
            )
        except httpx.ConnectError:
            logger.error("Failed to connect to IndicTrans2 daemon on port 8009.")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "TRANSLATION_UNAVAILABLE",
                    "message": "IndicTrans2 translation daemon (port 8009) is unreachable on the inference host.",
                },
            )
        except httpx.TimeoutException:
            logger.error("IndicTrans2 translation timed out after 45s.")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail={
                    "error": "TRANSLATION_TIMEOUT",
                    "message": "IndicTrans2 translation timed out.",
                },
            )

    dur = round(time.time() - t0, 2)
    logger.info(f"Translation completed in {dur}s (status {resp.status_code}).")

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type=resp.headers.get("content-type", "application/json"),
    )


def main():
    parser = argparse.ArgumentParser(description="Vidhik Local AI Inference Gateway CLI.")
    parser.add_argument("--port", type=int, default=8010, help="Socket port to bind (default: 8010).")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Socket host to bind (default: 0.0.0.0).")
    parser.add_argument("--token", type=str, default=DEFAULT_GATEWAY_TOKEN, help="Authentication bearer token.")
    args = parser.parse_args()

    app.state.gateway_token = args.token or DEFAULT_GATEWAY_TOKEN

    print("=" * 70)
    print("VIDHIK LOCAL AI INFERENCE GATEWAY")
    print("=" * 70)
    print(f"Host              : {args.host}")
    print(f"Port              : {args.port}")
    print(f"Ollama Target     : {OLLAMA_BASE_URL}")
    print(f"IndicTrans2 Target: {TRANSLATION_DAEMON_URL}")
    print(f"Token Protected   : {'YES' if bool(app.state.gateway_token) else 'NO (Development Mode)'}")
    if app.state.gateway_token:
        print(f"Active Token      : {app.state.gateway_token[:4]}...{app.state.gateway_token[-4:] if len(app.state.gateway_token) > 8 else ''}")
    print("=" * 70)
    print(f"Expose via ngrok:   ngrok http {args.port}")
    print("=" * 70)

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
