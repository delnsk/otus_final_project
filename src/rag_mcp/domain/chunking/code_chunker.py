"""Language-aware code chunking strategy."""

from __future__ import annotations

from langchain_text_splitters import (
    Language,
    RecursiveCharacterTextSplitter,
)

from rag_mcp.domain.chunking.base import BaseChunker
from rag_mcp.domain.models import Chunk, Document

_LANG_MAP: dict[str, Language] = {
    ".py": Language.PYTHON,
    ".js": Language.JS,
    ".ts": Language.TS,
}


class CodeChunker(BaseChunker):
    def chunk(self, document: Document) -> list[Chunk]:
        ext = "." + document.source.rsplit(".", 1)[-1].lower()
        language = _LANG_MAP.get(ext, Language.PYTHON)
        splitter = RecursiveCharacterTextSplitter.from_language(
            language=language,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )
        parts = splitter.split_text(document.content)
        return [
            self._make_chunk(document, part, idx)
            for idx, part in enumerate(parts)
            if part.strip()
        ]
