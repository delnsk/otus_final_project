"""MCP tool definitions with rich descriptions."""

from __future__ import annotations

from typing import Annotated, Any

from rag_mcp.application.ask_service import AskService
from rag_mcp.application.index_service import IndexService
from rag_mcp.application.search_service import SearchService
from rag_mcp.application.status_service import StatusService
from rag_mcp.mcp.middleware import MCPLoggingMiddleware, with_logging


class MCPTools:
    def __init__(
        self,
        index_service: IndexService,
        ask_service: AskService,
        search_service: SearchService,
        status_service: StatusService,
        middleware: MCPLoggingMiddleware,
    ) -> None:
        self._index = index_service
        self._ask = ask_service
        self._search = search_service
        self._status = status_service
        self._middleware = middleware

    async def index_folder(self, path: str, glob: str = "**/*") -> dict[str, Any]:
        try:
            stats = await self._index.index_folder(path, glob)
            return stats.to_dict()
        except FileNotFoundError as exc:
            return {"error": str(exc), "file_count": 0, "chunk_count": 0}

    async def ask_question(self, question: str) -> dict[str, Any]:
        try:
            answer = await self._ask.ask_question(question)
            return answer.to_dict()
        except (ValueError, ConnectionError) as exc:
            return {"error": str(exc), "answer": "", "sources": []}
        except Exception as exc:
            return {"error": f"Failed to answer: {exc}", "answer": "", "sources": []}

    async def find_relevant_docs(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        try:
            chunks = await self._search.find_relevant_docs(query, top_k)
            return [c.to_dict() for c in chunks]
        except Exception as exc:
            return [{"error": str(exc)}]

    async def index_status(self) -> dict[str, Any]:
        stats = await self._status.get_status()
        return stats.to_dict()

    def register(self, mcp: Any) -> None:
        @mcp.tool(
            description=(
                "Index documents from a local folder into the knowledge base. "
                "Scans files matching the glob pattern, splits them into chunks, "
                "creates embeddings, and stores them in ChromaDB. "
                "Use this BEFORE asking questions about documents. "
                "Supports .md, .txt, .py, .js, .ts, .json, .yaml files."
            )
        )
        async def index_folder(
            path: Annotated[
                str,
                "Absolute or relative path to the local folder with documents to index "
                "(e.g. './sample_docs/book').",
            ],
            glob: Annotated[
                str,
                (
                    "Glob pattern for selecting files within the folder "
                    "(e.g. '**/*' for all files recursively, '*.md' for markdown only)."
                ),
            ] = "**/*",
        ) -> dict:
            fn = with_logging(self._middleware, "index_folder", self.index_folder)
            return await fn(path=path, glob=glob)

        @mcp.tool(
            description=(
                "Ask a natural language question about indexed documents. "
                "Runs the full Corrective RAG pipeline: query rewriting, "
                "hybrid search (BM25 + vector), relevance grading, "
                "and answer generation with source citations. "
                "Requires documents to be indexed first via index_folder. "
                "Uses local LLM via Ollama."
            )
        )
        async def ask_question(
            question: Annotated[
                str,
                "Natural language question about documents already indexed in the knowledge base.",
            ],
        ) -> dict:
            fn = with_logging(self._middleware, "ask_question", self.ask_question)
            return await fn(question=question)

        @mcp.tool(
            description=(
                "Find relevant document chunks for a search query without generating an answer. "
                "Uses hybrid retrieval: BM25 keyword search combined with vector semantic search, "
                "merged via Reciprocal Rank Fusion (RRF). "
                "Returns ranked chunks with source paths, positions, and scores. "
                "Use for exploring what documents match a query."
            )
        )
        async def find_relevant_docs(
            query: Annotated[
                str,
                "Search query to find matching document chunks via hybrid BM25 + vector retrieval.",
            ],
            top_k: Annotated[
                int,
                "Maximum number of top-ranked chunks to return (default: 5).",
            ] = 5,
        ) -> list:
            fn = with_logging(
                self._middleware, "find_relevant_docs", self.find_relevant_docs
            )
            return await fn(query=query, top_k=top_k)

        @mcp.tool(
            description=(
                "Get statistics about the current document index. "
                "Returns the number of indexed files, total chunks, "
                "and timestamp of the last indexing operation. "
                "Use to check if documents have been indexed before asking questions."
            )
        )
        async def index_status() -> dict:
            fn = with_logging(self._middleware, "index_status", self.index_status)
            return await fn()

        self._middleware.log_list_tools(4)
