"""MCP progress adapter: forwards progress to FastMCP Context."""

from __future__ import annotations

from rag_mcp.application.progress_tracker import PROGRESS_TOTAL, OnProgress


def mcp_on_progress(ctx: object) -> OnProgress:
    async def report(percent: int, message: str) -> None:
        await ctx.report_progress(  # type: ignore[attr-defined]
            progress=percent,
            total=PROGRESS_TOTAL,
            message=message,
        )

    return report


def mcp_on_progress_from_context() -> OnProgress | None:
    """Return MCP progress callback when tool runs inside FastMCP; else None."""
    try:
        from fastmcp.server.dependencies import get_context

        return mcp_on_progress(get_context())
    except RuntimeError:
        return None
