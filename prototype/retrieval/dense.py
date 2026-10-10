"""
Dense Retrieval Subsystem (BGE-M3 + Qdrant Cloud)
=================================================
Performs dense semantic vector retrieval:
1. Encodes query text into a normalized 1024-dimensional dense vector via BGE-M3.
2. Queries the Qdrant Cloud collection 'vidhik_legal_chunks' via named vector 'dense' (Cosine distance).
3. Returns ranked candidates as RetrievalResult instances with full provenance metadata.
4. Supports batch payload hydration for BM25 hits via point ID lookup.
"""

import time
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

from qdrant_client import QdrantClient

from ingestion.embed import BGEM3EmbeddingEngine
from .models import RetrievalResult
from .config import DenseRetrievalConfig, ModelEmbeddingConfig, load_retrieval_config

logger = logging.getLogger("VidhikRetrieval.Dense")


class DenseRetriever:
    """
    Production-grade dense retriever combining BGE-M3 dense embeddings and Qdrant Cloud.
    """

    def __init__(
        self,
        config: Optional[DenseRetrievalConfig] = None,
        embedding_config: Optional[ModelEmbeddingConfig] = None,
        embed_engine: Optional[BGEM3EmbeddingEngine] = None,
        client: Optional[QdrantClient] = None,
    ):
        if config is None or embedding_config is None:
            full_cfg = load_retrieval_config()
            self.config = config or full_cfg.dense
            self.embedding_config = embedding_config or full_cfg.embedding
        else:
            self.config = config
            self.embedding_config = embedding_config

        # 1. Initialize BGE-M3 Embedding Engine (once)
        if embed_engine is not None:
            self.embed_engine = embed_engine
        else:
            logger.info("Initializing BGE-M3 dense query embedding engine...")
            self.embed_engine = BGEM3EmbeddingEngine(
                model_name=self.embedding_config.model,
                local_model_dir=self.embedding_config.local_model_dir,
                onnx_model_file=self.embedding_config.onnx_model_file,
                tokenizer_file=self.embedding_config.tokenizer_file,
                dense_dim=self.embedding_config.dense_dim,
                max_length=self.embedding_config.max_length,
            )

        # 2. Initialize Qdrant Client (once)
        self.client = client
        if self.client is None:
            self._init_qdrant_client()

    def _init_qdrant_client(self):
        """Establish connection to Qdrant Cloud."""
        if not self.config.url or not self.config.api_key:
            raise ValueError("Qdrant URL and API key must be provided in environment or config.")

        parsed = urlparse(self.config.url)
        port_to_use = parsed.port if parsed.port else self.config.port

        logger.info(f"Connecting to Qdrant Cloud at host={parsed.hostname}, port={port_to_use}...")
        self.client = QdrantClient(
            url=self.config.url,
            api_key=self.config.api_key,
            https=self.config.https,
            port=port_to_use,
            timeout=self.config.timeout,
            check_compatibility=False,
        )

    def encode_query(self, query: str) -> List[float]:
        """Encode query text into a 1024-d normalized dense vector."""
        if not query or not query.strip():
            raise ValueError("Query string cannot be empty.")
        return self.embed_engine.encode_query(query.strip())

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
    ) -> List[RetrievalResult]:
        """
        Execute dense search on Qdrant Cloud collection.
        Returns top_k RetrievalResult objects.
        """
        limit = top_k if top_k is not None else self.config.top_k
        if limit <= 0:
            return []

        # Generate query dense vector
        query_vector = self.encode_query(query)

        # Query Qdrant with exponential backoff on transient network faults
        response = None
        last_err = None
        for attempt in range(1, 4):
            try:
                response = self.client.query_points(
                    collection_name=self.config.collection_name,
                    query=query_vector,
                    using=self.config.vector_name,
                    limit=limit,
                    with_payload=True,
                    with_vectors=False,
                )
                break
            except Exception as e:
                last_err = e
                logger.warning(f"Qdrant query attempt {attempt} failed: {e}; retrying...")
                time.sleep(1.0 * attempt)
        else:
            raise RuntimeError(f"Qdrant query failed after 3 attempts: {last_err}") from last_err

        results: List[RetrievalResult] = []
        for rank, pt in enumerate(response.points, start=1):
            payload = pt.payload or {}
            chunk_id = payload.get("chunk_id", "")
            doc_id = payload.get("document_id", "")
            text = payload.get("text", "")
            court = payload.get("court", payload.get("court_level", ""))

            res = RetrievalResult(
                chunk_id=chunk_id,
                document_id=doc_id,
                score=float(pt.score),
                retrieval_method="dense",
                text=text,
                qdrant_point_id=str(pt.id),
                rank=rank,
                source=court,
                metadata=payload,
            )
            results.append(res)

        logger.debug(f"Dense search retrieved {len(results)} points for query.")
        return results

    def retrieve_payloads_by_point_ids(
        self,
        point_ids: List[str],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Batch retrieve payloads from Qdrant Cloud for the specified point IDs.
        Used to hydrate complete provenance metadata for BM25 candidates.
        """
        if not point_ids:
            return {}

        payload_map: Dict[str, Dict[str, Any]] = {}
        # Batch in chunks of 100 to avoid payload size limits
        batch_size = 100
        for i in range(0, len(point_ids), batch_size):
            batch = point_ids[i:i + batch_size]
            last_err = None
            for attempt in range(1, 4):
                try:
                    pts = self.client.retrieve(
                        collection_name=self.config.collection_name,
                        ids=batch,
                        with_payload=True,
                        with_vectors=False,
                    )
                    for pt in pts:
                        payload_map[str(pt.id)] = pt.payload or {}
                    break
                except Exception as e:
                    last_err = e
                    logger.warning(f"Qdrant retrieve attempt {attempt} failed: {e}; retrying...")
                    time.sleep(1.0 * attempt)
            else:
                logger.error(f"Failed to batch retrieve points from Qdrant: {last_err}")

        return payload_map

    def verify_connection(self) -> Dict[str, Any]:
        """Health check on Qdrant Cloud cluster connection."""
        info = self.client.get_collection(self.config.collection_name)
        return {
            "status": "connected",
            "collection": self.config.collection_name,
            "points_count": info.points_count,
            "dense_vector_name": self.config.vector_name,
        }
