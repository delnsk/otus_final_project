"""E2E tests for MCP tools."""

import pytest

from rag_mcp.config import Settings
from rag_mcp.container import Container
from rag_mcp.mcp.middleware import MCPLoggingMiddleware
from rag_mcp.mcp.server import create_mcp_server
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
        services.clear_index_service,
        middleware,
    )
    return mcp_tools, fixtures


@pytest.mark.asyncio
async def test_mcp_tool_parameter_descriptions(tools):
    mcp_tools, _ = tools
    mcp = create_mcp_server(mcp_tools)
    registered = await mcp.get_tools()

    expected = {
        "index_folder": ("path", "glob"),
        "ask_question": ("question",),
        "find_relevant_docs": ("query", "top_k"),
    }
    for tool_name, param_names in expected.items():
        schema = registered[tool_name].parameters
        props = schema["properties"]
        for param in param_names:
            assert param in props, f"{tool_name}: missing parameter {param}"
            assert props[param].get("description"), f"{tool_name}.{param}: missing description"


@pytest.mark.asyncio
async def test_index_status_empty(tools):
    mcp_tools, _ = tools
    status = await mcp_tools.index_status()
    assert status["chunk_count"] == 0


@pytest.mark.asyncio
async def test_index_folder(tools):
    mcp_tools, fixtures = tools
    updates: list[tuple[int, str]] = []

    async def on_progress(percent: int, message: str) -> None:
        updates.append((percent, message))

    result = await mcp_tools.index_folder(fixtures, "*", on_progress=on_progress)
    assert result["chunk_count"] > 0
    assert result["file_count"] >= 7
    assert updates[-1][0] == 100


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
    updates: list[tuple[int, str]] = []

    async def on_progress(percent: int, message: str) -> None:
        updates.append((percent, message))

    results = await mcp_tools.find_relevant_docs(
        "TOKEN_EXPIRY_HOURS", top_k=3, on_progress=on_progress
    )
    assert len(results) >= 1
    assert "error" not in results[0] or results[0].get("content")
    assert updates[-1][0] == 100
    assert any("BM25" in msg for _, msg in updates)


@pytest.mark.asyncio
async def test_ask_question_empty_index(tools):
    mcp_tools, _ = tools
    result = await mcp_tools.ask_question("What is TOKEN_EXPIRY_HOURS?")
    assert "error" in result


@pytest.mark.asyncio
async def test_clear_index(tools):
    mcp_tools, fixtures = tools
    await mcp_tools.index_folder(fixtures, "*")
    status_before = await mcp_tools.index_status()
    assert status_before["chunk_count"] > 0

    result = await mcp_tools.clear_index()
    assert result["chunk_count"] == 0
    assert result["file_count"] == 0
    assert result.get("last_indexed_at") is None

    status_after = await mcp_tools.index_status()
    assert status_after["chunk_count"] == 0

    search = await mcp_tools.find_relevant_docs("TOKEN_EXPIRY_HOURS", top_k=3)
    assert search == [] or (len(search) == 1 and "error" in search[0])


@pytest.mark.asyncio
async def test_clear_index_empty(tools):
    mcp_tools, _ = tools
    result = await mcp_tools.clear_index()
    assert result["chunk_count"] == 0
    assert result["file_count"] == 0
    assert "error" not in result


@pytest.mark.asyncio
async def test_ask_question_without_ollama(tools):
    mcp_tools, fixtures = tools
    await mcp_tools.index_folder(fixtures, "*")
    result = await mcp_tools.ask_question("What is TOKEN_EXPIRY_HOURS?")
    assert "error" in result or "answer" in result
