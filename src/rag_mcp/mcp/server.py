"""FastMCP server creation and registration."""

from __future__ import annotations

from fastmcp import FastMCP

from rag_mcp.mcp.tools import MCPTools


def create_mcp_server(tools: MCPTools) -> FastMCP:
    mcp = FastMCP(
        name="rag-knowledge-base",
        instructions=(
            "RAG Knowledge Base server. Index local documents and ask questions "
            "about them using Corrective RAG with hybrid search."
        ),
    )
    tools.register(mcp)
    return mcp
