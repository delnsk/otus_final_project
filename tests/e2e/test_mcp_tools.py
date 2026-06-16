"""E2E tests for MCP tools."""

import pytest

from rag_mcp.config import Settings
from rag_mcp.container import Container
from rag_mcp.mcp.middleware import MCPLoggingMiddleware
from rag_mcp.mcp.tools import MCPTools


@pytest.fixture
def tools(tmp_path):
    fixtures = str(__import__("pathlib").Path(__file__).parent.parent / "integration" / "fixtures")
    settings = Settings(
        chroma_path=tmp_path / "chroma",
        log_dir=tmp_path / "logs",
    )
    services = Container(settings).build()
    middleware = MCPLoggingMiddleware(services.logger)
    mcp_tools = MCPTools(
        services.index_service,
        services.ask_service,
        services.search_service,
        services.status_service,
        middleware,
    )
    return mcp_tools, fixtures


@pytest.mark.asyncio
async def test_index_status_empty(tools):
    mcp_tools, _ = tools
    status = await mcp_tools.index_status()
    assert status["chunk_count"] == 0


@pytest.mark.asyncio
async def test_index_folder(tools):
    mcp_tools, fixtures = tools
    result = await mcp_tools.index_folder(fixtures, "*")
    assert result["chunk_count"] > 0
    assert result["file_count"] >= 7


@pytest.mark.asyncio
async def test_index_status_after_index(tools):
    mcp_tools, fixtures = tools
    await mcp_tools.index_folder(fixtures, "*")
    status = await mcp_tools.index_status()
    assert status["chunk_count"] > 0


@pytest.mark.asyncio
async def test_find_relevant_docs(tools):
    mcp_tools, fixtures = tools
    await mcp_tools.index_folder(fixtures, "*")
    results = await mcp_tools.find_relevant_docs("TOKEN_EXPIRY_HOURS", top_k=3)
    assert len(results) >= 1
    assert "error" not in results[0] or results[0].get("content")


@pytest.mark.asyncio
async def test_ask_question_empty_index(tools):
    mcp_tools, _ = tools
    result = await mcp_tools.ask_question("What is TOKEN_EXPIRY_HOURS?")
    assert "error" in result


@pytest.mark.asyncio
async def test_ask_question_without_ollama(tools):
    mcp_tools, fixtures = tools
    await mcp_tools.index_folder(fixtures, "*")
    result = await mcp_tools.ask_question("What is TOKEN_EXPIRY_HOURS?")
    assert "error" in result or "answer" in result
