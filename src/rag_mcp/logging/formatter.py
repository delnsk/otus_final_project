"""Human-readable log line formatting."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

_META_KEYS = frozenset({"timestamp", "level", "event", "message"})
_HUMAN_LINE_RE = re.compile(r"^\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2}\.\d{2}: ")


def format_timestamp(dt: datetime | None = None) -> str:
    dt = dt or datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    centiseconds = dt.microsecond // 10000
    return dt.strftime("%Y.%m.%d %H:%M:%S.") + f"{centiseconds:02d}"


def _parse_iso_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _parse_json_payload(raw: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(payload, dict):
        return None
    if "event" not in payload and "message" not in payload:
        return None
    return payload


def _unwrap_payload(payload: dict[str, Any]) -> tuple[str, dict[str, Any], datetime | None]:
    data = dict(payload)
    event = data.pop("event", data.pop("message", "log"))
    timestamp = _parse_iso_timestamp(data.pop("timestamp", None))
    for key in _META_KEYS:
        data.pop(key, None)

    if isinstance(event, str):
        nested = _parse_json_payload(event)
        if nested:
            nested_event, nested_data, nested_ts = _unwrap_payload(nested)
            nested_data.update(data)
            return nested_event, nested_data, nested_ts or timestamp

    return str(event), data, timestamp


def extract_log_data(record: logging.LogRecord) -> tuple[str, dict[str, Any], datetime | None]:
    extra = getattr(record, "extra_data", None)
    if extra:
        event = str(getattr(record, "event", record.getMessage()))
        return event, dict(extra), None

    message = record.getMessage()
    payload = _parse_json_payload(message)
    if payload:
        return _unwrap_payload(payload)

    return message, {}, None


def _looks_human_formatted(line: str) -> bool:
    return bool(_HUMAN_LINE_RE.match(line))


def format_log_line(line: str) -> str:
    stripped = line.strip()
    if not stripped:
        return ""
    if _looks_human_formatted(stripped):
        return stripped

    payload = _parse_json_payload(stripped)
    if payload:
        event, data, timestamp = _unwrap_payload(payload)
        return format_log_event(event, timestamp=timestamp, **data)

    return stripped


def _quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _format_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, str):
        if len(value) > 120:
            return _quote(value[:117] + "...")
        return _quote(value)
    if isinstance(value, (int, float)):
        return str(value)
    if value is None:
        return "null"
    return _quote(str(value))


def _format_pairs(data: dict[str, Any], *, skip: frozenset[str] = frozenset()) -> str:
    parts: list[str] = []
    for key, value in data.items():
        if key in skip or value is None:
            continue
        parts.append(f"{key}={_format_field(key, value)}")
    return ", ".join(parts)


def _format_field(key: str, value: Any) -> str:
    if isinstance(value, list) and len(value) == 0:
        return "no"
    if key == "chunks" and isinstance(value, list):
        return _format_chunks(value)
    if key == "graded" and isinstance(value, list):
        return _format_graded(value)
    if key == "sources" and isinstance(value, list):
        return _format_sources(value)
    if key == "config" and isinstance(value, dict):
        return _format_pairs(value)
    if isinstance(value, dict):
        return _format_pairs(value)
    if isinstance(value, list):
        if all(isinstance(item, (str, int, float, bool)) for item in value):
            return ", ".join(_format_scalar(item) for item in value[:8])
        return f"{len(value)} items"
    return _format_scalar(value)


def _format_chunks(chunks: list[dict[str, Any]]) -> str:
    if not chunks:
        return "no"
    items: list[str] = []
    for chunk in chunks[:8]:
        chunk_id = chunk.get("chunk_id", "?")
        source = chunk.get("source", "?")
        score = chunk.get("score", "")
        items.append(f"{chunk_id}@{source}({score})")
    suffix = f", +{len(chunks) - 8} more" if len(chunks) > 8 else ""
    return f"{len(chunks)} [{', '.join(items)}{suffix}]"


def _format_graded(graded: list[dict[str, Any]]) -> str:
    if not graded:
        return "no"
    items: list[str] = []
    for item in graded[:8]:
        chunk_id = item.get("chunk_id", "?")
        relevant = "yes" if item.get("relevant") else "no"
        items.append(f"{chunk_id}={relevant}")
    suffix = f", +{len(graded) - 8} more" if len(graded) > 8 else ""
    return f"{len(graded)} [{', '.join(items)}{suffix}]"


def _format_sources(sources: list[dict[str, Any]]) -> str:
    if not sources:
        return "no"
    items: list[str] = []
    for source in sources[:8]:
        name = source.get("source", "?")
        position = source.get("position", "")
        items.append(f"{name}#{position}")
    suffix = f", +{len(sources) - 8} more" if len(sources) > 8 else ""
    return f"{len(sources)} [{', '.join(items)}{suffix}]"


def format_log_event(
    event: str,
    *,
    timestamp: datetime | None = None,
    **data: Any,
) -> str:
    if event == "request_separator":
        return ""

    timestamp_text = format_timestamp(timestamp)
    skip = _META_KEYS

    if event == "tool_call":
        tool_name = data.get("tool_name", "?")
        parts = [f"{timestamp_text}: tool_call {tool_name}"]
        arguments = data.get("arguments")
        if isinstance(arguments, dict) and arguments:
            parts.append(f"arguments: {_format_pairs(arguments)}")
        if data.get("error"):
            parts.append(f"error: {_format_scalar(data['error'])}")
        elif "result" in data:
            result = data["result"]
            if isinstance(result, dict):
                parts.append(f"result: {_format_pairs(result)}")
            else:
                parts.append(f"result: {_format_scalar(result)}")
        return "; ".join(parts)

    if _parse_json_payload(event):
        return format_log_line(event)

    details = _format_pairs(data, skip=skip)
    if details:
        return f"{timestamp_text}: {event}; {details}"
    return f"{timestamp_text}: {event}"


class HumanReadableFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        event, data, timestamp = extract_log_data(record)
        return format_log_event(event, timestamp=timestamp, **data)


def emit_log(logger: logging.Logger, event: str, level: int = logging.INFO, **data: Any) -> None:
    record = logging.LogRecord(
        name=logger.name,
        level=level,
        pathname="",
        lineno=0,
        msg=event,
        args=(),
        exc_info=None,
    )
    record.event = event
    record.extra_data = data
    logger.handle(record)
