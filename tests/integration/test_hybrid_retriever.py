"""Integration tests for hybrid retriever."""

import pytest

from rag_mcp.config import Settings
from rag_mcp.domain.models import Chunk
from rag_mcp.infrastructure.embeddings.factory import ChromaEmbeddings
from rag_mcp.infrastructure.retrieval.bm25_retriever import BM25Retriever
from rag_mcp.infrastructure.retrieval.hybrid_retriever import HybridRetriever
from rag_mcp.infrastructure.retrieval.vector_retriever import VectorRetriever
from rag_mcp.infrastructure.vectorstore.chroma import ChromaVectorStore


@pytest.fixture
async def hybrid(tmp_path):
    settings = Settings(chroma_path=tmp_path / "chroma", top_k=3)
    store = ChromaVectorStore(settings)
    embeddings = ChromaEmbeddings()
    bm25 = BM25Retriever()
    vector = VectorRetriever(store, embeddings)
    hybrid = HybridRetriever(bm25, vector, settings)

    chunks = [
        Chunk("c1", "Authentication uses JWT bearer tokens for API access", "auth.md", 0, "md"),
        Chunk("c2", "The database connection pool size is 17 connections", "db.md", 0, "md"),
        Chunk("c3", "TOKEN_EXPIRY_HOURS constant equals 47 hours", "config.py", 0, "py"),
    ]
    texts = [c.content for c in chunks]
    embs = await embeddings.embed_documents(texts)
    await store.add(chunks, embs)
    await hybrid.rebuild_index(chunks)
    return hybrid


@pytest.mark.asyncio
async def test_keyword_search(hybrid):
    results = await hybrid.retrieve("TOKEN_EXPIRY_HOURS", top_k=2)
    assert len(results) >= 1
    assert any("TOKEN_EXPIRY" in c.content for c in results)


@pytest.mark.asyncio
async def test_semantic_search(hybrid):
    results = await hybrid.retrieve("how does user login work", top_k=2)
    assert len(results) >= 1
