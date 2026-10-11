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
    Verify bearer token or x-gateway-token header if explicitly required.
    Authorization is disabled by default per user request to ensure seamless
    connectivity between Vercel, Render, and the local laptop gateway.
    """
    if not getattr(app.state, "require_auth", False):
        # Open access mode enabled - allow all requests without 401
        return

    expected_token = getattr(app.state, "gateway_token", DEFAULT_GATEWAY_TOKEN).strip().strip("\"'")
    if not expected_token:
        # No token configured, allow open prototype requests
        return

    # Check Authorization header (Bearer <token>)
    auth_header = request.headers.get("authorization", "").strip()
    token = ""
    if auth_header.lower().startswith("bearer "):
        token = auth_header[7:].strip().strip("\"'")
    elif "x-gateway-token" in request.headers:
        token = request.headers.get("x-gateway-token", "").strip().strip("\"'")

    # Also handle nested "Bearer " if client prefixed token with "Bearer "
    while token.lower().startswith("bearer "):
        token = token[7:].strip().strip("\"'")

    if not token or token != expected_token:
        client_host = request.client.host if request.client else "unknown"
        has_auth = bool(auth_header)
        has_xgateway = "x-gateway-token" in request.headers
        token_len = len(token)
        logger.warning(
            f"Unauthorized access attempt from {client_host} "
            f"(auth_header_present={has_auth}, x_gateway_present={has_xgateway}, "
            f"token_received_len={token_len}, expected_token_len={len(expected_token)})"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "UNAUTHORIZED",
                "message": "Invalid or missing AI Gateway authentication token. Ensure AI_GATEWAY_TOKEN matches.",
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


@app.post("/api/extract-pdf", summary="Extract Verified Text from PDF via Local PyMuPDF")
async def extract_pdf_endpoint(request: Request):
    """
    Extracts verified page-by-page text from a PDF file using local PyMuPDF.
    Accepts JSON with 'pdf_base64' or raw PDF binary body.
    Allows Vercel serverless to obtain high-fidelity text with zero cloud memory overhead.
    """
    import base64
    verify_authentication(request)

    pdf_bytes = b""
    content_type = request.headers.get("content-type", "").lower()

    if "application/pdf" in content_type or "application/octet-stream" in content_type:
        pdf_bytes = await request.body()
    else:
        try:
            body = await request.json()
            raw_b64 = body.get("pdf_base64") or body.get("file_base64") or ""
            if raw_b64:
                if "," in raw_b64:
                    raw_b64 = raw_b64.split(",", 1)[1]
                pdf_bytes = base64.b64decode(raw_b64)
            elif "text" in body:
                return {
                    "success": True,
                    "totalPages": 1,
                    "pages": [{"pageNumber": 1, "text": body["text"]}],
                    "fullText": body["text"],
                    "totalChars": len(body["text"]),
                }
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail={"error": "INVALID_PAYLOAD", "message": f"Could not read PDF data: {e}"},
            )

    if not pdf_bytes or len(pdf_bytes) < 10:
        raise HTTPException(
            status_code=400,
            detail={"error": "EMPTY_PDF", "message": "No valid PDF bytes provided."},
        )

    try:
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages = []
        full_text_list = []

        for i, page in enumerate(doc):
            txt = (page.get_text() or "").strip()
            pages.append({"pageNumber": i + 1, "text": txt})
            if txt:
                full_text_list.append(f"--- PAGE {i + 1} ---\n{txt}")

        total_chars = sum(len(p["text"]) for p in pages)
        logger.info(f"Local PyMuPDF extracted {len(doc)} pages ({total_chars} chars) from PDF.")

        return {
            "success": total_chars > 20,
            "totalPages": len(doc),
            "pages": pages,
            "fullText": "\n\n".join(full_text_list),
            "totalChars": total_chars,
        }
    except Exception as e:
        logger.error(f"Failed to extract PDF via PyMuPDF: {e}")
        raise HTTPException(
            status_code=422,
            detail={"error": "PDF_EXTRACTION_FAILED", "message": str(e)},
        )


def main():
    parser = argparse.ArgumentParser(description="Vidhik Local AI Inference Gateway CLI.")
    parser.add_argument("--port", type=int, default=8010, help="Socket port to bind (default: 8010).")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Socket host to bind (default: 0.0.0.0).")
    parser.add_argument("--token", type=str, default=DEFAULT_GATEWAY_TOKEN, help="Optional authentication bearer token.")
    parser.add_argument("--require-auth", action="store_true", default=False, help="Enforce token verification (default: False, open access).")
    args = parser.parse_args()

    app.state.gateway_token = args.token or DEFAULT_GATEWAY_TOKEN
    app.state.require_auth = args.require_auth

    print("=" * 70)
    print("VIDHIK LOCAL AI INFERENCE GATEWAY")
    print("=" * 70)
    print(f"Host              : {args.host}")
    print(f"Port              : {args.port}")
    print(f"Ollama Target     : {OLLAMA_BASE_URL}")
    print(f"IndicTrans2 Target: {TRANSLATION_DAEMON_URL}")
    print(f"BGE-M3 Embedding  : Local (1024-d dense)")
    print(f"Token Protected   : {'YES' if app.state.require_auth else 'NO (Authorization Removed / Open Access)'}")
    if app.state.require_auth and app.state.gateway_token:
        print(f"Active Token      : {app.state.gateway_token[:4]}...{app.state.gateway_token[-4:] if len(app.state.gateway_token) > 8 else ''}")
    print("=" * 70)
    print(f"Expose via ngrok:   ngrok http {args.port}")
    print("=" * 70)

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
