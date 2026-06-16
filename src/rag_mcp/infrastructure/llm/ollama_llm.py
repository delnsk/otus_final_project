"""Ollama LLM async adapter."""

from __future__ import annotations

import httpx

from rag_mcp.config import Settings


class OllamaLLM:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._base_url = settings.ollama_base_url.rstrip("/")
        self._model = settings.llm_model

    async def generate(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    f"{self._base_url}/api/generate",
                    json={"model": self._model, "prompt": prompt, "stream": False},
                )
                response.raise_for_status()
                return response.json().get("response", "").strip()
            except httpx.ConnectError as exc:
                raise ConnectionError(
                    f"Ollama is not available at {self._base_url}. "
                    "Start Ollama or check OLLAMA_BASE_URL."
                ) from exc
            except httpx.HTTPStatusError as exc:
                raise RuntimeError(
                    f"Ollama API error: {exc.response.status_code} {exc.response.text}"
                ) from exc

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self._base_url}/api/tags")
                return response.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False
