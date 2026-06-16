"""Domain data models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Chunk:
    chunk_id: str
    content: str
    source: str
    position: int
    file_type: str
    score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Document:
    source: str
    content: str
    file_type: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GradedChunk:
    chunk: Chunk
    relevant: bool
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"chunk": self.chunk.to_dict(), "relevant": self.relevant, "reason": self.reason}


@dataclass
class Source:
    source: str
    position: int
    chunk_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class IndexStats:
    file_count: int = 0
    chunk_count: int = 0
    last_indexed_at: datetime | None = None
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_count": self.file_count,
            "chunk_count": self.chunk_count,
            "last_indexed_at": self.last_indexed_at.isoformat() if self.last_indexed_at else None,
            "errors": self.errors,
        }


@dataclass
class Answer:
    answer: str
    sources: list[Source] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"answer": self.answer, "sources": [s.to_dict() for s in self.sources]}
