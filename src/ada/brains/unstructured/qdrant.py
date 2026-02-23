"""Qdrant vector database client abstraction."""

from __future__ import annotations

from typing import Any

import structlog
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

logger = structlog.get_logger()


class QdrantStore:
    """Abstraction over Qdrant for document storage and retrieval."""

    def __init__(
        self,
        url: str = "http://localhost:6333",
        api_key: str | None = None,
        collection_name: str = "ada_documents",
        vector_size: int = 1536,
    ) -> None:
        self._client = QdrantClient(url=url, api_key=api_key)
        self._collection = collection_name
        self._vector_size = vector_size

    def ensure_collection(self) -> None:
        """Create collection if it doesn't exist."""
        collections = self._client.get_collections().collections
        names = [c.name for c in collections]
        if self._collection not in names:
            self._client.create_collection(
                collection_name=self._collection,
                vectors_config=VectorParams(
                    size=self._vector_size,
                    distance=Distance.COSINE,
                ),
            )
            logger.info("qdrant_collection_created", collection=self._collection)

    def upsert(
        self,
        point_id: str,
        vector: list[float],
        payload: dict[str, Any],
    ) -> None:
        """Upsert a single point."""
        self._client.upsert(
            collection_name=self._collection,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                )
            ],
        )

    def search(
        self,
        query_vector: list[float],
        tenant_id: str,
        roles: list[str] | None = None,
        source: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search for similar documents with RBAC metadata filtering."""
        must_conditions = [
            FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id)),
        ]
        if source:
            must_conditions.append(
                FieldCondition(key="source", match=MatchValue(value=source)),
            )

        should_conditions = []
        if roles:
            for role in roles:
                should_conditions.append(
                    FieldCondition(
                        key="allowed_roles", match=MatchValue(value=role)
                    ),
                )

        query_filter = Filter(
            must=must_conditions,
            should=should_conditions if should_conditions else None,
        )

        results = self._client.query_points(
            collection_name=self._collection,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
        )

        return [
            {
                "id": str(point.id),
                "score": point.score,
                "payload": point.payload,
            }
            for point in results.points
        ]

    def delete(self, point_ids: list[str]) -> None:
        """Delete points by IDs."""
        self._client.delete(
            collection_name=self._collection,
            points_selector=point_ids,
        )
