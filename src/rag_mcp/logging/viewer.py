"""HTTP log viewer with SSE realtime tail."""

from __future__ import annotations

import asyncio

from aiohttp import web

from rag_mcp.config import Settings
from rag_mcp.logging.formatter import format_log_line

TAIL_LINES = 200


class LogViewer:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._log_file = settings.log_dir / "rag_mcp.log"

    def _read_last_lines(self, n: int = TAIL_LINES) -> list[str]:
        if not self._log_file.exists():
            return []
        text = self._log_file.read_text(encoding="utf-8", errors="replace")
        if not text:
            return []
        lines = text.split("\n")
        if lines and lines[-1] == "":
            lines.pop()
        return [format_log_line(line) for line in lines[-n:]]

    async def handle_index(self, request: web.Request) -> web.Response:
        lines = self._read_last_lines()
        body = "\n".join(lines)
        html = f"""<!DOCTYPE html>
<html><head><title>RAG MCP Logs</title>
<style>
body {{ font-family: monospace; background: #1e1e1e; color: #d4d4d4; margin: 0; padding: 1em; }}
#log {{ white-space: pre-wrap; word-break: break-all; }}
h1 {{ color: #569cd6; }}
</style></head><body>
<h1>RAG MCP Log Viewer</h1>
<div id="log">{body}</div>
<script>
const log = document.getElementById('log');
const es = new EventSource('/stream');
es.onmessage = (e) => {{
  log.textContent += '\\n' + e.data;
  const lines = log.textContent.split('\\n');
  if (lines.length > {TAIL_LINES}) {{
    log.textContent = lines.slice(-{TAIL_LINES}).join('\\n');
  }}
  window.scrollTo(0, document.body.scrollHeight);
}};
</script></body></html>"""
        return web.Response(text=html, content_type="text/html")

    async def handle_stream(self, request: web.Request) -> web.StreamResponse:
        response = web.StreamResponse(
            status=200,
            headers={
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )
        await response.prepare(request)

        last_size = self._log_file.stat().st_size if self._log_file.exists() else 0
        while True:
            await asyncio.sleep(0.5)
            if not self._log_file.exists():
                continue
            current_size = self._log_file.stat().st_size
            if current_size > last_size:
                with open(self._log_file, "r", encoding="utf-8", errors="replace") as f:
                    f.seek(last_size)
                    new_data = f.read()
                last_size = current_size
                for line in new_data.split("\n"):
                    await response.write(f"data: {format_log_line(line)}\n\n".encode())
        return response

    async def start(self) -> web.AppRunner:
        self._settings.log_dir.mkdir(parents=True, exist_ok=True)
        app = web.Application()
        app.router.add_get("/", self.handle_index)
        app.router.add_get("/stream", self.handle_stream)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", self._settings.log_viewer_port)
        await site.start()
        return runner
