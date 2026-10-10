"""
Retrieval Configuration Subsystem
=================================
Loads retrieval configurations from config/retrieval.yaml and environment credentials.
Provides typed configuration dataclasses for Dense, BM25, Fusion, and Embedding.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import yaml

PROTOTYPE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = PROTOTYPE_DIR.parent


def _load_env_file(env_path: Path) -> Dict[str, str]:
    """Parse key=value pairs from a .env file safely."""
    loaded = {}
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("\"'")
                    loaded[key] = val
                    if key not in os.environ:
                        os.environ[key] = val
    return loaded


@dataclass
class DenseRetrievalConfig:
    url: str
    api_key: str
    collection_name: str = "vidhik_legal_chunks"
    vector_name: str = "dense"
    top_k: int = 50
    dimension: int = 1024
    distance: str = "Cosine"
    timeout: float = 30.0
    https: bool = True
    port: int = 443

    @property
    def masked_key(self) -> str:
        if not self.api_key:
            return "<EMPTY>"
        return f"{self.api_key[:6]}...{self.api_key[-4:]}"


@dataclass
class BM25RetrievalConfig:
    index_dir: Path
    index_file: str = "bm25_index.pkl"
    mapping_file: str = "bm25_mapping.parquet"
    top_k: int = 50
    k1: float = 1.5
    b: float = 0.75
    epsilon: float = 0.25


@dataclass
class FusionConfig:
    method: str = "rrf"
    k: int = 60


@dataclass
class ModelEmbeddingConfig:
    model: str = "BAAI/bge-m3"
    dense_dim: int = 1024
    max_length: int = 8192
    local_model_dir: Path = field(default_factory=lambda: REPO_ROOT / "research" / "rag_experiments" / "indexes" / "models" / "bge-m3")
    onnx_model_file: str = "BAAI-bge-m3_quantized.onnx"
    tokenizer_file: str = "tokenizer.json"


@dataclass
class RetrievalConfig:
    dense: DenseRetrievalConfig
    bm25: BM25RetrievalConfig
    fusion: FusionConfig
    embedding: ModelEmbeddingConfig
    final_top_k: int = 20
    log_dir: Path = field(default_factory=lambda: PROTOTYPE_DIR / "logs")
    log_file: str = "retrieval.log"
    level: str = "INFO"


def load_retrieval_config(config_path: Optional[Path] = None) -> RetrievalConfig:
    """Load and validate the retrieval configuration."""
    if config_path is None:
        config_path = PROTOTYPE_DIR / "config" / "retrieval.yaml"

    raw_cfg = {}
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            raw_cfg = yaml.safe_load(f) or {}

    # Load credentials from .env
    env_paths = [
        PROTOTYPE_DIR / ".env",
        REPO_ROOT / ".env",
        REPO_ROOT / "research" / ".env",
    ]
    for ep in env_paths:
        if ep.exists():
            _load_env_file(ep)

    qdrant_url = os.environ.get("QDRANT_URL", "").strip()
    qdrant_api_key = os.environ.get("QDRANT_API_KEY", "").strip()

    parsed_url = urlparse(qdrant_url) if qdrant_url else None
    d_cfg = raw_cfg.get("dense", {})
    port = d_cfg.get("port", 443)
    if parsed_url and parsed_url.port:
        port = parsed_url.port
    is_https = True
    if parsed_url and parsed_url.scheme == "http":
        is_https = False

    def resolve_p(p_str: str) -> Path:
        p = Path(p_str)
        if not p.is_absolute():
            resolved = (PROTOTYPE_DIR / p).resolve()
            if not resolved.exists():
                alt = (REPO_ROOT / p_str.lstrip("./")).resolve()
                if alt.exists():
                    return alt
            return resolved
        return p

    dense_config = DenseRetrievalConfig(
        url=qdrant_url,
        api_key=qdrant_api_key,
        collection_name=d_cfg.get("collection_name", "vidhik_legal_chunks"),
        vector_name=d_cfg.get("vector_name", "dense"),
        top_k=int(d_cfg.get("top_k", 50)),
        dimension=int(d_cfg.get("dimension", 1024)),
        distance=d_cfg.get("distance", "Cosine"),
        timeout=float(d_cfg.get("timeout", 30.0)),
        https=is_https,
        port=port,
    )

    b_cfg = raw_cfg.get("bm25", {})
    bm25_config = BM25RetrievalConfig(
        index_dir=resolve_p(b_cfg.get("index_dir", "indexes/bm25")),
        index_file=b_cfg.get("index_file", "bm25_index.pkl"),
        mapping_file=b_cfg.get("mapping_file", "bm25_mapping.parquet"),
        top_k=int(b_cfg.get("top_k", 50)),
        k1=float(b_cfg.get("k1", 1.5)),
        b=float(b_cfg.get("b", 0.75)),
        epsilon=float(b_cfg.get("epsilon", 0.25)),
    )

    f_cfg = raw_cfg.get("fusion", {})
    fusion_config = FusionConfig(
        method=f_cfg.get("method", "rrf"),
        k=int(f_cfg.get("k", 60)),
    )

    emb_cfg = raw_cfg.get("embedding", {})
    embedding_config = ModelEmbeddingConfig(
        model=emb_cfg.get("model", "BAAI/bge-m3"),
        dense_dim=int(emb_cfg.get("dense_dim", 1024)),
        max_length=int(emb_cfg.get("max_length", 8192)),
        local_model_dir=resolve_p(emb_cfg.get("local_model_dir", "../research/rag_experiments/indexes/models/bge-m3")),
        onnx_model_file=emb_cfg.get("onnx_model_file", "BAAI-bge-m3_quantized.onnx"),
        tokenizer_file=emb_cfg.get("tokenizer_file", "tokenizer.json"),
    )

    final_cfg = raw_cfg.get("final", {})
    final_top_k = int(final_cfg.get("top_k", 20))

    log_cfg = raw_cfg.get("logging", {})
    log_dir = resolve_p(log_cfg.get("log_dir", "logs"))

    return RetrievalConfig(
        dense=dense_config,
        bm25=bm25_config,
        fusion=fusion_config,
        embedding=embedding_config,
        final_top_k=final_top_k,
        log_dir=log_dir,
        log_file=log_cfg.get("log_file", "retrieval.log"),
        level=log_cfg.get("level", "INFO"),
    )
