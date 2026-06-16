"""ChromaDB vector store adapter."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import chromadb

from rag_mcp.config import Settings
from rag_mcp.domain.models import Chunk, IndexStats


class ChromaVectorStore:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        settings.chroma_path.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(settings.chroma_path))
        self._collection = self._client.get_or_create_collection(
            name="rag_documents",
            metadata={"hnsw:space": "cosine"},
        )
        self._last_indexed_at: datetime | None = None
        self._file_sources: set[str] = set()

    async def add(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        await asyncio.to_thread(self._add_sync, chunks, embeddings)

    def _add_sync(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        if not chunks:
            return
        ids = [c.chunk_id for c in chunks]
        documents = [c.content for c in chunks]
        metadatas = [
            {
                "source": c.source,
                "position": c.position,
                "file_type": c.file_type,
            }
            for c in chunks
        ]
        self._collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        for c in chunks:
            self._file_sources.add(c.source)
        self._last_indexed_at = datetime.now(timezone.utc)

    async def search(self, query_embedding: list[float], top_k: int) -> list[Chunk]:
        return await asyncio.to_thread(self._search_sync, query_embedding, top_k)

    def _search_sync(self, query_embedding: list[float], top_k: int) -> list[Chunk]:
        if self._collection.count() == 0:
            return []
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self._collection.count()),
        )
        chunks: list[Chunk] = []
        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        for idx, doc_id in enumerate(ids):
            meta = metadatas[idx] if idx < len(metadatas) else {}
            dist = distances[idx] if idx < len(distances) else 0.0
            score = 1.0 - dist if dist is not None else 0.0
            chunks.append(
                Chunk(
                    chunk_id=doc_id,
                    content=documents[idx] if idx < len(documents) else "",
                    source=meta.get("source", ""),
                    position=int(meta.get("position", 0)),
                    file_type=meta.get("file_type", ""),
                    score=score,
                )
            )
        return chunks

    async def delete_all(self) -> None:
        await asyncio.to_thread(self._delete_all_sync)

    def _delete_all_sync(self) -> None:
        self._client.delete_collection("rag_documents")
        self._collection = self._client.get_or_create_collection(
            name="rag_documents",
            metadata={"hnsw:space": "cosine"},
        )
        self._file_sources.clear()
        self._last_indexed_at = None

    async def get_stats(self) -> IndexStats:
        return await asyncio.to_thread(self._get_stats_sync)

    def _get_stats_sync(self) -> IndexStats:
        count = self._collection.count()
        return IndexStats(
            file_count=len(self._file_sources),
            chunk_count=count,
            last_indexed_at=self._last_indexed_at,
        )

    def get_all_chunks(self) -> list[Chunk]:
        if self._collection.count() == 0:
            return []
        results = self._collection.get()
        chunks: list[Chunk] = []
        ids = results.get("ids", [])
        documents = results.get("documents", [])
        metadatas = results.get("metadatas", [])
        for idx, doc_id in enumerate(ids):
            meta = metadatas[idx] if idx < len(metadatas) else {}
            chunks.append(
                Chunk(
                    chunk_id=doc_id,
                    content=documents[idx] if idx < len(documents) else "",
                    source=meta.get("source", ""),
                    position=int(meta.get("position", 0)),
                    file_type=meta.get("file_type", ""),
                )
            )
        return chunks
