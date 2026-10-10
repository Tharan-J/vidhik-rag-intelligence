"""
Qdrant Cloud Vector Store Integration Subsystem
===============================================
Collection: 'vidhik_legal_chunks'
Vectors: Named 'dense' (1024-d, Cosine) and 'sparse' (SparseVectorParams)
Point IDs: Strictly deterministic UUIDs generated from document_id + chunk_id.
Operations: Fully idempotent (never destroys or recreates existing collections/data).
"""

import uuid
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    SparseVectorParams,
    SparseIndexParams,
    SparseVector,
    PointStruct,
    PayloadSchemaType,
)

from .chunk import LegalChunk

logger = logging.getLogger("VidhikIngestion.Qdrant")


def generate_deterministic_point_id(document_id: str, chunk_id: str) -> str:
    """
    Generate deterministic UUID from document_id + chunk_id.
    Ensures identical Qdrant point ID across any rerun, guaranteeing idempotency.
    """
    key = f"{document_id}_{chunk_id}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, key))


class QdrantCloudStore:
    def __init__(
        self,
        url: str,
        api_key: str,
        collection_name: str = "vidhik_legal_chunks",
        dense_vector_name: str = "dense",
        upsert_batch_size: int = 64,
        timeout: float = 30.0,
        https: bool = True,
        port: int = 443,
    ):
        self.url = url
        self.api_key = api_key
        self.collection_name = collection_name
        self.dense_vector_name = dense_vector_name
        self.upsert_batch_size = upsert_batch_size
        self.timeout = timeout
        self.https = https
        self.port = port
        self.client: Optional[QdrantClient] = None

    def connect(self) -> QdrantClient:
        """Initialize connection to Qdrant Cloud cluster."""
        if self.client is None:
            if not self.url or not self.api_key:
                raise ValueError("QDRANT_URL and QDRANT_API_KEY must be provided.")

            parsed = urlparse(self.url)
            port_to_use = parsed.port if parsed.port else self.port

            logger.info(f"Connecting to Qdrant Cloud at host={parsed.hostname}, port={port_to_use}...")
            self.client = QdrantClient(
                url=self.url,
                api_key=self.api_key,
                https=self.https,
                port=port_to_use,
                timeout=self.timeout,
                check_compatibility=False,
            )
        return self.client

    def ensure_collection(self) -> bool:
        """
        Idempotently create collection 'vidhik_legal_chunks' and payload indexes.
        Configures dense vector ONLY (size: 1024, Cosine). No Qdrant sparse vectors.
        If the collection exists, it is NEVER recreated or destroyed.
        """
        import time
        client = self.connect()

        last_err = None
        for attempt in range(1, 4):
            try:
                collections_response = client.get_collections()
                existing_names = [c.name for c in collections_response.collections]
                break
            except Exception as e:
                last_err = e
                logger.warning(f"Qdrant get_collections attempt {attempt} failed: {e}; retrying...")
                time.sleep(1.5 * attempt)
        else:
            raise last_err

        if self.collection_name in existing_names:
            logger.info(f"Qdrant collection '{self.collection_name}' already exists. Reusing without modification.")
            return False

        logger.info(f"Creating Qdrant collection '{self.collection_name}' with dense-only vector schema (1024-d, Cosine)...")

        vectors_config = {
            self.dense_vector_name: VectorParams(
                size=1024,
                distance=Distance.COSINE
            )
        }

        client.create_collection(
            collection_name=self.collection_name,
            vectors_config=vectors_config,
        )
        logger.info(f"Collection '{self.collection_name}' created successfully with dense-only vector schema.")

        # Create payload indexes for retrieval filtering
        self._create_payload_indexes()
        return True

    def _create_payload_indexes(self):
        """Create indexes for common legal filtering fields."""
        client = self.connect()
        indexed_fields = [
            ("court_level", PayloadSchemaType.KEYWORD),
            ("court", PayloadSchemaType.KEYWORD),
            ("year", PayloadSchemaType.INTEGER),
            ("document_id", PayloadSchemaType.KEYWORD),
            ("language", PayloadSchemaType.KEYWORD),
            ("document_type", PayloadSchemaType.KEYWORD),
        ]
        for field_name, schema_type in indexed_fields:
            try:
                client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field_name,
                    field_schema=schema_type,
                )
                logger.info(f"Created payload index for field: '{field_name}' ({schema_type})")
            except Exception as e:
                logger.debug(f"Payload index for '{field_name}' already present or failed: {e}")

    def upsert_chunks(
        self,
        chunks: List[LegalChunk],
        dense_vectors: List[List[float]],
    ) -> int:
        """
        Batch upsert chunks into Qdrant using deterministic UUID point IDs.
        Stores dense vector (1024-d, Cosine) and full provenance payload.
        
        Returns:
            Number of points successfully upserted.
        """
        import time
        client = self.connect()
        total_chunks = len(chunks)
        if total_chunks == 0:
            return 0

        points = []
        for idx, chunk in enumerate(chunks):
            point_id = generate_deterministic_point_id(chunk.document_id, chunk.chunk_id)
            payload = chunk.to_payload()
            payload["custom_point_id"] = f"{chunk.document_id}_{chunk.chunk_id}"

            vector_dict = {
                self.dense_vector_name: dense_vectors[idx]
            }

            point = PointStruct(
                id=point_id,
                vector=vector_dict,
                payload=payload,
            )
            points.append(point)

        # Upsert in configured batch sizes with retries
        total_upserted = 0
        for i in range(0, len(points), self.upsert_batch_size):
            batch = points[i:i + self.upsert_batch_size]
            for attempt in range(1, 4):
                try:
                    client.upsert(
                        collection_name=self.collection_name,
                        points=batch,
                        wait=True,
                    )
                    break
                except Exception as e:
                    logger.warning(f"Upsert batch {i//self.upsert_batch_size + 1} attempt {attempt} failed: {e}")
                    if attempt == 3:
                        raise
                    time.sleep(1.5 * attempt)

            total_upserted += len(batch)

        return total_upserted

    def reset_collection(self) -> Dict[str, Any]:
        """
        Explicitly reset collection 'vidhik_legal_chunks':
        1. Confirms collection exists.
        2. Reports current point count.
        3. Deletes collection.
        4. Recreates collection with dense-only vector config (1024-d, Cosine).
        5. Recreates payload indexes.
        6. Verifies resulting point count is 0.
        """
        import time
        client = self.connect()
        collections_response = client.get_collections()
        existing_names = [c.name for c in collections_response.collections]

        initial_points = 0
        if self.collection_name in existing_names:
            info = client.get_collection(self.collection_name)
            initial_points = info.points_count or 0
            logger.info(f"Resetting collection '{self.collection_name}' (initial points: {initial_points})...")
            client.delete_collection(self.collection_name)
            logger.info(f"Deleted old collection '{self.collection_name}'.")
            time.sleep(1.5)

        # Recreate collection with dense-only vector schema
        vectors_config = {
            self.dense_vector_name: VectorParams(
                size=1024,
                distance=Distance.COSINE
            )
        }
        client.create_collection(
            collection_name=self.collection_name,
            vectors_config=vectors_config,
        )
        logger.info(f"Recreated collection '{self.collection_name}' with dense-only schema.")

        # Recreate payload indexes
        self._create_payload_indexes()

        new_info = client.get_collection(self.collection_name)
        final_points = new_info.points_count or 0
        logger.info(f"Collection reset complete. New point count: {final_points}.")

        return {
            "collection": self.collection_name,
            "initial_points": initial_points,
            "final_points": final_points,
            "dense_dimension": 1024,
            "sparse_vectors": None,
        }

    def verify_connection(self) -> Dict[str, Any]:
        """Perform a safe health check on Qdrant Cloud connection with retries."""
        import time
        client = self.connect()
        last_err = None
        for attempt in range(1, 4):
            try:
                collections_resp = client.get_collections()
                colls = [c.name for c in collections_resp.collections]
                target_exists = self.collection_name in colls
                point_count = 0
                if target_exists:
                    try:
                        info = client.get_collection(self.collection_name)
                        point_count = info.points_count or 0
                    except Exception:
                        pass
                return {
                    "status": "connected",
                    "collections_count": len(colls),
                    "collections": colls,
                    "target_collection_exists": target_exists,
                    "target_points_count": point_count,
                }
            except Exception as e:
                last_err = e
                logger.warning(f"Connection attempt {attempt} failed: {e}; retrying...")
                time.sleep(1.5 * attempt)
        raise last_err
