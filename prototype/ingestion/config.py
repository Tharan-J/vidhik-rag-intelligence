"""
Configuration Loader and Environment Validator for Vidhik Ingestion
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import yaml

# Search paths for .env
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
class CorpusConfig:
    master_metadata_parquet: Path
    master_metadata_csv: Path
    district_structure_dir: Path
    legal_data_dir: Path
    target_documents: int = 1361


@dataclass
class ExtractionConfig:
    primary_engine: str = "pymupdf"
    min_page_chars: int = 30
    ocr_fallback: str = "paddleocr"
    ocr_confidence_threshold: float = 0.5


@dataclass
class NormalizationConfig:
    repair_line_wraps: bool = True
    collapse_repeated_whitespace: bool = True
    preserve_legal_entities: bool = True


@dataclass
class ChunkingConfig:
    target_tokens: int = 500
    min_tokens: int = 250
    max_tokens: int = 700
    overlap_tokens: int = 75
    respect_paragraph_boundaries: bool = True
    respect_sentence_boundaries: bool = True


@dataclass
class EmbeddingConfig:
    model: str = "BAAI/bge-m3"
    dense_dim: int = 1024
    batch_size: int = 32
    max_length: int = 8192
    local_model_dir: Path = field(default_factory=lambda: REPO_ROOT / "research" / "rag_experiments" / "indexes" / "models" / "bge-m3")
    onnx_model_file: str = "BAAI-bge-m3_quantized.onnx"
    tokenizer_file: str = "tokenizer.json"


@dataclass
class QdrantConfig:
    url: str
    api_key: str
    collection_name: str = "vidhik_legal_chunks"
    dense_vector_name: str = "dense"
    distance: str = "Cosine"
    upsert_batch_size: int = 64
    timeout: float = 30.0
    https: bool = True
    port: int = 443

    @property
    def masked_key(self) -> str:
        if not self.api_key:
            return "<EMPTY>"
        return f"{self.api_key[:6]}...{self.api_key[-4:]}"


@dataclass
class BM25Config:
    index_dir: Path
    index_file: str = "bm25_index.pkl"
    mapping_file: str = "bm25_mapping.parquet"
    k1: float = 1.5
    b: float = 0.75
    epsilon: float = 0.25


@dataclass
class IngestionConfig:
    corpus: CorpusConfig
    extraction: ExtractionConfig
    normalization: NormalizationConfig
    chunking: ChunkingConfig
    embedding: EmbeddingConfig
    qdrant: QdrantConfig
    bm25: BM25Config
    manifest_path: Path
    manifest_csv_path: Path
    log_dir: Path
    base_dir: Path = PROTOTYPE_DIR


def load_config(config_path: Optional[Path] = None) -> IngestionConfig:
    """Load and validate the ingestion pipeline configuration."""
    if config_path is None:
        config_path = PROTOTYPE_DIR / "config" / "ingestion.yaml"

    with open(config_path, "r", encoding="utf-8") as f:
        raw_cfg = yaml.safe_load(f)

    # 1. Load .env credentials
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

    # Determine port and scheme
    parsed_url = urlparse(qdrant_url) if qdrant_url else None
    port = raw_cfg.get("qdrant", {}).get("port", 443)
    if parsed_url and parsed_url.port:
        port = parsed_url.port
    is_https = True
    if parsed_url and parsed_url.scheme == "http":
        is_https = False

    def resolve_p(p_str: str) -> Path:
        p = Path(p_str)
        if not p.is_absolute():
            # Resolve relative to PROTOTYPE_DIR
            resolved = (PROTOTYPE_DIR / p).resolve()
            if not resolved.exists():
                # Try relative to REPO_ROOT
                alt = (REPO_ROOT / p_str.lstrip("./")).resolve()
                if alt.exists():
                    return alt
            return resolved
        return p

    c_cfg = raw_cfg.get("corpus", {})
    corpus = CorpusConfig(
        master_metadata_parquet=resolve_p(c_cfg.get("master_metadata_parquet", "../research/rag_readiness_audit/master_document_audit.parquet")),
        master_metadata_csv=resolve_p(c_cfg.get("master_metadata_csv", "../research/rag_readiness_audit/master_document_audit.csv")),
        district_structure_dir=resolve_p(c_cfg.get("district_structure_dir", "../research/district_extraction/structure/v1")),
        legal_data_dir=resolve_p(c_cfg.get("legal_data_dir", "../research/legal_data")),
        target_documents=c_cfg.get("target_documents", 1361),
    )

    ext_cfg = raw_cfg.get("extraction", {})
    extraction = ExtractionConfig(
        primary_engine=ext_cfg.get("primary_engine", "pymupdf"),
        min_page_chars=ext_cfg.get("min_page_chars", 30),
        ocr_fallback=ext_cfg.get("ocr_fallback", "paddleocr"),
        ocr_confidence_threshold=ext_cfg.get("ocr_confidence_threshold", 0.5),
    )

    norm_cfg = raw_cfg.get("normalization", {})
    normalization = NormalizationConfig(
        repair_line_wraps=norm_cfg.get("repair_line_wraps", True),
        collapse_repeated_whitespace=norm_cfg.get("collapse_repeated_whitespace", True),
        preserve_legal_entities=norm_cfg.get("preserve_legal_entities", True),
    )

    chk_cfg = raw_cfg.get("chunking", {})
    chunking = ChunkingConfig(
        target_tokens=chk_cfg.get("target_tokens", 500),
        min_tokens=chk_cfg.get("min_tokens", 250),
        max_tokens=chk_cfg.get("max_tokens", 700),
        overlap_tokens=chk_cfg.get("overlap_tokens", 75),
        respect_paragraph_boundaries=chk_cfg.get("respect_paragraph_boundaries", True),
        respect_sentence_boundaries=chk_cfg.get("respect_sentence_boundaries", True),
    )

    emb_cfg = raw_cfg.get("embedding", {})
    embedding = EmbeddingConfig(
        model=emb_cfg.get("model", "BAAI/bge-m3"),
        dense_dim=emb_cfg.get("dense_dim", 1024),
        batch_size=emb_cfg.get("batch_size", 32),
        max_length=emb_cfg.get("max_length", 8192),
        local_model_dir=resolve_p(emb_cfg.get("local_model_dir", "../research/rag_experiments/indexes/models/bge-m3")),
        onnx_model_file=emb_cfg.get("onnx_model_file", "BAAI-bge-m3_quantized.onnx"),
        tokenizer_file=emb_cfg.get("tokenizer_file", "tokenizer.json"),
    )

    q_cfg = raw_cfg.get("qdrant", {})
    qdrant = QdrantConfig(
        url=qdrant_url,
        api_key=qdrant_api_key,
        collection_name=q_cfg.get("collection_name", "vidhik_legal_chunks"),
        dense_vector_name=q_cfg.get("dense_vector_name", "dense"),
        distance=q_cfg.get("distance", "Cosine"),
        upsert_batch_size=q_cfg.get("upsert_batch_size", 64),
        timeout=float(q_cfg.get("timeout", 30.0)),
        https=is_https,
        port=port,
    )

    b_cfg = raw_cfg.get("bm25", {})
    bm25 = BM25Config(
        index_dir=resolve_p(b_cfg.get("index_dir", "indexes/bm25")),
        index_file=b_cfg.get("index_file", "bm25_index.pkl"),
        mapping_file=b_cfg.get("mapping_file", "bm25_mapping.parquet"),
        k1=float(b_cfg.get("k1", 1.5)),
        b=float(b_cfg.get("b", 0.75)),
        epsilon=float(b_cfg.get("epsilon", 0.25)),
    )

    m_cfg = raw_cfg.get("manifest", {})
    manifest_path = resolve_p(m_cfg.get("path", "manifests/qdrant_ingestion_manifest.parquet"))
    manifest_csv = resolve_p(m_cfg.get("csv_mirror_path", "manifests/qdrant_ingestion_manifest.csv"))

    log_cfg = raw_cfg.get("logging", {})
    log_dir = resolve_p(log_cfg.get("log_dir", "logs"))

    return IngestionConfig(
        corpus=corpus,
        extraction=extraction,
        normalization=normalization,
        chunking=chunking,
        embedding=embedding,
        qdrant=qdrant,
        bm25=bm25,
        manifest_path=manifest_path,
        manifest_csv_path=manifest_csv,
        log_dir=log_dir,
    )
