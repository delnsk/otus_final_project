"""Entry point: MCP server + Log Viewer."""

from __future__ import annotations

import argparse
import asyncio


def main() -> None:
    parser = argparse.ArgumentParser(description="RAG Knowledge Base MCP Server")
    parser.parse_known_args()

    from rag_mcp.config import Settings
    from rag_mcp.container import Container

    settings = Settings()
    container = Container(settings)
    services = container.build()
    asyncio.run(services.run())


if __name__ == "__main__":
    main()
