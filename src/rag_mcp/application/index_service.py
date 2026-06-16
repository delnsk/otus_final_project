"""Index folder use case: scan → load → chunk → embed → store."""

from __future__ import annotations

import asyncio
from pathlib import Path

from rag_mcp.config import Settings
from rag_mcp.domain.chunking.factory import ChunkerFactory
from rag_mcp.domain.models import Chunk, IndexStats
from rag_mcp.domain.ports import DocumentLoaderPort, EmbeddingsPort, RetrieverPort, VectorStorePort
from rag_mcp.logging.pipeline_logger import PipelineLogger


class IndexService:
    def __init__(
        self,
        settings: Settings,
        loader: DocumentLoaderPort,
        chunker_factory: ChunkerFactory,
        embeddings: EmbeddingsPort,
        vector_store: VectorStorePort,
        retriever: RetrieverPort,
        pipeline_logger: PipelineLogger,
    ) -> None:
        self._settings = settings
        self._loader = loader
        self._chunker_factory = chunker_factory
        self._embeddings = embeddings
        self._vector_store = vector_store
        self._retriever = retriever
        self._pipeline_logger = pipeline_logger

    async def index_folder(self, path: str, glob_pattern: str = "**/*") -> IndexStats:
        base = Path(path).resolve()
        if not base.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")

        files = sorted(
            str(p.resolve())
            for p in base.glob(glob_pattern)
            if p.is_file() and self._loader.supports(str(p))
        )
        self._pipeline_logger.log_index_scan(str(base), glob_pattern, len(files))

        all_chunks: list[Chunk] = []
        errors: list[str] = []

        for file_path in files:
            try:
                document = await asyncio.to_thread(self._loader.load, file_path)
                self._pipeline_logger.log_index_load(file_path, success=True)
                chunker = self._chunker_factory.get_chunker(file_path)
                chunks = await asyncio.to_thread(chunker.chunk, document)
                self._pipeline_logger.log_index_chunk(file_path, len(chunks))
                all_chunks.extend(chunks)
            except Exception as exc:
                msg = f"{file_path}: {exc}"
                errors.append(msg)
                self._pipeline_logger.log_index_load(file_path, success=False, error=str(exc))

        if all_chunks:
            texts = [c.content for c in all_chunks]
            embeddings = await self._embeddings.embed_documents(texts)
            self._pipeline_logger.log_index_embed(len(all_chunks))
            await self._vector_store.add(all_chunks, embeddings)
            self._pipeline_logger.log_index_store(len(all_chunks))
            all_in_store = self._vector_store.get_all_chunks()
            await self._retriever.rebuild_index(all_in_store)

        stats = await self._vector_store.get_stats()
        stats.errors = errors
        return stats
