"""Unit tests for Protocol ports with mock implementations."""

from rag_mcp.domain.models import Chunk, Document, IndexStats
from rag_mcp.domain.ports import (
    ChunkerPort,
    DocumentLoaderPort,
    EmbeddingsPort,
    LLMPort,
    LoggerPort,
    RetrieverPort,
    VectorStorePort,
)


class MockLLM:
    async def generate(self, prompt: str) -> str:
        return "mock response"

    async def is_available(self) -> bool:
        return True


class MockEmbeddings:
    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3]] * len(texts)

    async def embed_query(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]


class MockVectorStore:
    async def add(self, chunks, embeddings) -> None:
        pass

    async def search(self, query_embedding, top_k) -> list[Chunk]:
        return []

    async def delete_all(self) -> None:
        pass

    async def get_stats(self) -> IndexStats:
        return IndexStats()

    def get_all_chunks(self) -> list[Chunk]:
        return []


class MockRetriever:
    async def retrieve(self, query: str, top_k: int) -> list[Chunk]:
        return []

    async def rebuild_index(self, chunks: list[Chunk]) -> None:
        pass


class MockLoader:
    def load(self, path: str) -> Document:
        return Document(source=path, content="text", file_type="txt")

    def supports(self, path: str) -> bool:
        return True


class MockChunker:
    def chunk(self, document: Document) -> list[Chunk]:
        return [Chunk("id", document.content, document.source, 0, document.file_type)]


class MockLogger:
    def info(self, event: str, **kwargs) -> None:
        pass

    def error(self, event: str, **kwargs) -> None:
        pass

    def warning(self, event: str, **kwargs) -> None:
        pass


def test_mock_llm_satisfies_protocol():
    assert isinstance(MockLLM(), LLMPort)


def test_mock_embeddings_satisfies_protocol():
    assert isinstance(MockEmbeddings(), EmbeddingsPort)


def test_mock_vector_store_satisfies_protocol():
    assert isinstance(MockVectorStore(), VectorStorePort)


def test_mock_retriever_satisfies_protocol():
    assert isinstance(MockRetriever(), RetrieverPort)


def test_mock_loader_satisfies_protocol():
    assert isinstance(MockLoader(), DocumentLoaderPort)


def test_mock_chunker_satisfies_protocol():
    assert isinstance(MockChunker(), ChunkerPort)


def test_mock_logger_satisfies_protocol():
    assert isinstance(MockLogger(), LoggerPort)
