"""
BM25 Sparse Retrieval Engine for Vidhik Phase 3
Uses rank_bm25 with Indian legal-aware tokenization.
"""

import re
import logging
from rank_bm25 import BM25Okapi

logger = logging.getLogger("BM25_Retriever")


def tokenize_legal_text(text: str) -> list[str]:
    """Tokenize legal text preserving citations, sections, and legal abbreviations."""
    # Convert to lowercase
    text = text.lower()
    # Normalize slashes in citations like u/s, cr.p.c, 174/10
    text = re.sub(r'(\w+)/(\w+)', r'\1 \2 \1/\2', text)
    # Split on non-alphanumeric except slashes and periods inside numbers
    tokens = re.findall(r'[a-z0-9_\.\/-]+', text)
    # Remove isolated periods or hyphens
    clean_tokens = [t.strip('.-') for t in tokens if len(t.strip('.-')) > 1]
    return clean_tokens


class BM25Retriever:
    def __init__(self, k1: float = 1.5, b: float = 0.75, epsilon: float = 0.25):
        self.k1 = k1
        self.b = b
        self.epsilon = epsilon
        self.bm25 = None
        self.chunks = []
        self.corpus_tokens = []

    def index_chunks(self, chunks: list[dict]):
        self.chunks = chunks
        self.corpus_tokens = [tokenize_legal_text(c["text"]) for c in chunks]
        self.bm25 = BM25Okapi(self.corpus_tokens, k1=self.k1, b=self.b, epsilon=self.epsilon)
        logger.info("Indexed %d chunks with BM25 (k1=%.2f, b=%.2f)", len(chunks), self.k1, self.b)

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        query_tokens = tokenize_legal_text(query)
        if not query_tokens:
            return []
        scores = self.bm25.get_scores(query_tokens)
        
        # Rank by score descending
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        
        hits = []
        for rank, idx in enumerate(ranked_indices, start=1):
            chunk = dict(self.chunks[idx])
            chunk["score"] = float(scores[idx])
            chunk["bm25_rank"] = rank
            hits.append(chunk)
            
        return hits
