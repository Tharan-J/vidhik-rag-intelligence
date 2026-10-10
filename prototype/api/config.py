"""
Vidhik API Configuration Loader
===============================
Loads API server, CORS, and endpoint configurations from config/api.yaml
with support for environment variable overrides.
"""

import os
import json
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ServerConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    workers: int = 1
    timeout_seconds: float = 180.0


@dataclass
class CORSConfig:
    allowed_origins: List[str] = field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ]
    )
    allow_credentials: bool = True
    allow_methods: List[str] = field(
        default_factory=lambda: ["GET", "POST", "OPTIONS"]
    )
    allow_headers: List[str] = field(
        default_factory=lambda: ["Content-Type", "Authorization", "Accept"]
    )


@dataclass
class AppMetaConfig:
    title: str = "Vidhik Legal RAG API"
    description: str = "Production API for evidence-grounded Indian legal research powered by Hybrid Retrieval and Qwen."
    version: str = "1.0.0"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"


@dataclass
class APIConfig:
    server: ServerConfig = field(default_factory=ServerConfig)
    cors: CORSConfig = field(default_factory=CORSConfig)
    app: AppMetaConfig = field(default_factory=AppMetaConfig)


def load_api_config(config_path: Optional[Path] = None) -> APIConfig:
    """
    Load API configuration from YAML file and apply environment variable overrides.
    """
    cfg_file = config_path or Path(__file__).resolve().parent.parent / "config" / "api.yaml"
    raw: dict = {}

    if cfg_file.exists():
        with open(cfg_file, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}

    server_raw = raw.get("server", {})
    cors_raw = raw.get("cors", {})
    app_raw = raw.get("app", {})

    # Environment variable overrides
    host = os.environ.get("VIDHIK_API_HOST") or os.environ.get("HOST") or server_raw.get("host", "0.0.0.0")
    port_env = os.environ.get("VIDHIK_API_PORT") or os.environ.get("PORT")
    port = int(port_env) if port_env else int(server_raw.get("port", 8000))
    timeout_env = os.environ.get("VIDHIK_API_TIMEOUT")
    timeout = float(timeout_env) if timeout_env else float(server_raw.get("timeout_seconds", 180.0))

    cors_env = os.environ.get("VIDHIK_CORS_ORIGINS")
    if cors_env:
        try:
            allowed_origins = json.loads(cors_env)
        except json.JSONDecodeError:
            allowed_origins = [orig.strip() for orig in cors_env.split(",") if orig.strip()]
    else:
        allowed_origins = cors_raw.get("allowed_origins", [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ])

    return APIConfig(
        server=ServerConfig(
            host=host,
            port=port,
            reload=bool(server_raw.get("reload", False)),
            workers=int(server_raw.get("workers", 1)),
            timeout_seconds=timeout,
        ),
        cors=CORSConfig(
            allowed_origins=allowed_origins,
            allow_credentials=bool(cors_raw.get("allow_credentials", True)),
            allow_methods=cors_raw.get("allow_methods", ["GET", "POST", "OPTIONS"]),
            allow_headers=cors_raw.get("allow_headers", ["Content-Type", "Authorization", "Accept"]),
        ),
        app=AppMetaConfig(
            title=app_raw.get("title", "Vidhik Legal RAG API"),
            description=app_raw.get("description", "Production API for evidence-grounded Indian legal research powered by Hybrid Retrieval and Qwen."),
            version=app_raw.get("version", "1.0.0"),
            docs_url=app_raw.get("docs_url", "/docs"),
            redoc_url=app_raw.get("redoc_url", "/redoc"),
            openapi_url=app_raw.get("openapi_url", "/openapi.json"),
        ),
    )
