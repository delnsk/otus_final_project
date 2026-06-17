"""Progress tracking for find_relevant_docs hybrid retrieval."""

from __future__ import annotations

from rag_mcp.application.progress_tracker import OnProgress, ProgressTracker
from rag_mcp.logging.pipeline_logger import PipelineLogger

_W_BM25 = 30.0
_W_VECTOR = 45.0
_W_RRF = 25.0
_TOTAL = _W_BM25 + _W_VECTOR + _W_RRF


class SearchProgressTracker(ProgressTracker):
    def __init__(
        self,
        on_progress: OnProgress | None,
        pipeline_logger: PipelineLogger | None,
    ) -> None:
        super().__init__(on_progress, pipeline_logger)
        self._done_weight = 0.0

    async def _bump(self, weight: float, step: str) -> None:
        self._done_weight += weight
        percent = min(99, int(100 * self._done_weight / _TOTAL))
        await self.report(percent, step)

    async def bm25_done(self) -> None:
        await self._bump(_W_BM25, "BM25 search")

    async def vector_done(self) -> None:
        await self._bump(_W_VECTOR, "Vector search")

    async def rrf_done(self) -> None:
        await self._bump(_W_RRF, "RRF fusion")
        await self.complete("Search complete")
