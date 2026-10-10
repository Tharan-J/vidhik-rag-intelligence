"""
Vidhik Ingestion Subsystem
==========================
Production-grade legal document ingestion pipeline for 1,361 Indian Court judgments
into Qdrant Cloud ('vidhik_legal_chunks') with BGE-M3 dense and sparse representations.
"""

from .config import IngestionConfig, load_config
from .extract import extract_document
from .normalize import normalize_legal_text
from .structure import build_document_structure
from .chunk import chunk_document
from .embed import BGEM3EmbeddingEngine
from .qdrant_store import QdrantCloudStore
from .bm25_store import BM25Store, tokenize_legal_text, fuse_results
from .manifest import IngestionManifest
from .pipeline import IngestionPipeline

__all__ = [
    "IngestionConfig",
    "load_config",
    "extract_document",
    "normalize_legal_text",
    "build_document_structure",
    "chunk_document",
    "BGEM3EmbeddingEngine",
    "QdrantCloudStore",
    "BM25Store",
    "tokenize_legal_text",
    "fuse_results",
    "IngestionManifest",
    "IngestionPipeline",
]
