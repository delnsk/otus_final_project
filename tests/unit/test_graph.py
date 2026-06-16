"""Unit tests for LangGraph nodes and edges."""

import pytest

from rag_mcp.config import Settings
from rag_mcp.domain.graph.edges import decide_next_step
from rag_mcp.domain.graph.nodes import GraphNodes
from rag_mcp.domain.graph.state import RAGState
from rag_mcp.domain.models import Chunk
from rag_mcp.logging.pipeline_logger import PipelineLogger
from tests.unit.test_ports import MockLLM, MockRetriever


@pytest.fixture
def settings():
    return Settings(grade_relevance_threshold=2, max_broaden_loops=2)


@pytest.fixture
def nodes(settings, tmp_path):
    logger = __import__("logging").getLogger("test_graph")
    pl = PipelineLogger(logger)
    retriever = MockRetrieverWithChunks()
    return GraphNodes(MockLLM(), retriever, settings, pl)


class MockRetrieverWithChunks(MockRetriever):
    async def retrieve(self, query: str, top_k: int) -> list[Chunk]:
        return [
            Chunk("c1", "auth uses JWT tokens", "auth.md", 0, "md"),
            Chunk("c2", "database config", "db.md", 0, "md"),
        ]


class MockLLMYes(MockLLM):
    async def generate(self, prompt: str) -> str:
        if "relevant" in prompt.lower() or "yes" in prompt.lower():
            return "yes"
        if "rewrite" in prompt.lower() or "search query" in prompt.lower():
            return "authentication JWT"
        if "broaden" in prompt.lower():
            return "broader auth query"
        return "The answer is JWT authentication."


def test_decide_enough_relevant(monkeypatch):
    monkeypatch.setenv("GRADE_RELEVANCE_THRESHOLD", "2")
    settings = Settings()
    state: RAGState = {
        "relevant": [Chunk("a", "", "", 0, ""), Chunk("b", "", "", 0, "")],
        "loop_count": 0,
    }
    assert decide_next_step(state, settings) == "generate"


def test_decide_broaden_on_few(settings):
    state: RAGState = {"relevant": [], "loop_count": 0}
    assert decide_next_step(state, settings) == "broaden"


def test_decide_force_generate_at_max_loops(settings):
    state: RAGState = {"relevant": [], "loop_count": 2}
    assert decide_next_step(state, settings) == "generate"


@pytest.mark.asyncio
async def test_rewrite_node(settings, tmp_path):
    logger = __import__("logging").getLogger("test")
    pl = PipelineLogger(logger)
    nodes = GraphNodes(MockLLMYes(), MockRetrieverWithChunks(), settings, pl)
    state: RAGState = {"question": "How does auth work?"}
    result = await nodes.rewrite_query(state)
    assert "query" in result
    assert len(result["query"]) > 0


@pytest.mark.asyncio
async def test_retrieve_node(settings, tmp_path):
    logger = __import__("logging").getLogger("test")
    pl = PipelineLogger(logger)
    nodes = GraphNodes(MockLLMYes(), MockRetrieverWithChunks(), settings, pl)
    state: RAGState = {"question": "auth?", "query": "auth"}
    result = await nodes.retrieve(state)
    assert len(result["chunks"]) == 2


@pytest.mark.asyncio
async def test_grade_node(settings):
    logger = __import__("logging").getLogger("test")
    pl = PipelineLogger(logger)
    nodes = GraphNodes(MockLLMYes(), MockRetrieverWithChunks(), settings, pl)
    chunks = [Chunk("c1", "text", "src", 0, "md")]
    state: RAGState = {"question": "q", "chunks": chunks}
    result = await nodes.grade_chunks(state)
    assert len(result["graded"]) == 1
    assert len(result["relevant"]) == 1


@pytest.mark.asyncio
async def test_generate_node(settings):
    logger = __import__("logging").getLogger("test")
    pl = PipelineLogger(logger)
    nodes = GraphNodes(MockLLMYes(), MockRetrieverWithChunks(), settings, pl)
    chunks = [Chunk("c1", "JWT auth", "auth.md", 0, "md")]
    state: RAGState = {"question": "How auth?", "relevant": chunks}
    result = await nodes.generate_answer(state)
    assert result["answer"]
    assert len(result["sources"]) == 1


@pytest.mark.asyncio
async def test_graph_e2e_with_mock(settings):
    from rag_mcp.domain.graph.builder import build_rag_graph

    logger = __import__("logging").getLogger("test")
    pl = PipelineLogger(logger)
    graph = build_rag_graph(MockLLMYes(), MockRetrieverWithChunks(), settings, pl)
    result = await graph.ainvoke({
        "question": "How does authentication work?",
        "query": "",
        "chunks": [],
        "graded": [],
        "relevant": [],
        "loop_count": 0,
        "answer": "",
        "sources": [],
    })
    assert result["answer"]
    assert result["sources"]
