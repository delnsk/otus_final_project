"""Find relevant docs use case (hybrid search without LLM)."""

from __future__ import annotations

from rag_mcp.application.progress_tracker import OnProgress
from rag_mcp.application.search_progress import SearchProgressTracker
from rag_mcp.config import Settings
from rag_mcp.domain.models import Chunk
from rag_mcp.domain.ports import RetrieverPort
from rag_mcp.logging.pipeline_logger import PipelineLogger


class SearchService:
    def __init__(
        self,
        retriever: RetrieverPort,
        settings: Settings,
        pipeline_logger: PipelineLogger,
    ) -> None:
        self._retriever = retriever
        self._settings = settings
        self._pipeline_logger = pipeline_logger

    async def find_relevant_docs(
        self,
        query: str,
        top_k: int | None = None,
        *,
        on_progress: OnProgress | None = None,
    ) -> list[Chunk]:
        k = top_k or self._settings.top_k
        progress = (
            SearchProgressTracker(on_progress, self._pipeline_logger)
            if on_progress is not None
            else None
        )
        if progress is not None:
            from rag_mcp.infrastructure.retrieval.hybrid_retriever import HybridRetriever

            if isinstance(self._retriever, HybridRetriever):
                return await self._retriever.retrieve(query, k, progress=progress)
        return await self._retriever.retrieve(query, k)
