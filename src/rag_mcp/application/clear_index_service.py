"""Clear index use case: remove all indexed chunks from ChromaDB and BM25."""

from __future__ import annotations

from rag_mcp.domain.models import IndexStats
from rag_mcp.domain.ports import RetrieverPort, VectorStorePort
from rag_mcp.logging.pipeline_logger import PipelineLogger


class ClearIndexService:
    def __init__(
        self,
        vector_store: VectorStorePort,
        retriever: RetrieverPort,
        pipeline_logger: PipelineLogger,
    ) -> None:
        self._vector_store = vector_store
        self._retriever = retriever
        self._pipeline_logger = pipeline_logger

    async def clear_index(self) -> IndexStats:
        before = await self._vector_store.get_stats()
        self._pipeline_logger.log_index_clear(
            file_count=before.file_count,
            chunk_count=before.chunk_count,
        )
        await self._vector_store.delete_all()
        await self._retriever.rebuild_index([])
        return await self._vector_store.get_stats()
