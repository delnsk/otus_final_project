"""Unit tests for Reciprocal Rank Fusion."""

from rag_mcp.domain.fusion import reciprocal_rank_fusion
from rag_mcp.domain.models import Chunk


def _chunk(cid: str, score: float = 0.0) -> Chunk:
    return Chunk(cid, f"content-{cid}", f"src/{cid}", 0, "txt", score)


def test_rrf_single_list():
    chunks = [_chunk("a"), _chunk("b"), _chunk("c")]
    result = reciprocal_rank_fusion([chunks], k=60, top_k=2)
    assert len(result) == 2
    assert result[0].chunk_id == "a"


def test_rrf_combines_two_lists():
    list1 = [_chunk("a"), _chunk("b"), _chunk("c")]
    list2 = [_chunk("c"), _chunk("a"), _chunk("d")]
    result = reciprocal_rank_fusion([list1, list2], k=60, top_k=3)
    ids = [c.chunk_id for c in result]
    assert "a" in ids
    assert "c" in ids


def test_rrf_deterministic_order():
    list1 = [_chunk("x"), _chunk("y")]
    list2 = [_chunk("y"), _chunk("x")]
    r1 = reciprocal_rank_fusion([list1, list2], k=60, top_k=2)
    r2 = reciprocal_rank_fusion([list1, list2], k=60, top_k=2)
    assert [c.chunk_id for c in r1] == [c.chunk_id for c in r2]


def test_rrf_scores_assigned():
    result = reciprocal_rank_fusion([[_chunk("a")]], k=60, top_k=1)
    assert result[0].score > 0
