"""Integration test for index service."""

import pytest

from rag_mcp.config import Settings
from rag_mcp.container import Container


@pytest.mark.asyncio
async def test_index_test_fixtures(tmp_path):
    fixtures = str(__import__("pathlib").Path(__file__).parent / "fixtures")
    settings = Settings(
        chroma_path=tmp_path / "chroma",
        log_dir=tmp_path / "logs",
    )
    services = Container(settings).build()
    stats = await services.index_service.index_folder(fixtures, "*")
    assert stats.chunk_count > 0
    assert stats.file_count >= 7
