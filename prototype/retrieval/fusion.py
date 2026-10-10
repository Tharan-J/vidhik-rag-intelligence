"""
Reciprocal Rank Fusion (RRF) Subsystem
======================================
Fuses ranked candidates from Dense vector retrieval and BM25 lexical retrieval.
Implements the standard unweighted RRF formula:
    RRF(d) = Σ 1 / (k + rank(d))
with established parameter k = 60.

Deduplicates results using deterministic point IDs (UUIDv5) / (document_id + chunk_id).
Preserves dense rank, BM25 rank, raw scores, RRF score, and all provenance payload metadata.
"""

import logging
from typing import List, Dict, Any, Optional

from .models import RetrievalResult, HybridRetrievalResult

logger = logging.getLogger("VidhikRetrieval.Fusion")


def reciprocal_rank_fusion(
    dense_results: List[RetrievalResult],
    bm25_results: List[RetrievalResult],
    k: int = 60,
    top_k: Optional[int] = None,
    payload_cache: Optional[Dict[str, Dict[str, Any]]] = None,
) -> List[HybridRetrievalResult]:
    """
    Fuse dense and BM25 ranked candidate lists using standard Reciprocal Rank Fusion.
    
    Args:
        dense_results: Scored and ranked results from DenseRetriever (1-indexed ranks).
        bm25_results: Scored and ranked results from BM25Retriever (1-indexed ranks).
        k: Smoothing constant (default: 60).
        top_k: Number of final fused candidates to return. If None, returns all deduplicated candidates.
        payload_cache: Optional pre-fetched full Qdrant payloads for BM25 candidates.
    
    Returns:
        List of HybridRetrievalResult sorted in descending order of RRF score.
    """
    scores: Dict[str, float] = {}
    dense_ranks: Dict[str, int] = {}
    dense_scores: Dict[str, float] = {}
    bm25_ranks: Dict[str, int] = {}
    bm25_scores: Dict[str, float] = {}
    
    # Track candidate models / payloads
    candidates: Dict[str, Dict[str, Any]] = {}

    # 1. Process Dense Results
    for rank, item in enumerate(dense_results, start=1):
        uid = item.qdrant_point_id or f"{item.document_id}_{item.chunk_id}"
        dense_ranks[uid] = rank
        dense_scores[uid] = item.score
        scores[uid] = scores.get(uid, 0.0) + (1.0 / (k + rank))
        candidates[uid] = {
            "chunk_id": item.chunk_id,
            "document_id": item.document_id,
            "qdrant_point_id": item.qdrant_point_id or uid,
            "text": item.text,
            "metadata": dict(item.metadata),
        }

    # 2. Process BM25 Results
    for rank, item in enumerate(bm25_results, start=1):
        uid = item.qdrant_point_id or f"{item.document_id}_{item.chunk_id}"
        bm25_ranks[uid] = rank
        bm25_scores[uid] = item.score
        scores[uid] = scores.get(uid, 0.0) + (1.0 / (k + rank))
        if uid not in candidates:
            candidates[uid] = {
                "chunk_id": item.chunk_id,
                "document_id": item.document_id,
                "qdrant_point_id": item.qdrant_point_id or uid,
                "text": item.text,
                "metadata": dict(item.metadata),
            }
        else:
            # If candidate was in dense results, merge any additional metadata
            candidates[uid]["metadata"].update({
                "bm25_score": item.score,
                "bm25_rank": rank,
            })

    # 3. Sort candidates by RRF score descending
    sorted_uids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    if top_k is not None and top_k > 0:
        sorted_uids = sorted_uids[:top_k]

    # 4. Construct HybridRetrievalResult instances preserving full provenance
    fused_results: List[HybridRetrievalResult] = []
    for final_rank, uid in enumerate(sorted_uids, start=1):
        cand = candidates[uid]
        meta = cand["metadata"]

        # Incorporate payload_cache if provided (e.g. hydrated from Qdrant)
        if payload_cache and uid in payload_cache:
            meta = {**payload_cache[uid], **meta}

        # Provenance fields extracted from metadata
        doc_id = meta.get("document_id", cand["document_id"])
        chk_id = meta.get("chunk_id", cand["chunk_id"])
        court_level = meta.get("court_level", "Unknown")
        court = meta.get("court", "Unknown")
        case_title = meta.get("case_title", "Unknown")
        case_number = meta.get("case_number", "Unknown")
        decision_date = str(meta.get("decision_date", "Unknown"))
        year = meta.get("year")
        if year is not None:
            try:
                year = int(year)
            except (ValueError, TypeError):
                year = None

        judges = meta.get("judges") or meta.get("judge")
        document_type = meta.get("document_type")
        language = meta.get("language", "en")
        source_file = meta.get("source_file", "")
        document_sha256 = meta.get("document_sha256", "")

        try:
            page_start = int(meta.get("page_start", 1))
        except (ValueError, TypeError):
            page_start = 1

        try:
            page_end = int(meta.get("page_end", page_start))
        except (ValueError, TypeError):
            page_end = page_start

        paragraph_start = str(meta.get("paragraph_start", ""))
        paragraph_end = str(meta.get("paragraph_end", paragraph_start))
        sentence_start = str(meta.get("sentence_start", ""))
        sentence_end = str(meta.get("sentence_end", sentence_start))
        
        try:
            token_count = int(meta.get("token_count", 0))
        except (ValueError, TypeError):
            token_count = 0

        sentence_ids = meta.get("sentence_ids", [])
        paragraph_ids = meta.get("paragraph_ids", [])
        text = cand["text"] or meta.get("text", "")

        hybrid_item = HybridRetrievalResult(
            chunk_id=chk_id,
            document_id=doc_id,
            qdrant_point_id=cand["qdrant_point_id"],
            text=text,
            rrf_score=float(scores[uid]),
            rrf_rank=final_rank,
            dense_score=dense_scores.get(uid),
            dense_rank=dense_ranks.get(uid),
            bm25_score=bm25_scores.get(uid),
            bm25_rank=bm25_ranks.get(uid),
            court_level=court_level,
            court=court,
            case_title=case_title,
            case_number=case_number,
            decision_date=decision_date,
            year=year,
            judges=judges,
            document_type=document_type,
            language=language,
            source_file=source_file,
            document_sha256=document_sha256,
            page_start=page_start,
            page_end=page_end,
            paragraph_start=paragraph_start,
            paragraph_end=paragraph_end,
            sentence_start=sentence_start,
            sentence_end=sentence_end,
            token_count=token_count,
            sentence_ids=sentence_ids,
            paragraph_ids=paragraph_ids,
            metadata=meta,
        )
        fused_results.append(hybrid_item)

    logger.debug(f"RRF fusion produced {len(fused_results)} ranked candidates.")
    return fused_results
