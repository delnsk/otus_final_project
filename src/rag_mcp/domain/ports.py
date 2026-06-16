"""Domain port interfaces (Protocol contracts)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from rag_mcp.domain.models import Chunk, Document, IndexStats


@runtime_checkable
class LLMPort(Protocol):
    async def generate(self, prompt: str) -> str: ...

    async def is_available(self) -> bool: ...


@runtime_checkable
class EmbeddingsPort(Protocol):
    async def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    async def embed_query(self, text: str) -> list[float]: ...


@runtime_checkable
class VectorStorePort(Protocol):
    async def add(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None: ...

    async def search(self, query_embedding: list[float], top_k: int) -> list[Chunk]: ...

    async def delete_all(self) -> None: ...

    async def get_stats(self) -> IndexStats: ...

    def get_all_chunks(self) -> list[Chunk]: ...


@runtime_checkable
class RetrieverPort(Protocol):
    async def retrieve(self, query: str, top_k: int) -> list[Chunk]: ...

    async def rebuild_index(self, chunks: list[Chunk]) -> None: ...


@runtime_checkable
class DocumentLoaderPort(Protocol):
    def load(self, path: str) -> Document: ...

    def supports(self, path: str) -> bool: ...


@runtime_checkable
class ChunkerPort(Protocol):
    def chunk(self, document: Document) -> list[Chunk]: ...


@runtime_checkable
class LoggerPort(Protocol):
    def info(self, event: str, **kwargs: object) -> None: ...

    def error(self, event: str, **kwargs: object) -> None: ...

    def warning(self, event: str, **kwargs: object) -> None: ...
