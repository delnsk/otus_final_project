"""Hybrid retriever: BM25 + vector search fused with RRF."""

from __future__ import annotations

from copy import deepcopy

from rag_mcp.config import Settings
from rag_mcp.domain.fusion import reciprocal_rank_fusion
from rag_mcp.domain.models import Chunk
from rag_mcp.infrastructure.retrieval.bm25_retriever import BM25Retriever
from rag_mcp.infrastructure.retrieval.vector_retriever import VectorRetriever


class HybridRetriever:
    def __init__(
        self,
        bm25: BM25Retriever,
        vector: VectorRetriever,
        settings: Settings,
    ) -> None:
        self._bm25 = bm25
        self._vector = vector
        self._settings = settings

    async def retrieve(self, query: str, top_k: int | None = None) -> list[Chunk]:
        k = top_k or self._settings.top_k
        bm25_results = await self._bm25.retrieve(query, k)
        vector_results = await self._vector.retrieve(query, k)
        bm25_copy = [deepcopy(c) for c in bm25_results]
        vector_copy = [deepcopy(c) for c in vector_results]
        return reciprocal_rank_fusion(
            [bm25_copy, vector_copy],
            k=self._settings.rrf_k,
            top_k=k,
        )

    async def rebuild_index(self, chunks: list[Chunk]) -> None:
        await self._bm25.rebuild_index(chunks)
