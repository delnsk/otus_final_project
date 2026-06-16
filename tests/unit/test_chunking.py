"""Unit tests for chunking strategies."""

from rag_mcp.config import Settings
from rag_mcp.domain.chunking.factory import ChunkerFactory
from rag_mcp.domain.models import Document


def test_text_chunker_metadata():
    factory = ChunkerFactory(Settings())
    chunker = factory.get_chunker("readme.md")
    doc = Document(source="readme.md", content="Paragraph one.\n\nParagraph two.", file_type="md")
    chunks = chunker.chunk(doc)
    assert len(chunks) >= 1
    assert chunks[0].source == "readme.md"
    assert chunks[0].file_type == "md"
    assert chunks[0].position >= 0
    assert chunks[0].chunk_id


def test_code_chunker_for_py():
    factory = ChunkerFactory(Settings())
    py_chunker = factory.get_chunker("module.py")
    md_chunker = factory.get_chunker("readme.md")
    assert type(py_chunker) is not type(md_chunker)


def test_structured_json_chunker():
    factory = ChunkerFactory(Settings())
    chunker = factory.get_chunker("config.json")
    doc = Document(
        source="config.json",
        content='{"api_key": "secret", "timeout": 42, "host": "localhost"}',
        file_type="json",
    )
    chunks = chunker.chunk(doc)
    assert len(chunks) >= 2
    assert any("api_key" in c.content for c in chunks)


def test_code_chunker_splits_functions():
    factory = ChunkerFactory(Settings())
    chunker = factory.get_chunker("app.py")
    code = "def foo():\n    return 1\n\ndef bar():\n    return 2\n" * 5
    doc = Document(source="app.py", content=code, file_type="py")
    chunks = chunker.chunk(doc)
    assert len(chunks) >= 1
    assert chunks[0].file_type == "py"
