"""Integration tests: index persistence across restarts and multi-folder indexing."""

from __future__ import annotations

from pathlib import Path

import pytest

from rag_mcp.config import Settings
from rag_mcp.container import Container
from rag_mcp.domain.models import Chunk
from rag_mcp.infrastructure.vectorstore.chroma import ChromaVectorStore


def _write_two_corpora(base: Path) -> tuple[str, str]:
    dir_a = base / "corpus_a"
    dir_b = base / "corpus_b"
    dir_a.mkdir()
    dir_b.mkdir()
    (dir_a / "alpha.md").write_text("ALPHA_UNIQUE_TOKEN for authentication", encoding="utf-8")
    (dir_b / "beta.md").write_text("BETA_UNIQUE_TOKEN database pool", encoding="utf-8")
    return str(dir_a), str(dir_b)


@pytest.fixture
def settings(tmp_path):
    return Settings(
        chroma_path=tmp_path / "chroma",
        log_dir=tmp_path / "logs",
    )


@pytest.mark.asyncio
async def test_multi_folder_index_keeps_both_corpora_in_bm25(settings, tmp_path):
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    path_a, path_b = _write_two_corpora(docs_root)

    services = Container(settings).build()
    await services.index_service.index_folder(path_a)
    await services.index_service.index_folder(path_b)

    alpha_hits = await services.search_service.find_relevant_docs("ALPHA_UNIQUE_TOKEN", top_k=3)
    beta_hits = await services.search_service.find_relevant_docs("BETA_UNIQUE_TOKEN", top_k=3)

    assert any("ALPHA" in c.content for c in alpha_hits)
    assert any("BETA" in c.content for c in beta_hits)

    status = await services.status_service.get_status()
    assert status.file_count == 2
    assert status.chunk_count >= 2
    assert status.last_indexed_at is not None


@pytest.mark.asyncio
async def test_index_survives_container_restart(settings, tmp_path):
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    path_a, path_b = _write_two_corpora(docs_root)

    first = Container(settings).build()
    await first.index_service.index_folder(path_a)
    await first.index_service.index_folder(path_b)
    before = await first.status_service.get_status()

    restarted = Container(settings).build()
    after = await restarted.status_service.get_status()

    assert after.chunk_count == before.chunk_count
    assert after.file_count == before.file_count == 2
    assert after.last_indexed_at is not None

    alpha_hits = await restarted.search_service.find_relevant_docs("ALPHA_UNIQUE_TOKEN", top_k=3)
    beta_hits = await restarted.search_service.find_relevant_docs("BETA_UNIQUE_TOKEN", top_k=3)

    assert any("ALPHA" in c.content for c in alpha_hits)
    assert any("BETA" in c.content for c in beta_hits)


@pytest.mark.asyncio
async def test_chroma_stats_derived_from_persisted_metadata(tmp_path):
    chroma_path = tmp_path / "chroma"
    store = ChromaVectorStore(Settings(chroma_path=chroma_path))
    chunks = [
        Chunk("c1", "text a", "a.md", 0, "md"),
        Chunk("c2", "text b", "b.md", 0, "md"),
    ]
    await store.add(chunks, [[0.1] * 384, [0.2] * 384])

    reopened = ChromaVectorStore(Settings(chroma_path=chroma_path))
    stats = await reopened.get_stats()

    assert stats.file_count == 2
    assert stats.chunk_count == 2
    assert stats.last_indexed_at is not None
