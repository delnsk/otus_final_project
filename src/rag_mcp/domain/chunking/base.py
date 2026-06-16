"""Chunking strategies for different document types."""

from __future__ import annotations

from abc import ABC, abstractmethod

from rag_mcp.domain.models import Chunk, Document


class BaseChunker(ABC):
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 100) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    @abstractmethod
    def chunk(self, document: Document) -> list[Chunk]:
        ...

    def _make_chunk(
        self,
        document: Document,
        content: str,
        position: int,
        chunk_id: str | None = None,
    ) -> Chunk:
        cid = chunk_id or f"{document.source}:{position}"
        return Chunk(
            chunk_id=cid,
            content=content,
            source=document.source,
            position=position,
            file_type=document.file_type,
        )
