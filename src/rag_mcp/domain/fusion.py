"""Reciprocal Rank Fusion for combining ranked lists."""

from __future__ import annotations

from collections import defaultdict

from rag_mcp.domain.models import Chunk


def reciprocal_rank_fusion(
    ranked_lists: list[list[Chunk]],
    k: int = 60,
    top_k: int = 5,
) -> list[Chunk]:
    """Merge multiple ranked chunk lists using RRF: score = sum(1 / (k + rank))."""
    scores: dict[str, float] = defaultdict(float)
    chunk_map: dict[str, Chunk] = {}

    for ranked in ranked_lists:
        for rank, chunk in enumerate(ranked, start=1):
            scores[chunk.chunk_id] += 1.0 / (k + rank)
            if chunk.chunk_id not in chunk_map:
                chunk_map[chunk.chunk_id] = chunk

    sorted_ids = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)
    result: list[Chunk] = []
    for cid in sorted_ids[:top_k]:
        chunk = chunk_map[cid]
        chunk.score = scores[cid]
        result.append(chunk)
    return result
