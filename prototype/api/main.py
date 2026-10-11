"""
Vidhik Legal RAG FastAPI Application
====================================
Factory and entrypoint for the Vidhik backend REST API server.
Configures lifespan lifecycle, CORS middleware, OpenAPI documentation,
and unified error handling envelopes.
"""

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from rag.engine import LegalRAGEngine
from .config import APIConfig, load_api_config
from .routes import router

logger = logging.getLogger("VidhikAPI")


def get_process_rss_mb() -> float:
    """Return process resident set size (RSS) in megabytes."""
    try:
        import psutil
        return psutil.Process().memory_info().rss / (1024 * 1024)
    except Exception:
        return 0.0


def log_memory_checkpoint(label: str) -> float:
    rss = get_process_rss_mb()
    msg = f"[MEMORY CHECKPOINT] {label}: RSS={rss:.2f} MiB"
    print(msg, flush=True)
    logger.info(msg)
    return rss


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Initializes the LegalRAGEngine (and its underlying BGE-M3 model,
    Qdrant client, and BM25 index) once on server startup.
    """
    logger.info("Initializing Vidhik API server lifecycle...")
    log_memory_checkpoint("FastAPI lifespan start")
    if not hasattr(app.state, "engine") or app.state.engine is None:
        try:
            logger.info("Instantiating LegalRAGEngine on startup...")
            app.state.engine = LegalRAGEngine()
            log_memory_checkpoint("FastAPI application startup completion")
            logger.info("LegalRAGEngine initialized and attached to app state.")
        except Exception as e:
            logger.error(f"Failed to initialize LegalRAGEngine on startup: {e}", exc_info=True)
            # Still allow the app to boot so /health can report status
            app.state.engine = None
    else:
        logger.info("LegalRAGEngine already present on app state (injected).")
        log_memory_checkpoint("FastAPI application startup completion (injected engine)")

    yield

    logger.info("Shutting down Vidhik API server...")


def create_app(
    engine: Optional[LegalRAGEngine] = None,
    config: Optional[APIConfig] = None,
) -> FastAPI:
    """
    Application factory. Allows dependency injection for tests and custom runners.
    """
    api_config = config or load_api_config()

    app = FastAPI(
        title=api_config.app.title,
        description=api_config.app.description,
        version=api_config.app.version,
        docs_url=api_config.app.docs_url,
        redoc_url=api_config.app.redoc_url,
        openapi_url=api_config.app.openapi_url,
        lifespan=app_lifespan,
    )

    # Attach injected engine if supplied
    if engine is not None:
        app.state.engine = engine

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=api_config.cors.allowed_origins,
        allow_credentials=api_config.cors.allow_credentials,
        allow_methods=api_config.cors.allow_methods,
        allow_headers=api_config.cors.allow_headers,
    )

    # Global Exception Handlers
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        detail = exc.detail
        if isinstance(detail, dict) and "error" in detail:
            return JSONResponse(status_code=exc.status_code, content=detail)
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": str(detail),
                    "details": None,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        formatted_errors = []
        for err in exc.errors():
            loc = " -> ".join(str(p) for p in err.get("loc", []))
            formatted_errors.append(f"{loc}: {err.get('msg')}")

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid request parameters.",
                    "details": formatted_errors,
                }
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled server exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An internal server error occurred.",
                    "details": None,
                }
            },
        )

    # Include routes
    app.include_router(router)

    return app


# Module-level instance for uvicorn run
app = create_app()
