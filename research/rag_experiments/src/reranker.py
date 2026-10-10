"""
Cross-Encoder Reranker for Vidhik Phase 3
Uses BAAI/bge-reranker-base via FastEmbed for high-precision neural reranking over hybrid candidate pools.
"""

import logging
from fastembed.rerank.cross_encoder import TextCrossEncoder

logger = logging.getLogger("CrossEncoder_Reranker")


class LegalCrossEncoderReranker:
    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        self.model_name = model_name
        self.encoder = TextCrossEncoder(model_name=model_name)
        logger.info("Initialized Cross-Encoder with %s", model_name)

    def rerank(self, query: str, candidate_chunks: list[dict], top_k: int = 10) -> list[dict]:
        if not candidate_chunks:
            return []
            
        # Truncate text to standard cross-encoder window (600 chars) to prevent O(N^2) attention slowdown
        docs = [c["text"][:600] for c in candidate_chunks]
        scores = list(self.encoder.rerank(query, docs))
        
        # Sort candidate chunks by cross-encoder score descending
        ranked = sorted(zip(candidate_chunks, scores), key=lambda x: x[1], reverse=True)[:top_k]
        
        reranked_hits = []
        for rank, (chunk, score) in enumerate(ranked, start=1):
            hit = dict(chunk)
            hit["rerank_score"] = float(score)
            hit["rerank_rank"] = rank
            reranked_hits.append(hit)
            
        return reranked_hits
