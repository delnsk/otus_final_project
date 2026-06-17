"""Dependency injection container."""

from __future__ import annotations

from dataclasses import dataclass

from rag_mcp.application.ask_service import AskService
from rag_mcp.application.clear_index_service import ClearIndexService
from rag_mcp.application.index_service import IndexService
from rag_mcp.application.search_service import SearchService
from rag_mcp.application.status_service import StatusService
from rag_mcp.config import Settings
from rag_mcp.domain.chunking.factory import ChunkerFactory
from rag_mcp.infrastructure.embeddings.factory import create_embeddings
from rag_mcp.infrastructure.llm.ollama_llm import OllamaLLM
from rag_mcp.infrastructure.loaders.registry import DocumentLoaderAdapter
from rag_mcp.infrastructure.retrieval.bm25_retriever import BM25Retriever
from rag_mcp.infrastructure.retrieval.hybrid_retriever import HybridRetriever
from rag_mcp.infrastructure.retrieval.vector_retriever import VectorRetriever
from rag_mcp.infrastructure.vectorstore.chroma import ChromaVectorStore
from rag_mcp.logging.pipeline_logger import PipelineLogger
from rag_mcp.logging.setup import log_startup, setup_logging
from rag_mcp.logging.viewer import LogViewer
from rag_mcp.mcp.middleware import MCPLoggingMiddleware
from rag_mcp.mcp.server import create_mcp_server
from rag_mcp.mcp.tools import MCPTools


@dataclass
class Services:
    settings: Settings
    index_service: IndexService
    ask_service: AskService
    search_service: SearchService
    status_service: StatusService
    clear_index_service: ClearIndexService
    mcp_server: object
    log_viewer: LogViewer
    logger: object

    async def run(self) -> None:
        log_startup(self.logger, self.settings)
        viewer_runner = await self.log_viewer.start()
        try:
            await self.mcp_server.run_stdio_async()
        finally:
            await viewer_runner.cleanup()


class Container:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()

    def build(self) -> Services:
        settings = self._settings
        logger = setup_logging(settings)
        log_file = settings.log_dir / "rag_mcp.log"
        pipeline_logger = PipelineLogger(logger, log_file=log_file)

        loader = DocumentLoaderAdapter()
        chunker_factory = ChunkerFactory(settings)
        embeddings = create_embeddings(settings)
        vector_store = ChromaVectorStore(settings)
        bm25 = BM25Retriever()
        vector_retriever = VectorRetriever(vector_store, embeddings)
        hybrid_retriever = HybridRetriever(bm25, vector_retriever, settings)
        persisted_chunks = vector_store.get_all_chunks()
        if persisted_chunks:
            hybrid_retriever.hydrate(persisted_chunks)

        llm = OllamaLLM(settings)

        index_service = IndexService(
            settings, loader, chunker_factory, embeddings,
            vector_store, hybrid_retriever, pipeline_logger,
        )
        ask_service = AskService(
            llm, hybrid_retriever, vector_store, settings, pipeline_logger,
        )
        search_service = SearchService(hybrid_retriever, settings, pipeline_logger)
        status_service = StatusService(vector_store)
        clear_index_service = ClearIndexService(
            vector_store, hybrid_retriever, pipeline_logger,
        )

        middleware = MCPLoggingMiddleware(logger)
        mcp_tools = MCPTools(
            index_service,
            ask_service,
            search_service,
            status_service,
            clear_index_service,
            middleware,
        )
        mcp_server = create_mcp_server(mcp_tools)
        log_viewer = LogViewer(settings)

        return Services(
            settings=settings,
            index_service=index_service,
            ask_service=ask_service,
            search_service=search_service,
            status_service=status_service,
            clear_index_service=clear_index_service,
            mcp_server=mcp_server,
            log_viewer=log_viewer,
            logger=logger,
        )
