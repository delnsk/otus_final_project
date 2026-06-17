"""Integration tests for index_folder progress reporting."""

from pathlib import Path

import pytest

from rag_mcp.config import Settings
from rag_mcp.container import Container


@pytest.mark.asyncio
async def test_index_folder_reports_progress_to_100(tmp_path):
    fixtures = str(Path(__file__).parent / "fixtures")
    settings = Settings(
        chroma_path=tmp_path / "chroma",
        log_dir=tmp_path / "logs",
    )
    services = Container(settings).build()
    updates: list[tuple[int, str]] = []

    async def on_progress(percent: int, message: str) -> None:
        updates.append((percent, message))

    stats = await services.index_service.index_folder(fixtures, "*", on_progress=on_progress)

    assert stats.chunk_count > 0
    percents = [p for p, _ in updates]
    assert percents == sorted(percents)
    assert percents[-1] == 100
    assert any("Embedding" in msg for _, msg in updates)
    assert any("Indexing complete" in msg for _, msg in updates)


@pytest.mark.asyncio
async def test_index_folder_empty_dir_reports_complete(tmp_path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    settings = Settings(
        chroma_path=tmp_path / "chroma",
        log_dir=tmp_path / "logs",
    )
    services = Container(settings).build()
    updates: list[tuple[int, str]] = []

    async def on_progress(percent: int, message: str) -> None:
        updates.append((percent, message))

    stats = await services.index_service.index_folder(str(empty_dir), "*", on_progress=on_progress)

    assert stats.chunk_count == 0
    assert updates[-1] == (100, "No files to index")
