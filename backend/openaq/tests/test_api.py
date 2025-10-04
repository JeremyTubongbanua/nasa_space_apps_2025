from __future__ import annotations

import json
import socket
import threading
import time
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request

from werkzeug.serving import make_server

from main import app


class LiveServer(threading.Thread):
    def __init__(self, host: str, port: int) -> None:
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.ready = threading.Event()
        self._startup_error: Exception | None = None
        self._server = None
        self._ctx = None

    def run(self) -> None:
        try:
            self._server = make_server(self.host, self.port, app)
            self._ctx = app.app_context()
            self._ctx.push()
            self.ready.set()
            self._server.serve_forever()
        except Exception as exc:  # pragma: no cover - debug path
            self._startup_error = exc
            self.ready.set()

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
        if self._ctx is not None:
            self._ctx.pop()


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_for_health(base_url: str, timeout: float = 10.0) -> bool:
    deadline = time.time() + timeout
    url = f"{base_url}/health"
    while time.time() < deadline:
        try:
            with urllib_request.urlopen(url, timeout=1) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.25)
    return False


def _http_get_json(url: str) -> Any:
    with urllib_request.urlopen(url, timeout=5) as resp:
        payload = resp.read().decode("utf-8")
    return json.loads(payload)


def run_live_checks() -> None:
    host = "127.0.0.1"
    try:
        port = _find_free_port()
    except PermissionError as exc:
        raise RuntimeError("Unable to bind to a local TCP port; live server checks cannot run in this environment.") from exc

    server = LiveServer(host, port)
    server.start()
    server.ready.wait(timeout=5)

    if server._startup_error is not None:
        server.stop()
        raise RuntimeError(f"Server failed to start: {server._startup_error}")

    base_url = f"http://{host}:{port}"
    if not _wait_for_health(base_url):
        server.stop()
        raise RuntimeError("Server failed to become healthy within timeout")

    try:
        health = _http_get_json(f"{base_url}/health")
        assert health.get("status") == "ok"

        locations = _http_get_json(f"{base_url}/locations?parameters_id=2&limit=3")
        assert "results" in locations and len(locations["results"]) == 3

        near = _http_get_json(
            f"{base_url}/locations?coordinates=136.90610,35.14942&radius=12000&limit=2"
        )
        assert "results" in near

        bbox = _http_get_json(
            f"{base_url}/locations?bbox=-118.668153,33.703935,-118.155358,34.337306&limit=2"
        )
        assert "results" in bbox

        measurements = _http_get_json(f"{base_url}/sensors/3917/measurements?limit=2")
        assert measurements["results"], "Expected measurement results"

        days = _http_get_json(f"{base_url}/sensors/3917/days?limit=2")
        assert days["results"], "Expected daily aggregation results"

        yearly = _http_get_json(f"{base_url}/sensors/3917/days/yearly?limit=2")
        assert yearly["results"], "Expected yearly aggregation results"

        latest = _http_get_json(f"{base_url}/parameters/2/latest?limit=2")
        assert latest["results"], "Expected latest parameter results"
    finally:
        server.stop()
        server.join(timeout=2)


if __name__ == "__main__":
    run_live_checks()
    print("Live server checks passed.")
