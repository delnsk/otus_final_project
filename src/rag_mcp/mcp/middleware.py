"""MCP middleware for logging tool calls."""

from __future__ import annotations

import json
import logging
from typing import Any, Callable

from rag_mcp.logging.formatter import emit_log


class MCPLoggingMiddleware:
    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger
        self._ask_question_count = 0

    def _log(self, event: str, **data: Any) -> None:
        emit_log(self._logger, event, **data)

    def log_request_separator(self) -> None:
        if self._ask_question_count > 0:
            self._log("request_separator")
        self._ask_question_count += 1

    def log_list_tools(self, tool_count: int) -> None:
        self._log("list_tools", tool_count=tool_count)

    def log_tool_call(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        result: Any = None,
        error: str | None = None,
    ) -> None:
        self._log(
            "tool_call",
            tool_name=tool_name,
            arguments=arguments,
            result=_safe_serialize(result),
            error=error,
        )


def _safe_serialize(obj: Any) -> Any:
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: _safe_serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_safe_serialize(i) for i in obj]
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    try:
        return json.loads(json.dumps(obj, default=str))
    except (TypeError, ValueError):
        return str(obj)


def with_logging(
    middleware: MCPLoggingMiddleware,
    tool_name: str,
    fn: Callable,
) -> Callable:
    async def wrapper(**kwargs: Any) -> Any:
        if tool_name == "ask_question":
            middleware.log_request_separator()
        try:
            result = await fn(**kwargs)
            middleware.log_tool_call(tool_name, kwargs, result=result)
            return result
        except Exception as exc:
            middleware.log_tool_call(tool_name, kwargs, error=str(exc))
            raise

    return wrapper
