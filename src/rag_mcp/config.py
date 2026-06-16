"""Application settings loaded from environment and .env file."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    llm_model: str = Field(default="phi3:mini", alias="LLM_MODEL")
    embedding_provider: str = Field(default="chroma", alias="EMBEDDING_PROVIDER")
    embedding_model: str = Field(default="nomic-embed-text", alias="EMBEDDING_MODEL")
    chroma_path: Path = Field(default=Path("./data/chroma"), alias="CHROMA_PATH")
    chunk_size: int = Field(default=800, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=100, alias="CHUNK_OVERLAP")
    top_k: int = Field(default=5, alias="TOP_K")
    rrf_k: int = Field(default=60, alias="RRF_K")
    grade_relevance_threshold: int = Field(default=3, alias="GRADE_RELEVANCE_THRESHOLD")
    max_broaden_loops: int = Field(default=2, alias="MAX_BROADEN_LOOPS")
    log_dir: Path = Field(default=Path("./data/logs"), alias="LOG_DIR")
    log_max_bytes: int = Field(default=1_000_000, alias="LOG_MAX_BYTES")
    log_viewer_port: int = Field(default=8765, alias="LOG_VIEWER_PORT")

    def public_dict(self) -> dict:
        """Config snapshot safe for logging (no secrets)."""
        return {
            "ollama_base_url": self.ollama_base_url,
            "llm_model": self.llm_model,
            "embedding_provider": self.embedding_provider,
            "embedding_model": self.embedding_model,
            "chroma_path": str(self.chroma_path),
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "top_k": self.top_k,
            "rrf_k": self.rrf_k,
            "grade_relevance_threshold": self.grade_relevance_threshold,
            "max_broaden_loops": self.max_broaden_loops,
            "log_dir": str(self.log_dir),
            "log_max_bytes": self.log_max_bytes,
            "log_viewer_port": self.log_viewer_port,
        }
