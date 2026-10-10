"""
Vidhik Hybrid Retrieval Package
===============================
Provides dense (BGE-M3 + Qdrant Cloud), sparse (BM25 persistent index),
and Reciprocal Rank Fusion (RRF) for legal evidence retrieval.
"""

from .models import RetrievalResult, HybridRetrievalResult
from .config import RetrievalConfig, load_retrieval_config
from .dense import DenseRetriever
from .bm25 import BM25Retriever
from .fusion import reciprocal_rank_fusion
from .engine import HybridRetrievalEngine

__all__ = [
    "HybridRetrievalEngine",
    "DenseRetriever",
    "BM25Retriever",
    "reciprocal_rank_fusion",
    "RetrievalResult",
    "HybridRetrievalResult",
    "RetrievalConfig",
    "load_retrieval_config",
]
