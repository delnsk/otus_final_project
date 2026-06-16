"""Logging setup with rotating file handler and human-readable format."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from rag_mcp.config import Settings
from rag_mcp.logging.formatter import HumanReadableFormatter, emit_log


def setup_logging(settings: Settings) -> logging.Logger:
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    log_file = settings.log_dir / "rag_mcp.log"

    logger = logging.getLogger("rag_mcp")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    handler = RotatingFileHandler(
        str(log_file),
        maxBytes=settings.log_max_bytes,
        backupCount=5,
        encoding="utf-8",
    )
    handler.setFormatter(HumanReadableFormatter())
    logger.addHandler(handler)
    logger.propagate = False

    return logger


def log_startup(logger: logging.Logger, settings: Settings) -> None:
    emit_log(logger, "server_startup", config=settings.public_dict())
