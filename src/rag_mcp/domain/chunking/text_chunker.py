"""Text chunking strategy using recursive character splitting."""

from __future__ import annotations

from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag_mcp.domain.chunking.base import BaseChunker
from rag_mcp.domain.models import Chunk, Document


class TextChunker(BaseChunker):
    def chunk(self, document: Document) -> list[Chunk]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        parts = splitter.split_text(document.content)
        return [
            self._make_chunk(document, part, idx)
            for idx, part in enumerate(parts)
            if part.strip()
        ]
