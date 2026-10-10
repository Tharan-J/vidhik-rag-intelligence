"""
Vidhik Legal RAG Engine Package
===============================
Provides evidence selection, context assembly, Qwen generation,
and claim-level provenance tracking for Indian legal question answering.
"""

from .config import RAGConfig, load_rag_config
from .evidence import EvidenceItem, EvidenceSelector
from .context import ContextBuilder, ContextBundle
from .generator import QwenGenerator, RawGenerationOutput
from .provenance import CitationAuthority, ClaimWithProvenance, ProvenanceResolver
from .engine import LegalRAGEngine, LegalRAGResponse

__all__ = [
    "LegalRAGEngine",
    "LegalRAGResponse",
    "EvidenceItem",
    "EvidenceSelector",
    "ContextBuilder",
    "ContextBundle",
    "QwenGenerator",
    "RawGenerationOutput",
    "CitationAuthority",
    "ClaimWithProvenance",
    "ProvenanceResolver",
    "RAGConfig",
    "load_rag_config",
]
