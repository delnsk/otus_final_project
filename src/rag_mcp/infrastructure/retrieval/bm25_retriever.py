"""BM25 sparse retriever using rank_bm25."""

from __future__ import annotations

import asyncio
import re

from rank_bm25 import BM25Okapi

from rag_mcp.domain.models import Chunk


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


class BM25Retriever:
    def __init__(self) -> None:
        self._chunks: list[Chunk] = []
        self._bm25: BM25Okapi | None = None

    async def rebuild_index(self, chunks: list[Chunk]) -> None:
        await asyncio.to_thread(self._rebuild_sync, chunks)

    def rebuild_index_sync(self, chunks: list[Chunk]) -> None:
        self._rebuild_sync(chunks)

    def _rebuild_sync(self, chunks: list[Chunk]) -> None:
        self._chunks = list(chunks)
        if not chunks:
            self._bm25 = None
            return
        tokenized = [_tokenize(c.content) for c in chunks]
        self._bm25 = BM25Okapi(tokenized)

    async def retrieve(self, query: str, top_k: int) -> list[Chunk]:
        return await asyncio.to_thread(self._retrieve_sync, query, top_k)

    def _retrieve_sync(self, query: str, top_k: int) -> list[Chunk]:
        if not self._bm25 or not self._chunks:
            return []
        scores = self._bm25.get_scores(_tokenize(query))
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        result: list[Chunk] = []
        for idx in ranked_indices[:top_k]:
            if scores[idx] > 0:
                chunk = self._chunks[idx]
                chunk.score = float(scores[idx])
                result.append(chunk)
        return result
