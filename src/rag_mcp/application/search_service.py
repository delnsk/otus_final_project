"""Find relevant docs use case (hybrid search without LLM)."""

from __future__ import annotations

from rag_mcp.config import Settings
from rag_mcp.domain.models import Chunk
from rag_mcp.domain.ports import RetrieverPort


class SearchService:
    def __init__(self, retriever: RetrieverPort, settings: Settings) -> None:
        self._retriever = retriever
        self._settings = settings

    async def find_relevant_docs(self, query: str, top_k: int | None = None) -> list[Chunk]:
        k = top_k or self._settings.top_k
        return await self._retriever.retrieve(query, k)
