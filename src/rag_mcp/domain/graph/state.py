"""LangGraph RAG state."""

from __future__ import annotations

from typing import TypedDict

from rag_mcp.domain.models import Chunk, GradedChunk, Source


class RAGState(TypedDict, total=False):
    question: str
    query: str
    chunks: list[Chunk]
    graded: list[GradedChunk]
    relevant: list[Chunk]
    loop_count: int
    answer: str
    sources: list[Source]
