"""健康检查 HTTP 服务"""

import json
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

logger = logging.getLogger(__name__)


class HealthHandler(BaseHTTPRequestHandler):
    """健康检查请求处理器"""

    threads: list = []
    es_writer = None

    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {"status": "healthy"})
        elif self.path == "/ready":
            ready = self._check_ready()
            if ready:
                self._send_json(200, {"status": "ready"})
            else:
                self._send_json(503, {"status": "not_ready"})
        elif self.path == "/stats":
            self._send_json(200, self._get_stats())
        else:
            self._send_json(404, {"error": "not found"})

    def _send_json(self, code: int, data: dict):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def _check_ready(self) -> bool:
        alive = sum(1 for t in self.threads if t.is_alive())
        return alive > 0

    def _get_stats(self) -> dict:
        stats = {
            "threads": [
                {"name": t.name, "alive": t.is_alive()}
                for t in self.threads
            ],
        }
        if self.es_writer:
            stats["es_writer"] = {
                "total_written": self.es_writer.total_written,
                "buffered": self.es_writer.buffered_count,
            }
        return stats

    def log_message(self, format, *args):
        logger.debug(f"health: {args}")


class HealthServer:
    """健康检查服务"""

    def __init__(self, port: int, threads: list, es_writer=None):
        self.port = port
        HealthHandler.threads = threads
        HealthHandler.es_writer = es_writer

    def start(self):
        def _serve():
            server = HTTPServer(("0.0.0.0", self.port), HealthHandler)
            logger.info(f"健康检查服务启动: http://0.0.0.0:{self.port}/health")
            server.serve_forever()

        t = threading.Thread(target=_serve, name="health-server", daemon=True)
        t.start()
