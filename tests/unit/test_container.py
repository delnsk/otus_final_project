"""Unit tests for DI container."""

from rag_mcp.config import Settings
from rag_mcp.container import Container


def test_container_build():
    settings = Settings(chroma_path="./test_data/chroma", log_dir="./test_data/logs")
    services = Container(settings).build()
    assert services.index_service is not None
    assert services.ask_service is not None
    assert services.search_service is not None
    assert services.status_service is not None
    assert services.mcp_server is not None
