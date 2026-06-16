# RAG Knowledge Base MCP Server

MCP-сервер с Corrective RAG-пайплайном на LangGraph, гибридным поиском (BM25 + vector → RRF) и локальной LLM через Ollama.

## Быстрый старт

```bash
git clone <repo> && cd final_project
docker compose up
```

- MCP-сервер работает через stdio (подключение из IDE)
- Log Viewer: [http://localhost:8765](http://localhost:8765) (последние 200 строк, SSE realtime)

## Подключение MCP в VS Code Copilot

Скопируйте `mcp.config.example.json` в настройки MCP вашего редактора. Пример для локального запуска без Docker:

```json
{
  "mcpServers": {
    "rag-knowledge-base": {
      "command": "python",
      "args": ["-m", "rag_mcp"],
      "cwd": "/path/to/final_project"
    }
  }
}
```

## MCP-инструменты


| Инструмент                         | Описание                                      |
| ---------------------------------- | --------------------------------------------- |
| `index_folder(path, glob)`         | Индексация документов в ChromaDB              |
| `ask_question(question)`           | Вопрос с полным Corrective RAG (нужна Ollama) |
| `find_relevant_docs(query, top_k)` | Гибридный поиск без генерации                 |
| `index_status()`                   | Статистика индекса                            |


## Пример использования

1. `index_status()` — проверить, пуст ли индекс
2. `index_folder("./sample_docs/book")` и `index_folder("./sample_docs/code")` — проиндексировать демо-документы
3. `ask_question("Кто главный герой детективов в sample_docs?")` — получить ответ с источниками
4. `find_relevant_docs("createDeepAgent")` — найти релевантные чанки

## Проверочные факты

Специфические факты из `sample_docs/book/` и `sample_docs/code/` для проверки RAG (после индексации обоих каталогов):


| Вопрос | Ожидаемый ответ | Источник |
| --- | --- | --- |
| Кто главный герой детективов? | Майк Душнов | `book/teplyy_sloy.md`, `book/belyy_shum_u_pruda.txt` |
| Где происходит первое дело? | Поместье «Солнечная поляна» (корпоратив NeuroFlow) | `book/teplyy_sloy.md` |
| Кто CTO в «Тёплом слое»? | Павел Волков | `book/teplyy_sloy.md` |
| Кличка маньяка во второй книге? | Смотритель пруда | `book/belyy_shum_u_pruda.txt` |
| Компания-интегратор умного дома? | GrebSmart (владелец — Стас Гребнев) | `book/belyy_shum_u_pruda.txt` |
| Название ЖК у Патриарших? | Резиденция Ледяной | `book/belyy_shum_u_pruda.txt` |
| Как создать агента в deepagents? | `createDeepAgent()` | `code/deepagents/README.md` |
| Версия npm-пакета deepagents? | 1.10.3 | `code/deepagents/package.json` |
| Инструмент планирования в deepagents? | `write_todos` | `code/deepagents/README.md` |


## Конфигурация

Переменные окружения (см. `src/rag_mcp/config.py`):

- `OLLAMA_BASE_URL`, `LLM_MODEL`, `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`
- `CHROMA_PATH`, `CHUNK_SIZE`, `CHUNK_OVERLAP`, `TOP_K`, `RRF_K`
- `LOG_DIR`, `LOG_VIEWER_PORT`

## Разработка

```bash
python -m pip install -e ".[dev]"
python -m pytest tests/          # 54+ тестов
python -m ruff check src tests
python -m rag_mcp --help
```

## Документация

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — архитектура
- [REPORT.md](REPORT.md) — история разработки

