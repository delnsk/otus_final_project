"""Chunker factory: select strategy by file extension."""

from __future__ import annotations

from rag_mcp.config import Settings
from rag_mcp.domain.chunking.base import BaseChunker
from rag_mcp.domain.chunking.code_chunker import CodeChunker
from rag_mcp.domain.chunking.structured_chunker import StructuredChunker
from rag_mcp.domain.chunking.text_chunker import TextChunker
from rag_mcp.domain.ports import ChunkerPort

_TEXT_EXTS = {".md", ".txt"}
_CODE_EXTS = {".py", ".js", ".ts"}
_STRUCT_EXTS = {".json", ".yaml", ".yml"}


class ChunkerFactory:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._cache: dict[str, BaseChunker] = {}

    def get_chunker(self, path: str) -> ChunkerPort:
        ext = "." + path.rsplit(".", 1)[-1].lower() if "." in path else ""
        if ext == ".yml":
            ext = ".yaml"
        if ext not in self._cache:
            if ext in _TEXT_EXTS:
                self._cache[ext] = TextChunker(
                    self._settings.chunk_size, self._settings.chunk_overlap
                )
            elif ext in _CODE_EXTS:
                self._cache[ext] = CodeChunker(
                    self._settings.chunk_size, self._settings.chunk_overlap
                )
            elif ext in _STRUCT_EXTS:
                self._cache[ext] = StructuredChunker(
                    self._settings.chunk_size, self._settings.chunk_overlap
                )
            else:
                self._cache[ext] = TextChunker(
                    self._settings.chunk_size, self._settings.chunk_overlap
                )
        return self._cache[ext]
