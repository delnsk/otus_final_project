"""Unit tests for ask_question and find_relevant_docs progress."""

import pytest

from rag_mcp.application.ask_progress import AskProgressTracker
from rag_mcp.application.progress_tracker import PROGRESS_TOTAL
from rag_mcp.application.search_progress import SearchProgressTracker


@pytest.mark.asyncio
async def test_ask_progress_ends_at_100():
    tracker = AskProgressTracker(None, None, max_broaden_loops=2)
    await tracker.rewrite_done()
    await tracker.retrieve_done()
    await tracker.grade_chunk(0, 2)
    await tracker.grade_chunk(1, 2)
    await tracker.generate_done()
    assert tracker.updates[-1][0] == PROGRESS_TOTAL
    assert "Answer ready" in tracker.updates[-1][1]


@pytest.mark.asyncio
async def test_ask_progress_grade_substeps_notify_callback():
    received: list[tuple[int, str]] = []

    async def capture(percent: int, message: str) -> None:
        received.append((percent, message))

    tracker = AskProgressTracker(capture, None, max_broaden_loops=0)
    await tracker.grade_chunk(0, 3)
    await tracker.grade_chunk(1, 3)
    assert len(received) == 2
    assert all("Grade chunks" in msg for _, msg in received)


@pytest.mark.asyncio
async def test_search_progress_steps():
    tracker = SearchProgressTracker(None, None)
    await tracker.bm25_done()
    await tracker.vector_done()
    await tracker.rrf_done()
    messages = [msg for _, msg in tracker.updates]
    assert "BM25 search" in messages[0]
    assert "Vector search" in messages[1]
    assert tracker.updates[-1][0] == PROGRESS_TOTAL
