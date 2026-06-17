"""Unit tests for index progress tracking."""

import pytest

from rag_mcp.application.index_progress import INDEX_PROGRESS_TOTAL, IndexProgressTracker


@pytest.mark.asyncio
async def test_progress_is_monotonic_and_ends_at_100():
    tracker = IndexProgressTracker()

    await tracker.scan_complete(2)
    await tracker.file_processed(0, 2, "/docs/a.md")
    await tracker.file_processed(1, 2, "/docs/b.md")
    await tracker.embed_start(3)
    await tracker.embed_chunk(0, 3)
    await tracker.embed_chunk(1, 3)
    await tracker.embed_chunk(2, 3)
    await tracker.embed_complete()
    await tracker.store_complete()
    await tracker.complete()

    percents = [p for p, _ in tracker.updates]
    assert percents == sorted(percents)
    assert percents[0] == 5
    assert percents[-1] == INDEX_PROGRESS_TOTAL


@pytest.mark.asyncio
async def test_progress_never_decreases():
    tracker = IndexProgressTracker()
    await tracker.report(50, "half")
    await tracker.report(10, "should not go back")
    assert tracker.updates[-1][0] == 50
    assert len(tracker.updates) == 1


@pytest.mark.asyncio
async def test_duplicate_percent_not_logged():
    logged: list[tuple[int, str]] = []

    class _Logger:
        def log_pipeline_progress(self, percent: int, message: str) -> None:
            logged.append((percent, message))

    tracker = IndexProgressTracker(pipeline_logger=_Logger())  # type: ignore[arg-type]
    await tracker.report(10, "first")
    await tracker.report(10, "same percent")
    await tracker.report(15, "next")
    assert logged == [(10, "first"), (15, "next")]
    assert len(tracker.updates) == 2


@pytest.mark.asyncio
async def test_duplicate_percent_still_notifies_callback():
    received: list[tuple[int, str]] = []

    async def capture(percent: int, message: str) -> None:
        received.append((percent, message))

    tracker = IndexProgressTracker(on_progress=capture)
    await tracker.report(10, "Embedding 1/10")
    await tracker.report(10, "Embedding 2/10")
    await tracker.report(15, "Embedding 3/10")
    assert received == [
        (10, "Embedding 1/10"),
        (10, "Embedding 2/10"),
        (15, "Embedding 3/10"),
    ]
    assert len(tracker.updates) == 2


@pytest.mark.asyncio
async def test_no_files_jumps_to_complete():
    tracker = IndexProgressTracker()
    await tracker.scan_complete(0)
    await tracker.complete("No files to index")
    assert tracker.updates[-1] == (100, "No files to index")


@pytest.mark.asyncio
async def test_on_progress_callback_receives_updates():
    received: list[tuple[int, str]] = []

    async def capture(percent: int, message: str) -> None:
        received.append((percent, message))

    tracker = IndexProgressTracker(on_progress=capture)
    await tracker.scan_complete(1)
    await tracker.complete()

    assert len(received) >= 2
    assert received[-1][0] == 100


def test_mcp_on_progress_from_context_outside_server():
    from rag_mcp.mcp.progress import mcp_on_progress_from_context

    assert mcp_on_progress_from_context() is None
