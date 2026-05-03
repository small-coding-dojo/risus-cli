"""Unit tests for token authentication: server validation, scheme detection, URL derivation."""
from __future__ import annotations
import asyncio
import json
from unittest.mock import patch
import pytest
from fastapi import FastAPI, WebSocket
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from client.ws_client import WSClient
from risus import _http_base_url
from server.locks import LockManager
from server.ws import ConnectionManager

_TOKEN = "valid-token-for-auth-tests"


class _FakePool:
    def __init__(self):
        self._players: dict = {}


async def _fake_load_state(pool):
    return list(pool._players.values())


@pytest.fixture(autouse=True)
def _fast_sleep(monkeypatch):
    async def instant(_t: float) -> None:
        pass
    monkeypatch.setattr(asyncio, "sleep", instant)


@pytest.fixture(autouse=True)
def _patch_ws_load_state(monkeypatch):
    import server.ws as ws_mod
    monkeypatch.setattr(ws_mod, "load_state", _fake_load_state)


@pytest.fixture
def auth_client(monkeypatch):
    monkeypatch.setenv("RISUS_TOKEN", _TOKEN)
    pool = _FakePool()
    lock_mgr = LockManager()
    conn_mgr = ConnectionManager()
    app = FastAPI()

    @app.websocket("/ws/{name}")
    async def _ep(ws: WebSocket, name: str):
        await conn_mgr.handle(ws, name, pool, lock_mgr)

    with TestClient(app) as c:
        yield c


@pytest.fixture
def no_token_client(monkeypatch):
    monkeypatch.delenv("RISUS_TOKEN", raising=False)
    pool = _FakePool()
    lock_mgr = LockManager()
    conn_mgr = ConnectionManager()
    app = FastAPI()

    @app.websocket("/ws/{name}")
    async def _ep(ws: WebSocket, name: str):
        await conn_mgr.handle(ws, name, pool, lock_mgr)

    with TestClient(app) as c:
        yield c


# --- T010: Server token validation ---

def test_correct_token_accepted(auth_client):
    with auth_client.websocket_connect(f"/ws/Conan?token={_TOKEN}") as ws:
        frame = json.loads(ws.receive_text())
    assert frame["type"] == "state"


def test_wrong_token_rejected(auth_client):
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with auth_client.websocket_connect("/ws/Conan?token=wrong-token-value") as ws:
            ws.receive_text()
    assert exc_info.value.code == 4401


def test_absent_token_rejected(auth_client):
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with auth_client.websocket_connect("/ws/Conan") as ws:
            ws.receive_text()
    assert exc_info.value.code == 4401


def test_risus_token_unset_rejects_all(no_token_client):
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with no_token_client.websocket_connect(f"/ws/Conan?token={_TOKEN}") as ws:
            ws.receive_text()
    assert exc_info.value.code == 4401


# --- T021: Scheme detection tests ---

@pytest.mark.parametrize("server,expected_prefix", [
    ("localhost:8765", "ws://"),
    ("risus.example.com", "wss://"),
    ("[::1]:8765", "ws://"),
])
def test_scheme_detection(server, expected_prefix):
    client = WSClient()
    with patch.object(client, "_run_loop"):
        try:
            client.start(server, "Conan", "tok", timeout=0.001)
        except TimeoutError:
            pass
    assert client._uri.startswith(expected_prefix)


# --- T022: load_battle() URL derivation tests ---

def test_ws_uri_derives_http_base():
    assert _http_base_url("ws://host:8765/ws/Name") == "http://host:8765"


def test_wss_uri_derives_https_base():
    assert _http_base_url("wss://risus.example.com/ws/Name") == "https://risus.example.com"


def test_wss_uri_no_double_replace():
    assert _http_base_url("wss://risus.example.com/ws/Name") == "https://risus.example.com"
