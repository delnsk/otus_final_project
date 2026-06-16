"""LangGraph conditional edges for Corrective RAG."""

from __future__ import annotations

from rag_mcp.config import Settings
from rag_mcp.domain.graph.state import RAGState


def decide_next_step(state: RAGState, settings: Settings) -> str:
    relevant = state.get("relevant", [])
    loop_count = state.get("loop_count", 0)

    if len(relevant) >= settings.grade_relevance_threshold:
        return "generate"
    if loop_count < settings.max_broaden_loops:
        return "broaden"
    return "generate"
