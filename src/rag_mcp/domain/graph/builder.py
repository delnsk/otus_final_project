"""LangGraph builder for Corrective RAG."""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from rag_mcp.config import Settings
from rag_mcp.domain.graph.edges import decide_next_step
from rag_mcp.domain.graph.nodes import GraphNodes
from rag_mcp.domain.graph.state import RAGState


def build_rag_graph(nodes: GraphNodes, settings: Settings):
    graph = StateGraph(RAGState)
    graph.add_node("rewrite", nodes.rewrite_query)
    graph.add_node("retrieve", nodes.retrieve)
    graph.add_node("grade", nodes.grade_chunks)
    graph.add_node("broaden", nodes.broaden_query)
    graph.add_node("generate", nodes.generate_answer)

    graph.set_entry_point("rewrite")
    graph.add_edge("rewrite", "retrieve")
    graph.add_edge("retrieve", "grade")
    graph.add_conditional_edges(
        "grade",
        lambda state: decide_next_step(state, settings),
        {"generate": "generate", "broaden": "broaden"},
    )
    graph.add_edge("broaden", "retrieve")
    graph.add_edge("generate", END)

    return graph.compile()
