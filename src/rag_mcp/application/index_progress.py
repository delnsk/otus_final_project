"""Progress tracking for index_folder (0–100%)."""

from __future__ import annotations

from pathlib import Path

from rag_mcp.application.progress_tracker import OnProgress, PROGRESS_TOTAL, ProgressTracker
from rag_mcp.logging.pipeline_logger import PipelineLogger

_SCAN_END = 5
_FILES_END = 25  # 20% — load/chunk по файлам
_EMBED_END = 85  # 60% — эмбеддинги (2× прежней доли 30%)
_STORE_END = 95  # 10% — запись в ChromaDB

# Re-export for compatibility
INDEX_PROGRESS_TOTAL = PROGRESS_TOTAL


class IndexProgressTracker(ProgressTracker):
    """Maps index_folder pipeline stages to monotonic 0–100% progress."""

    async def scan_complete(self, file_count: int) -> None:
        await self.report(_SCAN_END, f"Found {file_count} file(s)")

    async def file_processed(self, index: int, total: int, path: str) -> None:
        if total == 0:
            return
        span = _FILES_END - _SCAN_END
        percent = _SCAN_END + int(span * (index + 1) / total)
        name = Path(path).name
        await self.report(percent, f"Processed {index + 1}/{total}: {name}")

    async def embed_start(self, chunk_count: int) -> None:
        await self.report(_FILES_END, f"Embedding {chunk_count} chunk(s)")

    async def embed_chunk(self, index: int, total: int) -> None:
        if total <= 1:
            return
        span = _EMBED_END - _FILES_END
        percent = _FILES_END + int(span * (index + 1) / total)
        await self.report(percent, f"Embedding {index + 1}/{total}")

    async def embed_complete(self) -> None:
        await self.report(_EMBED_END, "Embeddings complete")

    async def store_complete(self) -> None:
        await self.report(_STORE_END, "Stored in ChromaDB")

    async def complete(self, message: str = "Indexing complete") -> None:
        await super().complete(message)
