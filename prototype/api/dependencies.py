"""
FastAPI Dependencies & Subsystem Readiness Checkers
===================================================
Provides shared dependencies for FastAPI route handlers and performs
lightweight, non-generative readiness inspections of Qdrant, BM25,
embedding models, and the local Qwen generator service.
"""

import time
import json
import logging
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from fastapi import Request, HTTPException, status

from rag.engine import LegalRAGEngine
from .schemas import ComponentStatus, SystemStatusResponse

logger = logging.getLogger("VidhikAPI.Dependencies")


def get_rag_engine(request: Request) -> LegalRAGEngine:
    """
    Dependency returning the shared LegalRAGEngine instance stored on app state.
    """
    engine: Optional[LegalRAGEngine] = getattr(request.app.state, "engine", None)
    if engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": {
                    "code": "ENGINE_NOT_INITIALIZED",
                    "message": "Legal RAG Engine is not yet initialized.",
                }
            },
        )
    return engine


def check_subsystem_readiness(engine: LegalRAGEngine) -> SystemStatusResponse:
    """
    Inspects readiness of each RAG subsystem without invoking expensive generation.
    Checks:
    1. Qdrant Cloud (collection accessibility & point count)
    2. BM25 In-Memory Index (corpus size & tokenized state)
    3. BGE-M3 Dense Embedding Engine (ONNX runtime state)
    4. Ollama Generator Service (HTTP connectivity & Qwen model presence)
    """
    components: Dict[str, ComponentStatus] = {}
    all_ok = True

    # 1. Qdrant Check
    try:
        dense_ret = engine.retrieval_engine.dense_retriever
        coll_info = dense_ret.client.get_collection(dense_ret.config.collection_name)
        points_count = coll_info.points_count or 0
        components["qdrant"] = ComponentStatus(
            status="ok",
            details={
                "collection": dense_ret.config.collection_name,
                "points_count": points_count,
                "status": coll_info.status.value if hasattr(coll_info.status, "value") else str(coll_info.status),
            },
        )
    except Exception as e:
        logger.warning(f"Qdrant readiness check failed: {e}")
        components["qdrant"] = ComponentStatus(
            status="unavailable",
            details={"error": str(e)},
        )
        all_ok = False

    # 2. BM25 Check
    try:
        bm25_ret = engine.retrieval_engine.bm25_retriever
        corpus_size = bm25_ret.corpus_size
        index_loc = str(getattr(bm25_ret.config, "index_dir", getattr(bm25_ret.config, "index_path", "indexes/bm25")))
        if corpus_size > 0:
            components["bm25"] = ComponentStatus(
                status="ok",
                details={
                    "chunks_count": corpus_size,
                    "index_directory": index_loc,
                },
            )
        else:
            components["bm25"] = ComponentStatus(
                status="degraded",
                details={"chunks_count": 0, "message": "BM25 index contains no documents."},
            )
            all_ok = False
    except Exception as e:
        logger.warning(f"BM25 readiness check failed: {e}")
        components["bm25"] = ComponentStatus(
            status="unavailable",
            details={"error": str(e)},
        )
        all_ok = False

    # 3. BGE-M3 Dense Embedding Engine Check
    try:
        embed_eng = engine.retrieval_engine.dense_retriever.embed_engine
        is_ready = (
            (hasattr(embed_eng, "_onnx_session") and embed_eng._onnx_session is not None)
            or (hasattr(embed_eng, "model") and embed_eng.model is not None)
            or (hasattr(embed_eng, "session") and embed_eng.session is not None)
        )
        components["embedding_engine"] = ComponentStatus(
            status="ok" if is_ready else "unavailable",
            details={
                "model_name": embed_eng.model_name,
                "dense_dim": embed_eng.dense_dim,
                "engine_ready": is_ready,
            },
        )
        if not is_ready:
            all_ok = False
    except Exception as e:
        logger.warning(f"Embedding engine readiness check failed: {e}")
        components["embedding_engine"] = ComponentStatus(
            status="unavailable",
            details={"error": str(e)},
        )
        all_ok = False

    # 4. Ollama / Qwen Service Check
    try:
        generator_cfg = engine.config.generator
        ollama_endpoint = generator_cfg.endpoint  # e.g. http://localhost:11434/api/generate
        # Derive base URL or tags endpoint
        base_url = ollama_endpoint.rsplit("/api/", 1)[0]
        tags_url = f"{base_url}/api/tags"

        req = urllib.request.Request(tags_url, headers={"User-Agent": "Vidhik-StatusCheck/1.0"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = [m.get("name") for m in data.get("models", [])]
            model_present = any(generator_cfg.model in m for m in models)

            if model_present:
                components["generator"] = ComponentStatus(
                    status="ok",
                    details={
                        "model": generator_cfg.model,
                        "endpoint": generator_cfg.endpoint,
                        "model_loaded": True,
                    },
                )
            else:
                components["generator"] = ComponentStatus(
                    status="degraded",
                    details={
                        "model": generator_cfg.model,
                        "endpoint": generator_cfg.endpoint,
                        "available_models": models,
                        "warning": f"Configured model '{generator_cfg.model}' not listed in Ollama tags.",
                    },
                )
                all_ok = False
    except Exception as e:
        logger.warning(f"Generator readiness check failed: {e}")
        components["generator"] = ComponentStatus(
            status="unavailable",
            details={
                "model": engine.config.generator.model,
                "endpoint": engine.config.generator.endpoint,
                "error": str(e),
            },
        )
        all_ok = False

    overall_status = "ready" if all_ok else ("degraded" if any(c.status == "ok" for c in components.values()) else "unavailable")

    return SystemStatusResponse(
        status=overall_status,
        components=components,
        timestamp=datetime.now(timezone.utc).isoformat(),
        service="vidhik-api",
        version="1.0.0",
    )
