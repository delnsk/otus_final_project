"""Structured data chunking by top-level keys."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import yaml

from rag_mcp.domain.chunking.base import BaseChunker
from rag_mcp.domain.models import Chunk, Document


def _serialize_value(value: object) -> str:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


class StructuredChunker(BaseChunker):
    def chunk(self, document: Document) -> list[Chunk]:
        ext = Path(document.source).suffix.lower()
        if ext == ".json":
            data = json.loads(document.content)
        else:
            data = yaml.safe_load(document.content)

        if not isinstance(data, dict):
            text = document.content[: self.chunk_size]
            return [self._make_chunk(document, text, 0)] if text.strip() else []

        chunks: list[Chunk] = []
        for idx, (key, value) in enumerate(data.items()):
            content = f"{key}: {_serialize_value(value)}"
            if len(content) > self.chunk_size:
                content = content[: self.chunk_size]
            chunks.append(
                self._make_chunk(document, content, idx, chunk_id=f"{document.source}:{key}")
            )
        return chunks
