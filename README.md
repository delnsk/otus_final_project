# RAG Knowledge Base MCP Server

MCP-сервер с Corrective RAG-пайплайном на LangGraph, гибридным поиском (BM25 + vector → RRF) и локальной LLM через Ollama.

## Быстрый старт (Docker Compose)

```bash
git clone <repo-url> && cd final_project
docker compose up
```

При первом запуске сервис `model-init` скачивает модели `phi3:mini` и `nomic-embed-text` (может занять несколько минут).

| Сервис | Назначение |
| --- | --- |
| `ollama` | Локальная LLM и эмбеддинги ([http://localhost:11434](http://localhost:11434)) |
| `model-init` | Однократная загрузка моделей |
| `rag-mcp-server` | MCP-сервер (stdio) + Log Viewer |

- **MCP** — подключение из IDE через stdio (см. ниже)
- **Log Viewer** — [http://localhost:8765](http://localhost:8765): последние 200 строк лога, обновление по SSE в реальном времени

## Подключение MCP в VS Code Copilot

1. Скопируйте содержимое [`mcp.config.example.json`](mcp.config.example.json) в настройки MCP редактора (`.vscode/mcp.json` или глобальный конфиг Copilot).

Пример для **Docker Compose** (рекомендуется при сдаче):

```json
{
  "mcpServers": {
    "rag-knowledge-base": {
      "command": "docker",
      "args": [
        "compose",
        "-f",
        "${workspaceFolder}/docker-compose.yml",
        "run",
        "--rm",
        "-T",
        "rag-mcp-server",
        "python",
        "-m",
        "rag_mcp"
      ],
      "env": {
        "OLLAMA_BASE_URL": "http://host.docker.internal:11434"
      }
    }
  }
}
```

Пример для **локального запуска** без Docker (нужны Python 3.11+, установленный Ollama с моделями):

```json
{
  "mcpServers": {
    "rag-knowledge-base": {
      "command": "python",
      "args": ["-m", "rag_mcp"],
      "cwd": "/path/to/final_project",
      "env": {
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "LLM_MODEL": "phi3:mini",
        "EMBEDDING_PROVIDER": "ollama",
        "EMBEDDING_MODEL": "nomic-embed-text"
      }
    }
  }
}
```

2. Перезапустите MCP в IDE — агент должен увидеть 5 инструментов с содержательными `description`.

## MCP-инструменты

| Инструмент | Описание |
| --- | --- |
| `index_folder(path, glob)` | Индексация документов в ChromaDB |
| `ask_question(question)` | Вопрос с полным Corrective RAG (нужна Ollama) |
| `find_relevant_docs(query, top_k)` | Гибридный поиск без генерации |
| `index_status()` | Статистика индекса |
| `clear_index()` | Полная очистка индекса (ChromaDB + BM25); файлы на диске не удаляются |

## Сценарий проверки (процесс сдачи)

### Шаг 1. Проверка пустого индекса

```
index_status()
```

Ожидание: 0 файлов, 0 чанков (или пустая статистика).

### Шаг 2. Индексация демо-документов

```
index_folder("./sample_docs/book")
index_folder("./sample_docs/code")
```

Корпус `sample_docs/` (~1.9 МБ): два детектива про Майка Душнова и исходники TypeScript-библиотеки `deepagents`.

### Шаг 3. Статистика после индексации

```
index_status()
```

Ожидание: ненулевое число файлов и чанков, время последней индексации.

### Шаг 4. Вопросы через агента IDE

Спросите у агента (без явного указания инструмента) — он должен сам выбрать `ask_question` по `description`:

- «Кто главный герой детективов в базе знаний?»
- «Как создать агента в deepagents?»
- «Какая версия npm-пакета deepagents?»

Ответ должен содержать **проверочный факт** и **источник** из `sample_docs/`.

### Шаг 5. Прямая проверка инструментов (MCP Inspector / IDE)

```
find_relevant_docs("createDeepAgent", 5)
find_relevant_docs("Майк Душнов", 5)
```

Ожидание: ранжированные чанки с `source`, `position`, `score`.

## Проверочные факты

Специфические факты из `sample_docs/book/` и `sample_docs/code/` (после индексации обоих каталогов):

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

Переменные окружения (см. [`src/rag_mcp/config.py`](src/rag_mcp/config.py)):

| Переменная | По умолчанию | Назначение |
| --- | --- | --- |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | URL Ollama API |
| `LLM_MODEL` | `phi3:mini` | Модель для rewrite/grade/generate |
| `EMBEDDING_PROVIDER` | `chroma` | `chroma` или `ollama` |
| `EMBEDDING_MODEL` | `nomic-embed-text` | Модель эмбеддингов (для `ollama`) |
| `CHROMA_PATH` | `./data/chroma` | Путь к ChromaDB |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `1000` / `200` | Параметры чанкинга |
| `TOP_K` / `RRF_K` | `5` / `60` | Retrieval и RRF |
| `LOG_DIR` | `./data/logs` | Каталог логов |
| `LOG_VIEWER_PORT` | `8765` | Порт Log Viewer |

## Разработка

```bash
python -m pip install -e ".[dev]"
python -m pytest tests/          # 58 тестов
python -m ruff check src tests
python -m rag_mcp --help
```

CI (GitHub Actions): lint (`ruff`) + `pytest` + сборка Docker-образа — см. [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## Документация

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — архитектура, граф LangGraph, SOLID-структура
- [REPORT.md](REPORT.md) — история разработки, AI-инструменты, промпты
- [docs/implement_plan.md](docs/implement_plan.md) — пошаговый план реализации
