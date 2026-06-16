"""Unit tests for Settings."""


from rag_mcp.config import Settings


def test_default_settings():
    settings = Settings()
    assert settings.ollama_base_url == "http://localhost:11434"
    assert settings.llm_model == "phi3:mini"
    assert settings.embedding_provider == "chroma"
    assert settings.top_k == 5
    assert settings.rrf_k == 60
    assert settings.chunk_size == 800


def test_env_override(monkeypatch):
    monkeypatch.setenv("TOP_K", "10")
    monkeypatch.setenv("LLM_MODEL", "qwen2.5:3b")
    settings = Settings()
    assert settings.top_k == 10
    assert settings.llm_model == "qwen2.5:3b"


def test_public_dict_no_secrets():
    settings = Settings()
    d = settings.public_dict()
    assert "ollama_base_url" in d
    assert "chroma_path" in d
