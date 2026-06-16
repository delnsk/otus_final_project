FROM python:3.12-slim AS builder

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir .

FROM python:3.12-slim

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY src/ ./src/
COPY sample_docs/ ./sample_docs/

ENV CHROMA_PATH=/data/chroma
ENV LOG_DIR=/data/logs
ENV OLLAMA_BASE_URL=http://ollama:11434
ENV LLM_MODEL=phi3:mini
ENV EMBEDDING_PROVIDER=ollama
ENV EMBEDDING_MODEL=nomic-embed-text

RUN mkdir -p /data/chroma /data/logs

CMD ["python", "-m", "rag_mcp"]
