"""Local fixtures server for obstacle course tests."""
from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest


class _FixturesHandler(BaseHTTPRequestHandler):
    """Minimal fixtures server for the register/CDP flow."""

    def log_message(self, format: str, *args: object) -> None:
        pass

    def do_GET(self) -> None:
        if self.path == "/api/user/info":
            self._json_response({"ok": True, "data": {"email": "test@example.com", "id": "123"}})
        elif self.path == "/api/api_key/list":
            self._json_response({"ok": True, "data": [{"name": "default", "key": "sk-test"}]})
        else:
            self._json_response({"ok": True}, status=404)

    def do_POST(self) -> None:
        if self.path == "/api/auth/email/send-code":
            self._json_response({"ok": True, "code": "123456"})
        elif self.path == "/api/auth/email/verify-code":
            self._json_response({"ok": True, "token": "session-token"})
        elif self.path == "/api/api_key":
            self._json_response({"ok": True, "key": "sk-created"})
        else:
            self._json_response({"ok": True}, status=404)

    def _json_response(self, data: dict, status: int = 200) -> None:
        import json
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@pytest.fixture(scope="module")
def fixtures_server() -> str:
    """Yield the base URL of a local fixtures server."""
    server = HTTPServer(("127.0.0.1", 0), _FixturesHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    url = f"http://{host}:{port}"
    try:
        yield url
    finally:
        server.shutdown()
        server.server_close()
