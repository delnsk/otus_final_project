"""Integration tests for document loaders."""

from pathlib import Path

import pytest

from rag_mcp.infrastructure.loaders.registry import DocumentLoaderRegistry

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def registry():
    return DocumentLoaderRegistry()


@pytest.mark.parametrize(
    "filename",
    [
        "sample.md",
        "sample.txt",
        "sample.py",
        "sample.js",
        "sample.ts",
        "sample.json",
        "sample.yaml",
    ],
)
def test_load_each_format(registry, filename):
    path = str(FIXTURES / filename)
    doc = registry.load(path)
    assert doc.content
    assert doc.source
    assert doc.file_type
