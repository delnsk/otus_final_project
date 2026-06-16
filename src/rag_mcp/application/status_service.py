"""Index status use case."""

from __future__ import annotations

from rag_mcp.domain.models import IndexStats
from rag_mcp.domain.ports import VectorStorePort


class StatusService:
    def __init__(self, vector_store: VectorStorePort) -> None:
        self._vector_store = vector_store

    async def get_status(self) -> IndexStats:
        return await self._vector_store.get_stats()
