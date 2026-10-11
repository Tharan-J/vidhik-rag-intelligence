"""
Dense Retrieval Subsystem (BGE-M3 + Qdrant Cloud)
=================================================
Performs dense semantic vector retrieval:
1. Encodes query text into a normalized 1024-dimensional dense vector via
   either the authenticated Laptop AI Gateway (Render production mode) or
   local BGE-M3 engine (laptop / local development mode).
2. Queries the Qdrant Cloud collection 'vidhik_legal_chunks' via named vector 'dense' (Cosine distance).
3. Returns ranked candidates as RetrievalResult instances with full provenance metadata.
4. Supports batch payload hydration for BM25 hits via point ID lookup.
"""

import os
import time
import math
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

from qdrant_client import QdrantClient

from .models import RetrievalResult
from .config import DenseRetrievalConfig, ModelEmbeddingConfig, load_retrieval_config

logger = logging.getLogger("VidhikRetrieval.Dense")


class GatewayEmbeddingUnavailableError(RuntimeError):
    """Raised when the Laptop AI Gateway embedding endpoint is unreachable, timed out, or returns an error."""
    pass


class DenseRetriever:
    """
    Production-grade dense retriever combining BGE-M3 dense embeddings and Qdrant Cloud.
    In Render production mode, query embeddings are requested from the authenticated Laptop AI Gateway.
    """

    def __init__(
        self,
        config: Optional[DenseRetrievalConfig] = None,
        embedding_config: Optional[ModelEmbeddingConfig] = None,
        embed_engine: Optional[Any] = None,
        client: Optional[QdrantClient] = None,
        gateway_url: Optional[str] = None,
        gateway_token: Optional[str] = None,
        remote_mode: Optional[bool] = None,
    ):
        if config is None or embedding_config is None:
            full_cfg = load_retrieval_config()
            self.config = config or full_cfg.dense
            self.embedding_config = embedding_config or full_cfg.embedding
        else:
            self.config = config
            self.embedding_config = embedding_config

        # 1. Configure Gateway Embedding vs Local Model Loading
        env_gateway_url = os.environ.get("AI_GATEWAY_URL", "").rstrip("/")
        env_gateway_token = os.environ.get("AI_GATEWAY_TOKEN", os.environ.get("GATEWAY_TOKEN", ""))
        self.gateway_url = (gateway_url or env_gateway_url).rstrip("/") if (gateway_url or env_gateway_url) else ""
        self.gateway_token = gateway_token or env_gateway_token

        # Auto-detect remote mode if gateway URL is present or explicitly configured
        embedding_mode = os.environ.get("EMBEDDING_MODE", "gateway" if self.gateway_url else "local")
        if remote_mode is not None:
            self.remote_mode = remote_mode
        else:
            self.remote_mode = bool(self.gateway_url) or (embedding_mode == "gateway")

        self.embed_engine = embed_engine
        if not self.remote_mode and self.embed_engine is None:
            # Only eagerly instantiate BGEM3EmbeddingEngine if running purely in local mode
            try:
                from ingestion.embed import BGEM3EmbeddingEngine
                logger.info("Initializing local BGE-M3 dense query embedding engine...")
                self.embed_engine = BGEM3EmbeddingEngine(
                    model_name=self.embedding_config.model,
                    local_model_dir=self.embedding_config.local_model_dir,
                    onnx_model_file=self.embedding_config.onnx_model_file,
                    tokenizer_file=self.embedding_config.tokenizer_file,
                    dense_dim=self.embedding_config.dense_dim,
                    max_length=self.embedding_config.max_length,
                )
            except Exception as e:
                logger.warning(f"Local BGE-M3 engine not loaded: {e}. Dense retrieval will require gateway.")
                self.embed_engine = None

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
        """
        Encode query text into a 1024-d normalized dense vector.
        Obtains embedding from the authenticated laptop gateway if configured,
        or falls back to local engine.
        """
        if not query or not query.strip():
            raise ValueError("Query string cannot be empty.")

        clean_query = query.strip()

        # Gateway Mode (Render Production)
        if self.remote_mode and self.gateway_url:
            headers = {
                "Content-Type": "application/json",
                "ngrok-skip-browser-warning": "true",
            }
            if self.gateway_token:
                headers["Authorization"] = f"Bearer {self.gateway_token}"
                headers["x-gateway-token"] = self.gateway_token

            try:
                import httpx
                endpoint = f"{self.gateway_url}/api/embed"
                with httpx.Client(timeout=8.0) as http_client:
                    resp = http_client.post(
                        endpoint,
                        json={"text": clean_query},
                        headers=headers,
                    )
                if resp.status_code == 200:
                    data = resp.json()
                    vec = data.get("embedding")
                    if (
                        isinstance(vec, list)
                        and len(vec) == self.embedding_config.dense_dim
                        and all(isinstance(x, (int, float)) and not math.isnan(x) and not math.isinf(x) for x in vec)
                    ):
                        return vec
                    raise GatewayEmbeddingUnavailableError(
                        f"Gateway returned invalid embedding format (dimension {len(vec) if isinstance(vec, list) else 'non-list'})."
                    )
                elif resp.status_code == 401:
                    raise GatewayEmbeddingUnavailableError("Laptop AI Gateway rejected authentication token.")
                else:
                    raise GatewayEmbeddingUnavailableError(f"Laptop AI Gateway HTTP {resp.status_code}: {resp.text[:200]}")
            except GatewayEmbeddingUnavailableError:
                raise
            except Exception as e:
                logger.warning(f"Failed to obtain query embedding from laptop gateway ({self.gateway_url}): {e}")
                raise GatewayEmbeddingUnavailableError(f"Laptop AI Gateway unreachable: {e}") from e

        # Local Engine Mode
        if self.embed_engine is not None:
            return self.embed_engine.encode_query(clean_query)

        raise GatewayEmbeddingUnavailableError(
            "Dense query embedding is unavailable: no laptop AI gateway URL configured and local BGE-M3 model is not loaded."
        )

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

        # Generate query dense vector (may raise GatewayEmbeddingUnavailableError)
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
            "remote_mode": self.remote_mode,
            "gateway_configured": bool(self.gateway_url),
        }
