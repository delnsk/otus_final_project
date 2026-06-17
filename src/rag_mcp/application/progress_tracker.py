"""Shared 0–100% progress reporting for MCP tools."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from rag_mcp.logging.pipeline_logger import PipelineLogger

PROGRESS_TOTAL = 100

OnProgress = Callable[[int, str], Awaitable[None]]


class ProgressTracker:
    """MCP callback on every report; file log only when percent changes."""

    def __init__(
        self,
        on_progress: OnProgress | None = None,
        pipeline_logger: PipelineLogger | None = None,
    ) -> None:
        self._on_progress = on_progress
        self._pipeline_logger = pipeline_logger
        self._last_percent = 0
        self.updates: list[tuple[int, str]] = []

    async def report(self, percent: int, message: str) -> None:
        clamped = max(self._last_percent, min(PROGRESS_TOTAL, percent))
        if self._on_progress is not None:
            await self._on_progress(clamped, message)
        if clamped == self._last_percent:
            return
        self._last_percent = clamped
        self.updates.append((clamped, message))
        if self._pipeline_logger is not None:
            self._pipeline_logger.log_pipeline_progress(clamped, message)

    async def complete(self, message: str = "Complete") -> None:
        await self.report(PROGRESS_TOTAL, message)
