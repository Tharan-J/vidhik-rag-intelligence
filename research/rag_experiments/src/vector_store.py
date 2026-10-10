"""
Qdrant Local Vector Database Manager for Vidhik Phase 3
Stores chunks with full provenance metadata and supports fast cosine similarity vector search.
"""

import math
import logging
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

logger = logging.getLogger("Qdrant_Store")


class QdrantVectorStore:
    def __init__(self, collection_name: str = "vidhik_district_p3", storage_path: Path | str = None):
        self.collection_name = collection_name
        if storage_path is None:
            self.client = QdrantClient(":memory:")
        else:
            self.storage_path = str(storage_path)
            self.client = QdrantClient(path=self.storage_path)
            
    def init_collection(self, dimension: int = 1024, recreate: bool = False):
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection_name in collections:
            if recreate:
                self.client.delete_collection(self.collection_name)
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=dimension, distance=Distance.COSINE)
                )
        else:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=dimension, distance=Distance.COSINE)
            )

    def upsert_chunks(self, chunks: list[dict], embeddings: list):
        points = []
        for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            point = PointStruct(
                id=idx + 1,
                vector=emb.tolist() if hasattr(emb, "tolist") else list(emb),
                payload={
                    "chunk_id": str(chunk["chunk_id"]),
                    "document_id": str(chunk["document_id"]),
                    "page_number": int(chunk["page_number"]),
                    "paragraph_id": str(chunk["paragraph_id"]),
                    "paragraph_index": int(chunk["paragraph_index"]),
                    "source_sha256": str(chunk["source_sha256"]),
                    "state_name": str(chunk.get("state_name", "")),
                    "district_name": str(chunk.get("district_name", "")),
                    "court_complex_name": str(chunk.get("court_complex_name", "")),
                    "year": int(chunk["year"]) if chunk.get("year") is not None and not (isinstance(chunk.get("year"), float) and math.isnan(chunk["year"])) else None,
                    "text": str(chunk["text"]),
                    "word_count": int(chunk["word_count"]),
                    "sentence_count": int(chunk["sentence_count"]),
                    "sentence_ids": [str(s) for s in list(chunk.get("sentence_ids", []))]
                }
            )
            points.append(point)
            
        # Upsert in batches of 100
        batch_size = 100
        for i in range(0, len(points), batch_size):
            self.client.upsert(
                collection_name=self.collection_name,
                points=points[i:i + batch_size]
            )
        logger.info("Upserted %d points to Qdrant collection %s", len(points), self.collection_name)

    def search(self, query_vector: list, top_k: int = 10) -> list[dict]:
        """Search top-K nearest points using cosine similarity."""
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector.tolist() if hasattr(query_vector, "tolist") else list(query_vector),
            limit=top_k,
            with_payload=True
        )
        hits = []
        for p in results.points:
            hit = dict(p.payload)
            hit["score"] = float(p.score)
            hit["point_id"] = p.id
            hits.append(hit)
        return hits
