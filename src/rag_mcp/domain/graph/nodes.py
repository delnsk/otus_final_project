"""LangGraph nodes for Corrective RAG pipeline."""

from __future__ import annotations

from rag_mcp.application.ask_progress import AskProgressTracker
from rag_mcp.config import Settings
from rag_mcp.domain.graph.state import RAGState
from rag_mcp.domain.models import Chunk, GradedChunk, Source
from rag_mcp.domain.ports import LLMPort, RetrieverPort
from rag_mcp.logging.pipeline_logger import PipelineLogger


class GraphNodes:
    def __init__(
        self,
        llm: LLMPort,
        retriever: RetrieverPort,
        settings: Settings,
        pipeline_logger: PipelineLogger,
    ) -> None:
        self._llm = llm
        self._retriever = retriever
        self._settings = settings
        self._pipeline_logger = pipeline_logger
        self._progress: AskProgressTracker | None = None

    def set_progress(self, progress: AskProgressTracker | None) -> None:
        self._progress = progress

    async def rewrite_query(self, state: RAGState) -> RAGState:
        question = state["question"]
        prompt = (
            "Rewrite the following question into a concise search query "
            "for document retrieval. Return only the query, no explanation.\n\n"
            f"Question: {question}"
        )
        rewritten = await self._llm.generate(prompt)
        query = rewritten.strip() or question
        self._pipeline_logger.log_rewrite(question, query)
        if self._progress is not None:
            await self._progress.rewrite_done()
        return {**state, "query": query}

    async def retrieve(self, state: RAGState) -> RAGState:
        query = state.get("query", state["question"])
        chunks = await self._retriever.retrieve(query, self._settings.top_k)
        chunk_dicts = [
            {"chunk_id": c.chunk_id, "source": c.source, "score": c.score}
            for c in chunks
        ]
        self._pipeline_logger.log_retrieve(query, self._settings.top_k, chunk_dicts)
        if self._progress is not None:
            await self._progress.retrieve_done()
        return {**state, "chunks": chunks}

    async def grade_chunks(self, state: RAGState) -> RAGState:
        question = state["question"]
        chunks = state.get("chunks", [])
        graded: list[GradedChunk] = []
        relevant: list[Chunk] = []

        for index, chunk in enumerate(chunks):
            prompt = (
                "Is the following document chunk relevant to the question? "
                "Answer only 'yes' or 'no'.\n\n"
                f"Question: {question}\n\nChunk:\n{chunk.content[:1000]}"
            )
            response = (await self._llm.generate(prompt)).lower().strip()
            is_relevant = response.startswith("yes") or response == "y"
            gc = GradedChunk(chunk=chunk, relevant=is_relevant, reason=response)
            graded.append(gc)
            if is_relevant:
                relevant.append(chunk)
            if self._progress is not None:
                await self._progress.grade_chunk(index, len(chunks))

        graded_dicts = [
            {"chunk_id": g.chunk.chunk_id, "relevant": g.relevant} for g in graded
        ]
        self._pipeline_logger.log_grade(graded_dicts, len(relevant))
        return {**state, "graded": graded, "relevant": relevant}

    async def broaden_query(self, state: RAGState) -> RAGState:
        question = state["question"]
        query = state.get("query", question)
        loop_count = state.get("loop_count", 0) + 1
        prompt = (
            "Broaden the search query to find more relevant documents. "
            "Return only the new query.\n\n"
            f"Original question: {question}\nCurrent query: {query}"
        )
        broadened = (await self._llm.generate(prompt)).strip() or query
        self._pipeline_logger.log_broaden(broadened, loop_count)
        if self._progress is not None:
            await self._progress.broaden_done(loop_count)
        return {**state, "query": broadened, "loop_count": loop_count}

    async def generate_answer(self, state: RAGState) -> RAGState:
        question = state["question"]
        relevant = state.get("relevant") or state.get("chunks", [])
        context = "\n\n---\n\n".join(
            f"[{c.source} pos={c.position}]\n{c.content}" for c in relevant[:5]
        )
        prompt = (
            "Answer the question based only on the provided context. "
            "If the context is insufficient, say so.\n\n"
            f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
        )
        answer = await self._llm.generate(prompt)
        sources = [
            Source(source=c.source, position=c.position, chunk_id=c.chunk_id)
            for c in relevant[:5]
        ]
        self._pipeline_logger.log_generate(
            answer, [s.to_dict() for s in sources]
        )
        if self._progress is not None:
            await self._progress.generate_done()
        return {**state, "answer": answer, "sources": sources}
