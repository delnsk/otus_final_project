"""Unit tests for domain models."""

from rag_mcp.domain.models import Answer, Chunk, Document, GradedChunk, IndexStats, Source


def test_chunk_serialization():
    chunk = Chunk(
        chunk_id="test:0",
        content="hello",
        source="/path/file.md",
        position=0,
        file_type="md",
        score=0.95,
    )
    d = chunk.to_dict()
    assert d["chunk_id"] == "test:0"
    assert d["content"] == "hello"
    assert d["score"] == 0.95


def test_document_fields():
    doc = Document(source="a.py", content="code", file_type="py")
    assert doc.to_dict() == {"source": "a.py", "content": "code", "file_type": "py"}


def test_graded_chunk():
    chunk = Chunk("id", "text", "src", 0, "txt")
    gc = GradedChunk(chunk=chunk, relevant=True, reason="yes")
    assert gc.to_dict()["relevant"] is True


def test_answer_with_sources():
    answer = Answer(answer="42", sources=[Source("f.md", 1, "f.md:1")])
    d = answer.to_dict()
    assert d["answer"] == "42"
    assert len(d["sources"]) == 1


def test_index_stats_defaults():
    stats = IndexStats()
    assert stats.file_count == 0
    assert stats.chunk_count == 0
    assert stats.last_indexed_at is None
