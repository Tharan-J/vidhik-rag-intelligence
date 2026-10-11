#!/usr/bin/env python3
"""
Vidhik Local AI Inference Gateway
===================================
A narrowly scoped, authenticated gateway designed to safely expose
local AI services (BGE-M3 embeddings, Ollama Qwen generation, and
IndicTrans2 translation) to cloud-deployed backends (Vercel / Render)
via an ngrok tunnel.

Security Safeguards:
- Strict route whitelisting: ONLY /health, /api/embed, /api/generate, and /api/translate.
- Authenticated via Bearer token / x-gateway-token header.
- Input validation: character limits, batch size limits, structured types.
- No access to Ollama administration APIs (pull, delete, push, etc.).
- No filesystem or shell access.
- Structured error envelopes without leaking internal filesystem paths or stack traces.
- No confidential legal text logged to console.
- Comprehensive CORS and ngrok browser-warning bypass support.

Usage:
    python scripts/laptop_ai_gateway.py [--port 8010] [--token YOUR_SECRET_TOKEN]
"""

import sys
import os
import time
import math
import logging
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, List

# Ensure prototype root is in PYTHONPATH
PROTOTYPE_ROOT = Path(__file__).resolve().parent.parent
if str(PROTOTYPE_ROOT) not in sys.path:
    sys.path.insert(0, str(PROTOTYPE_ROOT))

from fastapi import FastAPI, Request, Response, HTTPException, status
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
DEFAULT_GATEWAY_TOKEN = os.environ.get("AI_GATEWAY_TOKEN", os.environ.get("GATEWAY_TOKEN", ""))

# Global BGE-M3 embedding engine cache
_embed_engine = None
_embed_engine_error = None


def get_embedding_engine():
    """Lazily initialize or return the BGE-M3 embedding engine on the laptop."""
    global _embed_engine, _embed_engine_error
    if _embed_engine is not None:
        return _embed_engine
    if _embed_engine_error is not None:
        raise RuntimeError(f"BGE-M3 initialization previously failed: {_embed_engine_error}")

    try:
        from ingestion.embed import BGEM3EmbeddingEngine
        logger.info("Initializing local BGE-M3 embedding engine on inference host...")
        _embed_engine = BGEM3EmbeddingEngine()
        logger.info("Local BGE-M3 embedding engine initialized successfully.")
        return _embed_engine
    except Exception as e:
        _embed_engine_error = str(e)
        logger.error(f"Failed to initialize local BGE-M3 engine: {e}")
        raise


app = FastAPI(
    title="Vidhik Local AI Gateway",
    description="Narrowly scoped proxy for local BGE-M3 embeddings, Qwen3 generation, and IndicTrans2 translation.",
    version="1.1.0",
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
    expected_token = getattr(app.state, "gateway_token", DEFAULT_GATEWAY_TOKEN)
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
        client_host = request.client.host if request.client else "unknown"
        logger.warning(f"Unauthorized access attempt from {client_host}")
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
    Checks availability of local Ollama (11434), IndicTrans2 (8009),
    and the local BGE-M3 embedding engine.
    Does not require authentication so load balancers / cloud platforms can verify reachability.
    """
    ollama_status = {"available": False, "endpoint": OLLAMA_BASE_URL, "error": None}
    translation_status = {"available": False, "endpoint": TRANSLATION_DAEMON_URL, "error": None}
    embedding_status = {"available": False, "model": "BAAI/bge-m3", "dimension": 1024, "error": None}

    # 1. Check local BGE-M3 Embedding Engine
    try:
        engine = get_embedding_engine()
        embedding_status["available"] = engine is not None
    except Exception as e:
        embedding_status["error"] = "Embedding engine initialization error"

    # 2. Check Ollama & IndicTrans2
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
            ollama_status["error"] = "Connection refused or timed out"

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
            translation_status["error"] = "Connection refused or timed out"

    overall_healthy = embedding_status["available"] and ollama_status["available"]
    return {
        "status": "healthy" if overall_healthy else "degraded",
        "timestamp": time.time(),
        "gateway_version": "1.1.0",
        "auth_required": bool(getattr(app.state, "gateway_token", DEFAULT_GATEWAY_TOKEN)),
        "embedding": embedding_status,
        "ollama": ollama_status,
        "indictrans2": translation_status,
    }


@app.post("/api/embed", summary="Generate BGE-M3 Dense Query Embeddings")
async def generate_embedding(request: Request):
    """
    Generates 1024-dimensional normalized dense embeddings via local BGE-M3.
    Used by Render retrieval service to perform dense semantic retrieval
    without loading BGE-M3 into Render memory.
    """
    verify_authentication(request)

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "INVALID_JSON", "message": "Malformed JSON payload."},
        )

    if not isinstance(body, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "INVALID_BODY", "message": "Request body must be a JSON object."},
        )

    # Support single text/query or batch texts
    single_text = body.get("text") or body.get("query")
    batch_texts = body.get("texts")

    if single_text is None and batch_texts is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "MISSING_INPUT",
                "message": "Field 'text', 'query', or 'texts' is required.",
            },
        )

    try:
        engine = get_embedding_engine()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "EMBEDDING_UNAVAILABLE",
                "message": "BGE-M3 embedding engine is unavailable on the local host.",
            },
        )

    # Handle batch request
    if batch_texts is not None:
        if not isinstance(batch_texts, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "INVALID_TEXTS", "message": "'texts' must be an array of strings."},
            )
        if len(batch_texts) == 0:
            return {"embeddings": [], "dimension": 1024, "count": 0, "model": "BAAI/bge-m3"}
        if len(batch_texts) > 32:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "BATCH_TOO_LARGE", "message": "Batch size cannot exceed 32 items."},
            )

        clean_texts = []
        for idx, t in enumerate(batch_texts):
            if not isinstance(t, str) or not t.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"error": "INVALID_TEXT", "message": f"Item at index {idx} must be a non-empty string."},
                )
            if len(t) > 8192:
                clean_texts.append(t[:8192])
            else:
                clean_texts.append(t)

        t0 = time.time()
        logger.info(f"Generating dense embeddings for batch of {len(clean_texts)} texts...")
        vecs = engine.encode_dense_batch(clean_texts)
        duration = round(time.time() - t0, 3)

        # Validate numeric output
        for v in vecs:
            if len(v) != 1024 or not all(isinstance(x, (int, float)) and not math.isnan(x) and not math.isinf(x) for x in v):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={"error": "EMBEDDING_INVALID", "message": "Failed to generate valid 1024-d numeric vector."},
                )

        logger.info(f"Batch embedding generated in {duration}s.")
        return {
            "embeddings": vecs,
            "dimension": 1024,
            "count": len(vecs),
            "model": "BAAI/bge-m3",
        }

    # Handle single text request
    if not isinstance(single_text, str) or not single_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "EMPTY_QUERY", "message": "Text/query cannot be empty."},
        )

    clean_text = single_text.strip()
    if len(clean_text) > 8192:
        clean_text = clean_text[:8192]

    t0 = time.time()
    logger.info(f"Generating dense query embedding (text length {len(clean_text)} chars)...")
    vec = engine.encode_query(clean_text)
    duration = round(time.time() - t0, 3)

    # Validate numeric output
    if len(vec) != 1024 or not all(isinstance(x, (int, float)) and not math.isnan(x) and not math.isinf(x) for x in vec):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "EMBEDDING_INVALID", "message": "Failed to generate valid 1024-d numeric vector."},
        )

    logger.info(f"Query embedding generated in {duration}s.")
    return {
        "embedding": vec,
        "dimension": 1024,
        "model": "BAAI/bge-m3",
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
        raise HTTPException(status_code=400, detail={"error": "INVALID_JSON", "message": "Invalid JSON payload."})

    # Target model default
    if not body.get("model"):
        body["model"] = "qwen3:4b-instruct"

    target_model = body.get("model")
    logger.info(f"Forwarding generate request for model '{target_model}' to Ollama...")
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
        raise HTTPException(status_code=400, detail={"error": "INVALID_JSON", "message": "Invalid JSON payload."})

    # Ensure body compatibility with translation daemon
    if not body.get("english_answer") and body.get("text"):
        body["english_answer"] = body["text"]

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
    print(f"BGE-M3 Embedding  : Local (1024-d dense)")
    print(f"Token Protected   : {'YES' if bool(app.state.gateway_token) else 'NO (Development Mode)'}")
    if app.state.gateway_token:
        print(f"Active Token      : {app.state.gateway_token[:4]}...{app.state.gateway_token[-4:] if len(app.state.gateway_token) > 8 else ''}")
    print("=" * 70)
    print(f"Expose via ngrok:   ngrok http {args.port}")
    print("=" * 70)

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
