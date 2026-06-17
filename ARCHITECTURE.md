# Архитектура: RAG Knowledge Base MCP-сервер

MCP-сервер превращает локальную папку с документами в поисковую базу знаний.
Разработчик подключает сервер к IDE, индексирует документы и задаёт вопросы.
Внутри — **Corrective RAG** на LangGraph с локальной LLM (Ollama) и гибридным
поиском (BM25 + vector → RRF).

> **Полная документация** (диаграммы, потоки MCP-инструментов, конфигурация,
> логирование, CI, статус реализации): [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

## Компоненты

| Слой | Модули | Ответственность |
| --- | --- | --- |
| Вход | `mcp/`, `logging/viewer.py` | FastMCP (5 инструментов), Log Viewer (SSE) |
| Приложение | `application/*_service.py` | Use cases: индексация, вопрос, поиск, статус, очистка |
| Домен | `domain/graph/`, `domain/chunking/`, `domain/fusion.py` | Corrective RAG, чанкинг, RRF |
| Инфраструктура | `infrastructure/` | Ollama, ChromaDB, BM25, загрузчики |
| Сквозные | `config.py`, `container.py`, `logging/` | Конфигурация, DI, логи с ротацией |

## Corrective RAG (LangGraph)

```
User Query → Rewrite Query → Retrieve (BM25 + vector → RRF)
  → Grade Chunks (yes/no)
    → enough relevant → Generate Answer → answer + sources
    → too few relevant → Broaden Query → Retrieve (max 2 loops)
```

Узлы: `rewrite`, `retrieve`, `grade`, `broaden`, `generate`. Условный переход
после `grade` — по порогу релевантных чанков (`GRADE_RELEVANCE_THRESHOLD`) и
счётчику циклов (`MAX_BROADEN_LOOPS=2`).

## MCP-инструменты

| Инструмент | LLM |
| --- | --- |
| `index_folder(path, glob)` | только эмбеддинги |
| `ask_question(question)` | да (полный граф) |
| `find_relevant_docs(query, top_k)` | нет |
| `index_status()` | нет |
| `clear_index()` | нет (расширение сверх задания) |

## Технологии

Python 3.11+, FastMCP, LangGraph, LangChain text splitters, ChromaDB (in-process),
`rank_bm25`, Ollama, Docker Compose.

## Конфигурация

Единая точка настройки — [`.env.example`](.env.example) → `.env`. Compose
подставляет `${VAR:-default}`; приложение читает те же переменные через
`pydantic-settings` (`src/rag_mcp/config.py`).
