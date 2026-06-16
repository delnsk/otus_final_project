"""Unit tests for logging setup and pipeline logger."""

from rag_mcp.config import Settings
from rag_mcp.logging.formatter import format_log_event
from rag_mcp.logging.pipeline_logger import PipelineLogger
from rag_mcp.logging.setup import setup_logging


def test_format_tool_call():
    line = format_log_event(
        "tool_call",
        tool_name="index_folder",
        arguments={"path": "/app/sample_docs/code", "glob": "**/*"},
        result={
            "file_count": 113,
            "chunk_count": 4114,
            "last_indexed_at": "2026-06-16T07:26:19.967671+00:00",
            "errors": [],
        },
        error=None,
    )
    assert line.startswith("20")
    assert "tool_call index_folder" in line
    assert 'path="/app/sample_docs/code"' in line
    assert 'glob="**/*"' in line
    assert "file_count=113" in line
    assert "chunk_count=4114" in line
    assert "errors=no" in line
    assert "{" not in line


def test_format_request_separator():
    assert format_log_event("request_separator") == ""


def test_format_json_tool_call_line():
    from rag_mcp.logging.formatter import format_log_line

    raw = (
        '{"timestamp": "2026-06-16T11:42:15.108793+00:00", "level": "INFO", '
        '"event": "tool_call", "message": "tool_call", "tool_name": "index_status", '
        '"arguments": {}, "result": {"file_count": 115, "chunk_count": 4547, '
        '"last_indexed_at": "2026-06-16T08:16:47.232926+00:00", "errors": []}, '
        '"error": null}'
    )
    line = format_log_line(raw)
    assert line.startswith("2026.06.16 11:42:15.10:")
    assert "tool_call index_status" in line
    assert "file_count=115" in line
    assert "chunk_count=4547" in line
    assert "errors=no" in line
    assert "{" not in line


def test_formatter_handles_json_log_record():
    import logging

    from rag_mcp.logging.formatter import HumanReadableFormatter

    raw = (
        '{"timestamp": "2026-06-16T11:45:04.375503+00:00", "level": "INFO", '
        '"event": "tool_call", "message": "tool_call", "tool_name": "index_status", '
        '"arguments": {}, "result": {"file_count": 115, "chunk_count": 4547, '
        '"last_indexed_at": "2026-06-16T08:16:47.232926+00:00", "errors": []}, '
        '"error": null}'
    )
    record = logging.LogRecord(
        name="rag_mcp",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg=raw,
        args=(),
        exc_info=None,
    )
    line = HumanReadableFormatter().format(record)
    assert "tool_call index_status" in line
    assert "{" not in line


def test_pipeline_logger_writes_readable_lines(tmp_path):
    settings = Settings(log_dir=tmp_path, log_max_bytes=1_000_000)
    log_file = tmp_path / "rag_mcp.log"
    logger = setup_logging(settings)
    pl = PipelineLogger(logger, log_file=log_file)

    pl.log_rewrite("What is X?", "search query X")
    pl.log_retrieve("query", 5, [{"chunk_id": "a", "source": "f.md", "score": 0.9}])
    pl.log_grade([{"chunk_id": "a", "relevant": True}], 1)
    pl.log_broaden("broader query", 1)
    pl.log_generate("answer text", [{"source": "f.md", "position": 0}])
    pl.log_index_scan("/docs", "**/*", 3)
    pl.log_index_load("f.md", True)
    pl.log_index_chunk("f.md", 5)
    pl.log_index_embed(5)
    pl.log_index_store(5)

    assert log_file.exists()
    lines = log_file.read_text(encoding="utf-8").split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    assert len(lines) == 10
    for line in lines:
        assert line
        assert line[0].isdigit()
        assert "{" not in line


def test_log_rotation(tmp_path):
    settings = Settings(log_dir=tmp_path, log_max_bytes=500)
    log_file = tmp_path / "rag_mcp.log"
    logger = setup_logging(settings)
    pl = PipelineLogger(logger, log_file=log_file)

    for i in range(50):
        pl.log_rewrite(f"question {i}", f"query {i}" * 20)

    assert log_file.exists()
    total_size = sum(path.stat().st_size for path in tmp_path.glob("rag_mcp.log*"))
    assert total_size > 500
