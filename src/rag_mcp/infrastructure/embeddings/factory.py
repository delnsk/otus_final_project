"""Embeddings providers: Chroma default and Ollama."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod

import httpx

from rag_mcp.config import Settings
from rag_mcp.domain.ports import EmbeddingsPort


class BaseEmbeddings(ABC):
    @abstractmethod
    async def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    @abstractmethod
    async def embed_query(self, text: str) -> list[float]: ...


class ChromaEmbeddings(BaseEmbeddings):
    """Uses ChromaDB's default embedding function (all-MiniLM-L6-v2)."""

    def __init__(self) -> None:
        from chromadb.utils import embedding_functions

        self._ef = embedding_functions.DefaultEmbeddingFunction()

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return await asyncio.to_thread(self._ef, texts)

    async def embed_query(self, text: str) -> list[float]:
        result = await asyncio.to_thread(self._ef, [text])
        return result[0]


class OllamaEmbeddings(BaseEmbeddings):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._base_url = settings.ollama_base_url.rstrip("/")
        self._model = settings.embedding_model

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed_query(t) for t in texts]

    async def embed_query(self, text: str) -> list[float]:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self._base_url}/api/embeddings",
                json={"model": self._model, "prompt": text},
            )
            response.raise_for_status()
            return response.json()["embedding"]


def create_embeddings(settings: Settings) -> EmbeddingsPort:
    provider = settings.embedding_provider.lower()
    if provider == "ollama":
        return OllamaEmbeddings(settings)
    return ChromaEmbeddings()
