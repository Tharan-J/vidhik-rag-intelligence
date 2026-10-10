"""
RAG Configuration Subsystem
===========================
Loads and validates configurations for the Evidence + RAG stage from config/rag.yaml.
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import yaml

PROTOTYPE_DIR = Path(__file__).resolve().parent.parent


@dataclass
class RetrievalRAGConfig:
    top_k: int = 20


@dataclass
class EvidenceConfig:
    max_evidence_chunks: int = 8
    min_rrf_score_threshold: float = 0.005
    deduplicate_by_chunk_id: bool = True


@dataclass
class ContextConfig:
    max_tokens: int = 3500
    format: str = "labeled_brackets"


@dataclass
class GeneratorConfig:
    provider: str = "ollama"
    endpoint: str = "http://localhost:11434/api/generate"
    model: str = "qwen3:4b-instruct"
    temperature: float = 0.0
    top_p: float = 0.95
    max_tokens: int = 800
    timeout: float = 120.0


@dataclass
class GroundingConfig:
    require_evidence: bool = True
    allow_unsupported_claims: bool = False
    insufficient_evidence_threshold: int = 1


@dataclass
class RAGConfig:
    retrieval: RetrievalRAGConfig
    evidence: EvidenceConfig
    context: ContextConfig
    generator: GeneratorConfig
    grounding: GroundingConfig
    log_dir: Path = field(default_factory=lambda: PROTOTYPE_DIR / "logs")
    log_file: str = "rag.log"
    level: str = "INFO"


def load_rag_config(config_path: Optional[Path] = None) -> RAGConfig:
    """Load configuration for the Vidhik Legal RAG system."""
    if config_path is None:
        config_path = PROTOTYPE_DIR / "config" / "rag.yaml"

    raw_cfg = {}
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            raw_cfg = yaml.safe_load(f) or {}

    r_cfg = raw_cfg.get("retrieval", {})
    e_cfg = raw_cfg.get("evidence", {})
    c_cfg = raw_cfg.get("context", {})
    g_cfg = raw_cfg.get("generator", {})
    gr_cfg = raw_cfg.get("grounding", {})
    l_cfg = raw_cfg.get("logging", {})

    def resolve_p(p_str: str) -> Path:
        p = Path(p_str)
        if not p.is_absolute():
            return (PROTOTYPE_DIR / p).resolve()
        return p

    return RAGConfig(
        retrieval=RetrievalRAGConfig(
            top_k=int(r_cfg.get("top_k", 20)),
        ),
        evidence=EvidenceConfig(
            max_evidence_chunks=int(e_cfg.get("max_evidence_chunks", 8)),
            min_rrf_score_threshold=float(e_cfg.get("min_rrf_score_threshold", 0.005)),
            deduplicate_by_chunk_id=bool(e_cfg.get("deduplicate_by_chunk_id", True)),
        ),
        context=ContextConfig(
            max_tokens=int(c_cfg.get("max_tokens", 3500)),
            format=str(c_cfg.get("format", "labeled_brackets")),
        ),
        generator=GeneratorConfig(
            provider=str(g_cfg.get("provider", "ollama")),
            endpoint=str(g_cfg.get("endpoint", "http://localhost:11434/api/generate")),
            model=str(g_cfg.get("model", "qwen3:4b-instruct")),
            temperature=float(g_cfg.get("temperature", 0.0)),
            top_p=float(g_cfg.get("top_p", 0.95)),
            max_tokens=int(g_cfg.get("max_tokens", 800)),
            timeout=float(g_cfg.get("timeout", 60.0)),
        ),
        grounding=GroundingConfig(
            require_evidence=bool(gr_cfg.get("require_evidence", True)),
            allow_unsupported_claims=bool(gr_cfg.get("allow_unsupported_claims", False)),
            insufficient_evidence_threshold=int(gr_cfg.get("insufficient_evidence_threshold", 1)),
        ),
        log_dir=resolve_p(l_cfg.get("log_dir", "logs")),
        log_file=str(l_cfg.get("log_file", "rag.log")),
        level=str(l_cfg.get("level", "INFO")),
    )
