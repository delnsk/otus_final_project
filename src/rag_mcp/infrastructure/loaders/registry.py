"""Document loader registry for supported file formats."""

from __future__ import annotations

from pathlib import Path

from rag_mcp.domain.models import Document
from rag_mcp.domain.ports import DocumentLoaderPort

SUPPORTED_EXTENSIONS = {".md", ".txt", ".py", ".js", ".ts", ".json", ".yaml", ".yml"}


class DocumentLoaderRegistry:
    def supports(self, path: str) -> bool:
        return Path(path).suffix.lower() in SUPPORTED_EXTENSIONS

    def load(self, path: str) -> Document:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {path}")
        ext = p.suffix.lower()
        if ext == ".yml":
            ext = ".yaml"
        content = p.read_text(encoding="utf-8", errors="replace")
        file_type = ext.lstrip(".")
        return Document(source=str(p.resolve()), content=content, file_type=file_type)


class DocumentLoaderAdapter(DocumentLoaderPort):
    def __init__(self, registry: DocumentLoaderRegistry | None = None) -> None:
        self._registry = registry or DocumentLoaderRegistry()

    def supports(self, path: str) -> bool:
        return self._registry.supports(path)

    def load(self, path: str) -> Document:
        return self._registry.load(path)
