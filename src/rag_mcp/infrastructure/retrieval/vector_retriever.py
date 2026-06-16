"""Vector-based dense retriever."""

from __future__ import annotations

from rag_mcp.domain.models import Chunk
from rag_mcp.domain.ports import EmbeddingsPort, VectorStorePort


class VectorRetriever:
    def __init__(self, vector_store: VectorStorePort, embeddings: EmbeddingsPort) -> None:
        self._vector_store = vector_store
        self._embeddings = embeddings

    async def retrieve(self, query: str, top_k: int) -> list[Chunk]:
        embedding = await self._embeddings.embed_query(query)
        return await self._vector_store.search(embedding, top_k)
