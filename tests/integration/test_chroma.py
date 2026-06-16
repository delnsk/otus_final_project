"""Integration tests for ChromaDB vector store."""

import pytest

from rag_mcp.config import Settings
from rag_mcp.domain.models import Chunk
from rag_mcp.infrastructure.vectorstore.chroma import ChromaVectorStore


@pytest.fixture
def store(tmp_path):
    return ChromaVectorStore(Settings(chroma_path=tmp_path / "chroma"))


@pytest.mark.asyncio
async def test_add_and_search(store):
    chunks = [
        Chunk("c1", "Python programming language", "a.py", 0, "py"),
        Chunk("c2", "JavaScript web development", "b.js", 0, "js"),
        Chunk("c3", "TOKEN_EXPIRY_HOURS is 47", "config.py", 0, "py"),
    ]
    embeddings = [[0.1] * 384, [0.2] * 384, [0.9] * 384]
    await store.add(chunks, embeddings)

    results = await store.search([0.9] * 384, top_k=1)
    assert len(results) == 1
    assert results[0].chunk_id == "c3"


@pytest.mark.asyncio
async def test_stats_after_index(store):
    await store.delete_all()
    chunks = [Chunk("c1", "text", "f.md", 0, "md")]
    await store.add(chunks, [[0.1] * 384])
    stats = await store.get_stats()
    assert stats.chunk_count >= 1
    assert stats.file_count >= 1
