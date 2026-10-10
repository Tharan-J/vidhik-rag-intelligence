"""
FastAPI Route Handlers for Vidhik API
=====================================
Defines endpoints:
- GET  /health         : Instant lightweight service health check.
- GET  /api/v1/status  : Non-generative runtime readiness check across all RAG subsystems.
- POST /api/v1/query   : Primary evidence-grounded legal question answering endpoint.
"""

import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from rag.engine import LegalRAGEngine, LegalRAGResponse
from .schemas import (
    LegalQueryRequest,
    LegalQueryResponse,
    ClaimResponse,
    CitationAuthorityResponse,
    EvidenceItemResponse,
    HealthResponse,
    SystemStatusResponse,
    ErrorResponse,
    LegalTranslationRequest,
    LegalTranslationResponse,
)
from .dependencies import get_rag_engine, check_subsystem_readiness

logger = logging.getLogger("VidhikAPI.Routes")

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    description="Lightweight health probe verifying that the API server is operational.",
    tags=["System"],
)
async def health_check() -> HealthResponse:
    """Instant health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        service="vidhik-api",
        version="1.0.0",
    )


@router.get(
    "/api/v1/status",
    response_model=SystemStatusResponse,
    summary="Subsystem Readiness Check",
    description="Inspects availability of Qdrant Cloud, BM25 index, BGE-M3 embedding engine, and local Qwen without performing expensive generation.",
    tags=["System"],
)
async def system_status(
    engine: LegalRAGEngine = Depends(get_rag_engine),
) -> SystemStatusResponse:
    """Detailed readiness check across RAG dependencies."""
    return check_subsystem_readiness(engine)


@router.post(
    "/api/v1/query",
    response_model=LegalQueryResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid or empty query string."},
        422: {"description": "Validation error in request payload."},
        503: {"model": ErrorResponse, "description": "Backend retrieval or generation dependency unavailable."},
        504: {"model": ErrorResponse, "description": "RAG pipeline execution timed out."},
    },
    summary="Execute Legal RAG Query",
    description="Processes a user legal question through Hybrid Retrieval (BGE-M3 + BM25), selects authoritative evidence, executes evidence-constrained Qwen generation, and returns a verified structured legal answer with full claim-to-evidence provenance.",
    tags=["Legal RAG"],
)
async def legal_query(
    request: LegalQueryRequest,
    engine: LegalRAGEngine = Depends(get_rag_engine),
) -> LegalQueryResponse:
    """
    Primary endpoint for evidence-grounded legal question answering.
    """
    clean_query = request.query.strip()
    if not clean_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "EMPTY_QUERY",
                    "message": "Query parameter must not be empty or whitespace only.",
                }
            },
        )

    t0 = time.time()
    logger.info(f"Received API legal query: '{clean_query}' (top_k={request.top_k}, max_evidence={request.max_evidence})")

    try:
        rag_response: LegalRAGResponse = engine.answer(
            query=clean_query,
            top_k=request.top_k,
            max_evidence=request.max_evidence,
        )
    except TimeoutError as te:
        logger.error(f"Generation timeout processing query '{clean_query}': {te}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={
                "error": {
                    "code": "GENERATION_TIMEOUT",
                    "message": "The legal generation service timed out before completing the answer.",
                }
            },
        )
    except RuntimeError as re:
        err_str = str(re)
        logger.error(f"Runtime error processing query '{clean_query}': {re}")
        if "Qwen service unreachable" in err_str or "Ollama" in err_str:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": {
                        "code": "GENERATOR_UNAVAILABLE",
                        "message": "The local Qwen legal generation service is currently unreachable.",
                    }
                },
            )
        elif "Qdrant query failed" in err_str or "Qdrant" in err_str:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": {
                        "code": "VECTOR_STORE_UNAVAILABLE",
                        "message": "The Qdrant vector retrieval service is currently unreachable.",
                    }
                },
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": {
                        "code": "RAG_PROCESSING_ERROR",
                        "message": "An internal error occurred during legal research retrieval or generation.",
                    }
                },
            )
    except Exception as e:
        logger.error(f"Unexpected error processing query '{clean_query}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred while processing the legal query.",
                }
            },
        )

    # Format claims and authorities
    # Format claims and authorities
    formatted_claims = []
    for c in rag_response.claims:
        authorities = [
            CitationAuthorityResponse(
                evidence_id=a.evidence_id,
                court=a.court,
                court_level=a.court_level,
                case_title=a.case_title,
                case_number=a.case_number,
                decision_date=a.decision_date,
                page_number=a.page_number,
                paragraph_id=a.paragraph_id,
                document_id=a.document_id,
                chunk_id=a.chunk_id,
                verification_status=getattr(a, "verification_status", "UNVERIFIED"),
                verified_page=getattr(a, "verified_page", None),
                verified_paragraph=getattr(a, "verified_paragraph", None),
                is_source_verified=getattr(a, "is_source_verified", False),
            )
            for a in c.authorities
        ]
        formatted_claims.append(
            ClaimResponse(
                claim=c.claim,
                evidence_ids=c.evidence_ids,
                authorities=authorities,
                is_grounded=c.is_grounded,
                claim_type=getattr(c, "claim_type", "judicial_finding"),
                support_level=getattr(c, "support_level", "directly_supports"),
                qualification=getattr(c, "qualification", None),
                citation_verified=getattr(c, "citation_verified", False),
                verification_status=getattr(c, "verification_status", "UNVERIFIED"),
                verification_details=getattr(c, "verification_details", None),
            )
        )

    # Format evidence items
    formatted_evidence = [
        EvidenceItemResponse(
            evidence_id=ev.get("evidence_id", ev.get("id", "")),
            court=ev.get("court", "Unknown"),
            court_level=ev.get("court_level", "Unknown"),
            case_title=ev.get("case_title", "Unknown"),
            case_number=ev.get("case_number", "Unknown"),
            decision_date=str(ev.get("decision_date", "Unknown")),
            page_start=int(ev.get("page_start", 1)),
            page_end=int(ev.get("page_end", 1)),
            page_number=ev.get("page_number", str(ev.get("page", ""))),
            paragraph_start=str(ev.get("paragraph_start", "")),
            paragraph_end=str(ev.get("paragraph_end", "")),
            paragraph_id=str(ev.get("paragraph_id", ev.get("paragraph", ""))),
            sentence_id=str(ev.get("sentence_id", "")),
            source_file=str(ev.get("source_file", "")),
            document_id=str(ev.get("document_id", ev.get("source_file", ""))),
            chunk_id=str(ev.get("chunk_id", "")),
            qdrant_point_id=str(ev.get("qdrant_point_id", "")),
            text=str(ev.get("text", "")),
            rrf_score=ev.get("rrf_score"),
            rrf_rank=ev.get("rrf_rank"),
        )
        for ev in rag_response.evidence
    ]

    # Format contrary / qualifying evidence
    contrary_evidence_raw = getattr(rag_response, "contrary_evidence", [])
    contrary_formatted = [
        {
            "evidence_id": ce.get("evidence_id", ""),
            "nature": ce.get("nature", "qualification"),
            "explanation": ce.get("explanation", ""),
        }
        for ce in contrary_evidence_raw
        if isinstance(ce, dict) and ce.get("evidence_id")
    ]

    return LegalQueryResponse(
        query=rag_response.query,
        answer=rag_response.answer,
        claims=formatted_claims,
        evidence=formatted_evidence,
        contrary_evidence=contrary_formatted,
        limitations=rag_response.limitations,
        confidence=rag_response.confidence,
        retrieval_count=rag_response.retrieval_count,
        evidence_count=rag_response.evidence_count,
        execution_time_seconds=rag_response.execution_time_seconds,
    )


@router.post(
    "/api/v1/translate",
    response_model=LegalTranslationResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input or unsupported language."},
        503: {"model": ErrorResponse, "description": "Translation service unavailable."},
    },
    summary="Translate Legal Answer",
    description="Translates an evidence-grounded legal answer to Tamil, Hindi, Kannada, or Marathi with protected entity preservation and deterministic verification.",
    tags=["Multilingual Representation"],
)
async def legal_translate(request: LegalTranslationRequest) -> LegalTranslationResponse:
    """
    Multilingual legal representation endpoint preserving legal entities and evidence.
    """
    import urllib.request
    import json

    clean_answer = request.english_answer.strip()
    if not clean_answer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "EMPTY_ANSWER",
                    "message": "english_answer cannot be empty.",
                }
            },
        )

    supported = ["ta", "hi", "kn", "mr"]
    tgt_lang = request.target_language.lower().strip()
    if tgt_lang not in supported:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "UNSUPPORTED_LANGUAGE",
                    "message": f"Unsupported language '{request.target_language}'. Supported: {supported}",
                }
            },
        )

    # 1. Forward to translation daemon or AI gateway
    import os
    daemon_url = os.environ.get("TRANSLATION_DAEMON_URL")
    if not daemon_url and os.environ.get("AI_GATEWAY_URL"):
        clean_gw = os.environ.get("AI_GATEWAY_URL", "").rstrip("/")
        daemon_url = clean_gw if clean_gw.endswith("/api/translate") else (clean_gw if clean_gw.endswith("/translate") else f"{clean_gw}/api/translate")
    if not daemon_url:
        daemon_url = "http://127.0.0.1:8009/translate"

    req_headers = {
        "Content-Type": "application/json; charset=utf-8",
        "ngrok-skip-browser-warning": "true",
    }
    gw_token = os.environ.get("AI_GATEWAY_TOKEN", os.environ.get("GATEWAY_TOKEN", ""))
    if gw_token:
        req_headers["Authorization"] = f"Bearer {gw_token}"
        req_headers["x-gateway-token"] = gw_token

    req_body = json.dumps({
        "english_answer": clean_answer,
        "target_language": tgt_lang,
        "matter_id": request.matter_id or "GLOBAL",
        "evidence": request.evidence or [],
        "claims": request.claims or [],
    }).encode("utf-8")

    try:
        http_req = urllib.request.Request(
            daemon_url,
            data=req_body,
            headers=req_headers,
            method="POST",
        )
        with urllib.request.urlopen(http_req, timeout=30.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return LegalTranslationResponse(**data)
    except urllib.error.HTTPError as he:
        err_body = he.read().decode("utf-8")
        try:
            err_json = json.loads(err_body)
            msg = err_json.get("error", str(he))
        except Exception:
            msg = str(he)
        raise HTTPException(
            status_code=he.code,
            detail={"error": {"code": "TRANSLATION_ERROR", "message": msg}},
        )
    except Exception as e:
        logger.error(f"Translation daemon unreachable: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": {
                    "code": "TRANSLATION_SERVICE_UNAVAILABLE",
                    "message": "The multilingual translation service daemon (port 8009) is unavailable.",
                }
            },
        )

