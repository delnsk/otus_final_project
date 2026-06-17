"""Progress tracking for ask_question Corrective RAG pipeline."""

from __future__ import annotations

from rag_mcp.application.progress_tracker import PROGRESS_TOTAL, OnProgress, ProgressTracker
from rag_mcp.logging.pipeline_logger import PipelineLogger

_W_REWRITE = 8.0
_W_RETRIEVE = 10.0
_W_GRADE = 45.0
_W_BROADEN = 5.0
_W_GENERATE = 27.0


def _total_weight(max_broaden_loops: int) -> float:
    return (
        _W_REWRITE
        + _W_GENERATE
        + (max_broaden_loops + 1) * (_W_RETRIEVE + _W_GRADE)
        + max_broaden_loops * _W_BROADEN
    )


class AskProgressTracker(ProgressTracker):
    def __init__(
        self,
        on_progress: OnProgress | None,
        pipeline_logger: PipelineLogger | None,
        max_broaden_loops: int,
    ) -> None:
        super().__init__(on_progress, pipeline_logger)
        self._max_broaden_loops = max_broaden_loops
        self._done_weight = 0.0
        self._retrieve_pass = 0

    async def _bump(self, weight: float, step: str, detail: str = "") -> None:
        self._done_weight += weight
        total = _total_weight(self._max_broaden_loops)
        percent = min(PROGRESS_TOTAL - 1, int(100 * self._done_weight / total))
        message = f"{step}: {detail}" if detail else step
        await self.report(percent, message)

    async def rewrite_done(self) -> None:
        await self._bump(_W_REWRITE, "Rewrite query")

    async def retrieve_done(self) -> None:
        self._retrieve_pass += 1
        detail = (
            f"pass {self._retrieve_pass}"
            if self._retrieve_pass > 1
            else "BM25 + vector → RRF"
        )
        await self._bump(_W_RETRIEVE, "Retrieve", detail)

    async def grade_chunk(self, index: int, total: int) -> None:
        if total <= 0:
            return
        await self._bump(_W_GRADE / total, "Grade chunks", f"{index + 1}/{total}")

    async def broaden_done(self, loop: int) -> None:
        await self._bump(_W_BROADEN, "Broaden query", f"loop {loop}")

    async def generate_done(self) -> None:
        await self._bump(_W_GENERATE, "Generate answer")
        await self.complete("Answer ready")
