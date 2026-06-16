"""Pipeline step logging for multi-step operations."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from rag_mcp.logging.formatter import emit_log


class PipelineLogger:
    def __init__(self, logger: logging.Logger | None = None, log_file: Path | None = None) -> None:
        self._logger = logger or logging.getLogger("rag_mcp")
        self._log_file = log_file

    def _log(self, event: str, **data: Any) -> None:
        emit_log(self._logger, event, **data)

    def log_rewrite(self, question: str, rewritten_query: str) -> None:
        self._log("rewrite_query", question=question, rewritten_query=rewritten_query)

    def log_retrieve(
        self,
        query: str,
        top_k: int,
        chunks: list[dict[str, Any]],
        bm25_count: int = 0,
        vector_count: int = 0,
    ) -> None:
        self._log(
            "retrieve",
            query=query,
            top_k=top_k,
            chunks=chunks,
            bm25_count=bm25_count,
            vector_count=vector_count,
        )

    def log_grade(self, graded: list[dict[str, Any]], relevant_count: int) -> None:
        self._log("grade_chunks", graded=graded, relevant_count=relevant_count)

    def log_broaden(self, query: str, loop_count: int) -> None:
        self._log("broaden_query", query=query, loop_count=loop_count)

    def log_generate(self, answer: str, sources: list[dict[str, Any]]) -> None:
        self._log("generate_answer", answer=answer[:500], sources=sources)

    def log_index_scan(self, path: str, glob_pattern: str, file_count: int) -> None:
        self._log("index_scan", path=path, glob=glob_pattern, file_count=file_count)

    def log_index_load(self, source: str, success: bool, error: str | None = None) -> None:
        self._log("index_load", source=source, success=success, error=error)

    def log_index_chunk(self, source: str, chunk_count: int) -> None:
        self._log("index_chunk", source=source, chunk_count=chunk_count)

    def log_index_embed(self, chunk_count: int) -> None:
        self._log("index_embed", chunk_count=chunk_count)

    def log_index_store(self, chunk_count: int) -> None:
        self._log("index_store", chunk_count=chunk_count)
