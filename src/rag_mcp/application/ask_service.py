"""Ask question use case: runs Corrective RAG graph."""

from __future__ import annotations

from rag_mcp.application.ask_progress import AskProgressTracker
from rag_mcp.application.progress_tracker import OnProgress
from rag_mcp.config import Settings
from rag_mcp.domain.graph.builder import build_rag_graph
from rag_mcp.domain.graph.nodes import GraphNodes
from rag_mcp.domain.models import Answer
from rag_mcp.domain.ports import LLMPort, RetrieverPort, VectorStorePort
from rag_mcp.logging.pipeline_logger import PipelineLogger


class AskService:
    def __init__(
        self,
        llm: LLMPort,
        retriever: RetrieverPort,
        vector_store: VectorStorePort,
        settings: Settings,
        pipeline_logger: PipelineLogger,
    ) -> None:
        self._llm = llm
        self._vector_store = vector_store
        self._settings = settings
        self._pipeline_logger = pipeline_logger
        self._nodes = GraphNodes(llm, retriever, settings, pipeline_logger)
        self._graph = build_rag_graph(self._nodes, settings)

    async def ask_question(
        self,
        question: str,
        *,
        on_progress: OnProgress | None = None,
    ) -> Answer:
        stats = await self._vector_store.get_stats()
        if stats.chunk_count == 0:
            raise ValueError(
                "Index is empty. Call index_folder first to index documents."
            )
        if not await self._llm.is_available():
            raise ConnectionError(
                f"Ollama is not available at {self._settings.ollama_base_url}. "
                "Start Ollama before asking questions."
            )

        progress = (
            AskProgressTracker(
                on_progress, self._pipeline_logger, self._settings.max_broaden_loops
            )
            if on_progress is not None
            else None
        )
        self._nodes.set_progress(progress)
        try:
            result = await self._graph.ainvoke(
                {
                    "question": question,
                    "query": question,
                    "chunks": [],
                    "graded": [],
                    "relevant": [],
                    "loop_count": 0,
                    "answer": "",
                    "sources": [],
                }
            )
        finally:
            self._nodes.set_progress(None)

        return Answer(
            answer=result.get("answer", ""),
            sources=result.get("sources", []),
        )
