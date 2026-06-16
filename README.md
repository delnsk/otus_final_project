# RAG Knowledge Base MCP Server

MCP-сервер с Corrective RAG-пайплайном на LangGraph, гибридным поиском (BM25 + vector → RRF) и локальной LLM через Ollama.

## Быстрый старт

```bash
git clone <repo> && cd final_project_2
docker compose up
```

- MCP-сервер работает через stdio (подключение из IDE)
- Log Viewer: http://localhost:8765 (последние 200 строк, SSE realtime)

## Подключение MCP в VS Code Copilot

Скопируйте `mcp.config.example.json` в настройки MCP вашего редактора. Пример для локального запуска без Docker:

```json
{
  "mcpServers": {
    "rag-knowledge-base": {
      "command": "python",
      "args": ["-m", "rag_mcp"],
      "cwd": "/path/to/final_project_2"
    }
  }
}
```

## MCP-инструменты

| Инструмент | Описание |
|---|---|
| `index_folder(path, glob)` | Индексация документов в ChromaDB |
| `ask_question(question)` | Вопрос с полным Corrective RAG (нужна Ollama) |
| `find_relevant_docs(query, top_k)` | Гибридный поиск без генерации |
| `index_status()` | Статистика индекса |

## Пример использования

1. `index_status()` — проверить, пуст ли индекс
2. `index_folder("./sample_docs")` — проиндексировать демо-документы
3. `ask_question("Какой кодовый номер проекта Zephyr?")` — получить ответ с источниками
4. `find_relevant_docs("TOKEN_EXPIRY_HOURS")` — найти релевантные чанки

## Проверочные факты

Специфические факты из `sample_docs/` для проверки RAG:

| Вопрос | Ожидаемый ответ | Источник |
|---|---|---|
| Какой кодовый номер проекта? | Zephyr-7742 | overview.md, config.py, settings.json |
| Значение TOKEN_EXPIRY_HOURS? | 47 | config.py, api.js, types.ts |
| Максимальное число повторов API? | 13 | notes.txt, settings.json |
| Имя главного архитектора? | Dr. Elena Vostrikova | overview.md, deployment.yaml |
| Дата назначения архитектора? | 2019-03-17 | settings.json, deployment.yaml |
| Имя сервера? | atlas-node-881.internal.corp | notes.txt, config.py |
| Размер пула соединений БД? | 17 | deployment.yaml, settings.json |

## Конфигурация

Переменные окружения (см. `src/rag_mcp/config.py`):

- `OLLAMA_BASE_URL`, `LLM_MODEL`, `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`
- `CHROMA_PATH`, `CHUNK_SIZE`, `CHUNK_OVERLAP`, `TOP_K`, `RRF_K`
- `LOG_DIR`, `LOG_VIEWER_PORT`

## Разработка

```bash
pip install -e ".[dev]"
pytest tests/          # 54+ тестов
ruff check src tests
python -m rag_mcp --help
```

## Документация

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — архитектура
- [REPORT.md](REPORT.md) — история разработки
