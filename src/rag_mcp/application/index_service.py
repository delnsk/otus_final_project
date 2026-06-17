"""Index folder use case: scan → load → chunk → embed → store."""

from __future__ import annotations

import asyncio
from pathlib import Path

from rag_mcp.application.index_progress import IndexProgressTracker
from rag_mcp.application.progress_tracker import OnProgress
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

    async def index_folder(
        self,
        path: str,
        glob_pattern: str = "**/*",
        *,
        on_progress: OnProgress | None = None,
    ) -> IndexStats:
        progress = (
            IndexProgressTracker(on_progress, self._pipeline_logger)
            if on_progress is not None
            else None
        )

        base = Path(path).resolve()
        if not base.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")

        files = sorted(
            str(p.resolve())
            for p in base.glob(glob_pattern)
            if p.is_file() and self._loader.supports(str(p))
        )
        self._pipeline_logger.log_index_scan(str(base), glob_pattern, len(files))
        if progress is not None:
            await progress.scan_complete(len(files))

        if not files:
            if progress is not None:
                await progress.complete("No files to index")
            stats = await self._vector_store.get_stats()
            stats.errors = []
            return stats

        all_chunks: list[Chunk] = []
        errors: list[str] = []

        for index, file_path in enumerate(files):
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
            if progress is not None:
                await progress.file_processed(index, len(files), file_path)

        if all_chunks:
            embeddings = await self._embed_documents(all_chunks, progress)
            self._pipeline_logger.log_index_embed(len(all_chunks))
            await self._vector_store.add(all_chunks, embeddings)
            self._pipeline_logger.log_index_store(len(all_chunks))
            if progress is not None:
                await progress.store_complete()
            all_in_store = self._vector_store.get_all_chunks()
            await self._retriever.rebuild_index(all_in_store)

        if progress is not None:
            await progress.complete()

        stats = await self._vector_store.get_stats()
        stats.errors = errors
        return stats

    async def _embed_documents(
        self,
        chunks: list[Chunk],
        progress: IndexProgressTracker | None,
    ) -> list[list[float]]:
        texts = [c.content for c in chunks]
        if not texts:
            return []

        if progress is None:
            return await self._embeddings.embed_documents(texts)

        await progress.embed_start(len(texts))
        if len(texts) == 1:
            embeddings = await self._embeddings.embed_documents(texts)
        else:
            embeddings = []
            for index, text in enumerate(texts):
                embedding = await self._embeddings.embed_query(text)
                embeddings.append(embedding)
                await progress.embed_chunk(index, len(texts))
        await progress.embed_complete()
        return embeddings
