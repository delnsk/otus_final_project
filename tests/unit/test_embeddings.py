"""Unit tests for embeddings factory."""

from rag_mcp.config import Settings
from rag_mcp.infrastructure.embeddings.factory import (
    ChromaEmbeddings,
    OllamaEmbeddings,
    create_embeddings,
)


def test_default_chroma_provider():
    settings = Settings(embedding_provider="chroma")
    emb = create_embeddings(settings)
    assert isinstance(emb, ChromaEmbeddings)


def test_ollama_provider(monkeypatch):
    monkeypatch.setenv("EMBEDDING_PROVIDER", "ollama")
    settings = Settings()
    emb = create_embeddings(settings)
    assert isinstance(emb, OllamaEmbeddings)
