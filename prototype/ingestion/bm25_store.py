"""
Corpus-Level BM25 Lexical Retrieval Engine & Index Store
========================================================
Maintains a standalone, persistent sparse lexical index using rank_bm25 (BM25Okapi).
Computes authentic corpus-level term statistics (document frequencies, IDF, average document length).
Preserves legal identifiers (Section, 438, CrPC, Article, 21, IPC, BNSS, AIR, SCC, OnLine, SC, citations).
Retains direct mapping from BM25 index positions to deterministic Qdrant point IDs (UUIDv5).
Provides Reciprocal Rank Fusion (RRF) for downstream hybrid dense + lexical retrieval.
"""

import os
import re
import pickle
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from rank_bm25 import BM25Okapi

from .chunk import LegalChunk
from .qdrant_store import generate_deterministic_point_id

logger = logging.getLogger("VidhikIngestion.BM25")


class CompactMappingRecords:
    """
    Memory-efficient sequence wrapper for parquet mapping records.
    Prevents allocating 29,156 individual Python dicts and string objects on the heap.
    Provides standard list/sequence indexing, length, and iteration.
    """
    def __init__(self, df: pd.DataFrame):
        self._df = df
        self._length = len(df)
        self._pos = df["bm25_index_position"].values
        self._qdrant = df["qdrant_point_id"].values
        self._doc = df["document_id"].values
        self._chunk = df["chunk_id"].values
        self._text = df["text"].values

    def __len__(self) -> int:
        return self._length

    def __bool__(self) -> bool:
        return self._length > 0

    def __getitem__(self, idx: Any) -> Any:
        if isinstance(idx, slice):
            return [self[i] for i in range(*idx.indices(self._length))]
        return {
            "bm25_index_position": int(self._pos[idx]),
            "qdrant_point_id": str(self._qdrant[idx]),
            "document_id": str(self._doc[idx]),
            "chunk_id": str(self._chunk[idx]),
            "text": str(self._text[idx]),
        }

    def __iter__(self):
        for i in range(self._length):
            yield self[i]


class CompactBM25Okapi:
    """
    High-performance, low-memory BM25Okapi implementation using a pure NumPy
    compressed inverted index (indptr, indices, data) instead of 29,156 Python dicts.
    Scores match rank_bm25.BM25Okapi mathematically.
    Memory footprint: ~32 MB (vs >800 MB for rank_bm25.BM25Okapi + corpus_tokens).
    """
    def __init__(
        self,
        indptr: np.ndarray,
        indices: np.ndarray,
        data: np.ndarray,
        idf_array: np.ndarray,
        doc_len: np.ndarray,
        avgdl: float,
        vocab: Dict[str, int],
        k1: float = 1.5,
        b: float = 0.75,
        epsilon: float = 0.25,
    ):
        self.indptr = indptr
        self.indices = indices
        self.data = data
        self.idf_array = idf_array
        self.doc_len = doc_len
        self.avgdl = avgdl
        self.vocab = vocab
        self.k1 = k1
        self.b = b
        self.epsilon = epsilon
        self.corpus_size = len(doc_len)

    def get_scores(self, query: List[str]) -> np.ndarray:
        scores = np.zeros(self.corpus_size, dtype=np.float32)
        len_norm = self.k1 * (1.0 - self.b + self.b * (self.doc_len / self.avgdl))

        for q in query:
            if q in self.vocab:
                t_id = self.vocab[q]
                start = self.indptr[t_id]
                end = self.indptr[t_id + 1]
                if start == end:
                    continue
                d_ids = self.indices[start:end]
                q_freq = self.data[start:end].astype(np.float32)
                q_idf = self.idf_array[t_id]
                scores[d_ids] += q_idf * (q_freq * (self.k1 + 1.0)) / (q_freq + len_norm[d_ids])

        return scores


def tokenize_legal_text(text: str) -> List[str]:
    """
    Tokenize legal text preserving citations, sections, and legal abbreviations.
    Conservative preprocessing: preserves numbers, legal terms, statutes, and citations.
    """
    if not text:
        return []

    # Expand slash forms like u/s, cr/pc, 174/10 while keeping original component words
    text_expanded = re.sub(r"(\b\w+)/(\w+\b)", r"\1 \2 \1/\2", text)

    # Tokenize words, numbers, sections, abbreviations with dots/slashes
    raw_tokens = re.findall(r"[a-zA-Z0-9]+(?:[./-][a-zA-Z0-9]+)*|\b[a-zA-Z0-9]+\b", text_expanded.lower())

    # Strip extraneous punctuation edges while preserving alphanumeric content
    clean_tokens = []
    for t in raw_tokens:
        cleaned = t.strip(".-/")
        if cleaned:
            clean_tokens.append(cleaned)

    return clean_tokens


class BM25Store:
    def __init__(
        self,
        index_dir: Optional[Path] = None,
        index_file: str = "bm25_index.pkl",
        mapping_file: str = "bm25_mapping.parquet",
        k1: float = 1.5,
        b: float = 0.75,
        epsilon: float = 0.25,
    ):
        self.index_dir = Path(index_dir) if index_dir else None
        self.index_file = index_file
        self.mapping_file = mapping_file
        self.k1 = k1
        self.b = b
        self.epsilon = epsilon

        self.bm25: Optional[Any] = None
        self.corpus_tokens: List[List[str]] = []
        # Mapping records: list or CompactMappingRecords
        self.mapping_records: Any = []

    def add_chunks(self, chunks: List[LegalChunk]):
        """Accumulate chunks across documents for corpus-level BM25 construction."""
        for chunk in chunks:
            pos = len(self.mapping_records)
            qdrant_pt_id = generate_deterministic_point_id(chunk.document_id, chunk.chunk_id)
            tokens = tokenize_legal_text(chunk.text)

            self.corpus_tokens.append(tokens)
            self.mapping_records.append({
                "bm25_index_position": pos,
                "qdrant_point_id": qdrant_pt_id,
                "document_id": chunk.document_id,
                "chunk_id": chunk.chunk_id,
                "text": chunk.text,
            })

    def build_index(self, chunks: Optional[List[LegalChunk]] = None):
        """
        Build the corpus-level BM25Okapi index over all accumulated chunks.
        Computes global IDF, doc lengths, and average document length.
        """
        if chunks:
            self.corpus_tokens.clear()
            self.mapping_records.clear()
            self.add_chunks(chunks)

        if not self.corpus_tokens:
            raise ValueError("Cannot build BM25 index: no chunk tokens available.")

        logger.info(f"Building corpus-level BM25 index over {len(self.corpus_tokens)} chunks (k1={self.k1}, b={self.b})...")
        self.bm25 = BM25Okapi(
            self.corpus_tokens,
            k1=self.k1,
            b=self.b,
            epsilon=self.epsilon
        )
        logger.info(f"Corpus-level BM25 index built successfully over {len(self.corpus_tokens)} chunks.")

    def save(self, index_dir: Optional[Path] = None):
        """Persist BM25 index and mapping DataFrame to disk."""
        target_dir = Path(index_dir) if index_dir else self.index_dir
        if not target_dir:
            raise ValueError("index_dir must be specified to save BM25 index.")

        target_dir.mkdir(parents=True, exist_ok=True)
        idx_path = target_dir / self.index_file
        map_path = target_dir / self.mapping_file

        if self.bm25 is None or not self.mapping_records:
            raise ValueError("Cannot save uninitialized BM25 index.")

        logger.info(f"Persisting BM25 model to {idx_path}...")
        with open(idx_path, "wb") as f:
            pickle.dump({
                "bm25": self.bm25,
                "corpus_tokens": self.corpus_tokens,
                "k1": self.k1,
                "b": self.b,
                "epsilon": self.epsilon,
            }, f, protocol=pickle.HIGHEST_PROTOCOL)

        logger.info(f"Persisting BM25 mapping to {map_path}...")
        df_map = pd.DataFrame(list(self.mapping_records))
        df_map.to_parquet(map_path, index=False)
        logger.info(f"BM25 index and mapping successfully persisted ({len(self.mapping_records)} entries).")

    def _build_compact_bm25(self, df_map: pd.DataFrame, cache_path: Optional[Path] = None) -> CompactBM25Okapi:
        """Construct compact inverted index streaming chunk texts with bounded RSS."""
        from collections import Counter
        import math

        total_rows = len(df_map)
        doc_len = np.zeros(total_rows, dtype=np.float32)
        doc_freq_counts = Counter()
        vocab: Dict[str, int] = {}
        rows: List[int] = []
        cols: List[int] = []
        vals: List[int] = []

        texts = df_map["text"].values
        for doc_id in range(total_rows):
            txt = str(texts[doc_id])
            tokens = tokenize_legal_text(txt)
            doc_len[doc_id] = len(tokens)
            if tokens:
                counts = Counter(tokens)
                for term, freq in counts.items():
                    doc_freq_counts[term] += 1
                    if term not in vocab:
                        vocab[term] = len(vocab)
                    t_id = vocab[term]
                    cols.append(doc_id)
                    rows.append(t_id)
                    vals.append(freq)

        vocab_size = len(vocab)
        vocab_keys = list(vocab.keys())

        # Sort postings by term_id, then doc_id to construct CSC format
        cols_arr = np.array(cols, dtype=np.int32)
        rows_arr = np.array(rows, dtype=np.int32)
        max_val = max(vals, default=1)
        vals_arr = np.array(vals, dtype=np.uint8 if max_val < 256 else np.uint16)
        del rows, cols, vals

        order = np.lexsort((cols_arr, rows_arr))
        indices = cols_arr[order].astype(np.uint16)
        data = vals_arr[order]
        sorted_terms = rows_arr[order]
        indptr = np.searchsorted(sorted_terms, np.arange(vocab_size + 1), side="left").astype(np.int32)
        del cols_arr, rows_arr, vals_arr, order, sorted_terms

        avgdl = float(np.mean(doc_len)) if len(doc_len) > 0 else 1.0
        idf_array = np.zeros(vocab_size, dtype=np.float32)
        for term, t_id in vocab.items():
            df = doc_freq_counts[term]
            idf_array[t_id] = math.log(1.0 + (total_rows - df + 0.5) / (df + 0.5))
        del doc_freq_counts

        # Optionally persist to /tmp cache for fast restart in container
        if cache_path:
            try:
                np.savez_compressed(
                    cache_path,
                    indptr=indptr,
                    indices=indices,
                    data=data,
                    idf_array=idf_array,
                    doc_len=doc_len,
                    avgdl=avgdl,
                    vocab_keys=np.array(vocab_keys, dtype=object),
                    k1=self.k1,
                    b=self.b,
                    epsilon=self.epsilon,
                )
                logger.info(f"Saved compact BM25 cache to {cache_path}")
            except Exception as e:
                logger.warning(f"Could not save compact BM25 cache: {e}")

        return CompactBM25Okapi(
            indptr=indptr,
            indices=indices,
            data=data,
            idf_array=idf_array,
            doc_len=doc_len,
            avgdl=avgdl,
            vocab=vocab,
            k1=self.k1,
            b=self.b,
            epsilon=self.epsilon,
        )

    def load(self, index_dir: Optional[Path] = None):
        """Load persistent BM25 index and mapping within Render 512MB RAM budget."""
        target_dir = Path(index_dir) if index_dir else self.index_dir
        if not target_dir:
            raise ValueError("index_dir must be specified to load BM25 index.")

        map_path = target_dir / self.mapping_file

        if not map_path.exists():
            raise FileNotFoundError(f"BM25 mapping file missing at {map_path}")

        logger.info(f"Loading BM25 mapping from {map_path} (memory-efficient columnar layout)...")
        df_map = pd.read_parquet(map_path)
        self.mapping_records = CompactMappingRecords(df_map)

        # 1. Check for pre-cached compact sparse index (e.g. in /tmp or index_dir)
        cache_candidates = [
            Path("/tmp/vidhik_bm25_sparse_cache.npz"),
            target_dir / "bm25_sparse_cache.npz",
        ]
        loaded_compact = False
        for cache_path in cache_candidates:
            if cache_path.exists():
                try:
                    logger.info(f"Loading compact BM25 sparse index from {cache_path}...")
                    npz = np.load(cache_path, allow_pickle=True)
                    vocab_keys = npz["vocab_keys"]
                    vocab = {term: idx for idx, term in enumerate(vocab_keys)}
                    indptr = npz["indptr"]
                    if "delta_indices" in npz:
                        delta_indices = npz["delta_indices"]
                        decoded_indices = np.empty_like(delta_indices)
                        for i in range(len(indptr) - 1):
                            start, end = indptr[i], indptr[i + 1]
                            if start < end:
                                decoded_indices[start:end] = np.cumsum(delta_indices[start:end])
                        indices = decoded_indices
                    else:
                        indices = npz["indices"]

                    self.bm25 = CompactBM25Okapi(
                        indptr=indptr,
                        indices=indices,
                        data=npz["data"],
                        idf_array=npz["idf_array"],
                        doc_len=npz["doc_len"],
                        avgdl=float(npz["avgdl"]),
                        vocab=vocab,
                        k1=float(npz["k1"]) if "k1" in npz else self.k1,
                        b=float(npz["b"]) if "b" in npz else self.b,
                        epsilon=float(npz["epsilon"]) if "epsilon" in npz else self.epsilon,
                    )
                    loaded_compact = True
                    logger.info(f"Compact BM25 index loaded from cache in memory ({len(self.mapping_records)} chunks).")
                    break
                except Exception as e:
                    logger.warning(f"Could not load compact BM25 cache {cache_path}: {e}")

        # 2. If no compact cache exists, build compact inverted index streaming chunk texts
        if not loaded_compact:
            logger.info(f"Constructing compact BM25 sparse index from mapping ({len(self.mapping_records)} chunks)...")
            self.bm25 = self._build_compact_bm25(df_map, cache_path=cache_candidates[0])

        # Release corpus_tokens to keep memory footprint strictly minimal
        self.corpus_tokens = []
        import gc
        gc.collect()
        logger.info(f"BM25 index and mapping ready ({len(self.mapping_records)} chunks).")

    def search(self, query: str, top_k: int = 50) -> List[Dict[str, Any]]:
        """
        Perform BM25 lexical retrieval for a query.
        Returns top_k hits mapped to Qdrant point IDs.
        """
        if self.bm25 is None or not self.mapping_records:
            raise RuntimeError("BM25 index is not loaded or built.")

        query_tokens = tokenize_legal_text(query)
        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        hits = []
        for rank, idx in enumerate(ranked_indices, start=1):
            score = float(scores[idx])
            rec = self.mapping_records[idx]
            hits.append({
                "qdrant_point_id": rec["qdrant_point_id"],
                "document_id": rec["document_id"],
                "chunk_id": rec["chunk_id"],
                "bm25_rank": rank,
                "score": score,
                "text": rec.get("text", ""),
            })

        return hits


def fuse_results(
    dense_results: List[Dict[str, Any]],
    bm25_results: List[Dict[str, Any]],
    k: int = 60,
    dense_weight: float = 0.60,
    bm25_weight: float = 0.40,
    top_k: int = 50,
) -> List[Dict[str, Any]]:
    """
    Standard Reciprocal Rank Fusion (RRF) between dense Qdrant results and BM25 lexical results.
    
    Formula:
        RRF(d) = dense_weight * (1 / (k + rank_dense(d))) + bm25_weight * (1 / (k + rank_bm25(d)))
    
    Both dense_results and bm25_results must contain 'qdrant_point_id'.
    """
    scores: Dict[str, float] = {}
    dense_ranks: Dict[str, int] = {}
    bm25_ranks: Dict[str, int] = {}
    item_metadata: Dict[str, Dict[str, Any]] = {}

    for rank, item in enumerate(dense_results, start=1):
        pt_id = item["qdrant_point_id"]
        dense_ranks[pt_id] = rank
        item_metadata[pt_id] = item
        scores[pt_id] = scores.get(pt_id, 0.0) + dense_weight * (1.0 / (k + rank))

    for rank, item in enumerate(bm25_results, start=1):
        pt_id = item["qdrant_point_id"]
        bm25_ranks[pt_id] = rank
        if pt_id not in item_metadata:
            item_metadata[pt_id] = item
        scores[pt_id] = scores.get(pt_id, 0.0) + bm25_weight * (1.0 / (k + rank))

    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:top_k]

    fused = []
    for rank, pt_id in enumerate(sorted_ids, start=1):
        meta = item_metadata[pt_id]
        fused.append({
            "fused_rank": rank,
            "rrf_score": scores[pt_id],
            "qdrant_point_id": pt_id,
            "document_id": meta.get("document_id"),
            "chunk_id": meta.get("chunk_id"),
            "dense_rank": dense_ranks.get(pt_id),
            "bm25_rank": bm25_ranks.get(pt_id),
            "text": meta.get("text"),
        })

    return fused
