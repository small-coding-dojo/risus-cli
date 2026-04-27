"""E2E test fixtures that spin up real containers."""
from __future__ import annotations
import os
import subprocess
import time
import urllib.request
import urllib.error
import pytest

COMPOSE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "docker-compose.yml")
COMPOSE_FILE = os.path.abspath(COMPOSE_FILE)
PROJECT_NAME = f"risus_e2e_{os.getpid()}"
SERVER_URL = "http://localhost:8765"
WS_URL = "ws://localhost:8765"

_CONTAINER_ENGINE = os.environ.get("CONTAINER_ENGINE", "docker")


def _compose(*args: str) -> list[str]:
    engine = _CONTAINER_ENGINE
    if engine == "docker":
        return ["docker", "compose", "-f", COMPOSE_FILE, "-p", PROJECT_NAME, *args]
    elif engine == "podman":
        return ["podman", "compose", "-f", COMPOSE_FILE, *args]
    else:
        # Assume it's a full command like "podman-compose" or "docker-compose"
        return [engine, "-f", COMPOSE_FILE, "-p", PROJECT_NAME, *args]


def _run_compose(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    cmd = _compose(*args)
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def _wait_healthy(url: str, timeout: float = 60.0, interval: float = 1.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(interval)
    return False


@pytest.fixture(scope="session")
def risus_stack():
    # Use podman-compose if podman is the engine, otherwise docker compose
    engine = _CONTAINER_ENGINE
    if engine in ("docker", "podman"):
        if engine == "podman":
            cmd = ["podman-compose", "-f", COMPOSE_FILE, "up", "-d", "--build"]
        else:
            cmd = ["docker", "compose", "-f", COMPOSE_FILE, "-p", PROJECT_NAME, "up", "-d", "--build"]
    else:
        cmd = [engine, "-f", COMPOSE_FILE, "up", "-d", "--build"]

    subprocess.run(cmd, check=True)

    healthy = _wait_healthy(f"{SERVER_URL}/healthz", timeout=120)
    if not healthy:
        # Dump logs for debugging
        if engine == "podman":
            subprocess.run(["podman-compose", "-f", COMPOSE_FILE, "logs"])
        yield None
        _teardown()
        pytest.fail("Server did not become healthy within 120s")
        return

    yield {"ws_url": WS_URL, "http_url": SERVER_URL}

    _teardown()


def _teardown():
    engine = _CONTAINER_ENGINE
    if engine == "podman":
        subprocess.run(["podman-compose", "-f", COMPOSE_FILE, "down", "-v"], check=False)
    else:
        subprocess.run(
            ["docker", "compose", "-f", COMPOSE_FILE, "-p", PROJECT_NAME, "down", "-v"],
            check=False,
        )


@pytest.fixture
def ws_connect(risus_stack):
    """Factory: open a WebSocket connection as a named client. Returns (ws, frames_received)."""
    import websockets
    import asyncio

    async def _connect(name: str, collect: int = 2):
        ws = await websockets.connect(f"{WS_URL}/ws/{name}")
        frames = []
        for _ in range(collect):
            raw = await asyncio.wait_for(ws.recv(), timeout=5)
            import json
            frames.append(json.loads(raw))
        return ws, frames

    return _connect
