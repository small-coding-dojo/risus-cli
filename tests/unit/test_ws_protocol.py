"""WS protocol integration tests using FastAPI TestClient with mocked DB."""
from __future__ import annotations
import json
import pytest
from fastapi import FastAPI, WebSocket
from fastapi.testclient import TestClient

from server.locks import LockManager
from server.ws import ConnectionManager
from server.rest import router as rest_router


# ---------------------------------------------------------------------------
# Fake pool
# ---------------------------------------------------------------------------

class FakePool:
    def __init__(self):
        self._players: dict[str, dict] = {}
        self._saves: dict[str, list] = {}


async def _fake_load_state(pool):
    return list(pool._players.values())


async def _fake_upsert_player(pool, name, cliche, dice, lost_dice):
    pool._players[name] = {"name": name, "cliche": cliche, "dice": dice, "lost_dice": lost_dice}


async def _fake_delete_player(pool, name):
    pool._players.pop(name, None)


async def _fake_player_exists(pool, name):
    return name in pool._players


async def _fake_save_snapshot(pool, save_name, data):
    pool._saves[save_name] = data


async def _fake_load_snapshot(pool, save_name):
    return pool._saves.get(save_name)


async def _fake_replace_players(pool, players):
    pool._players = {p["name"]: dict(p) for p in players}


async def _fake_list_saves(pool):
    return [{"save_name": k, "saved_at": "2024-01-01T00:00:00"} for k in pool._saves]


@pytest.fixture(autouse=True)
def patch_db(monkeypatch):
    import server.commands as cmd
    import server.db as db
    import server.ws as ws_mod
    import server.rest as rest_mod

    monkeypatch.setattr(cmd, "load_state", _fake_load_state)
    monkeypatch.setattr(cmd, "upsert_player", _fake_upsert_player)
    monkeypatch.setattr(cmd, "delete_player", _fake_delete_player)
    monkeypatch.setattr(cmd, "player_exists", _fake_player_exists)
    monkeypatch.setattr(cmd, "save_snapshot", _fake_save_snapshot)
    monkeypatch.setattr(cmd, "load_snapshot", _fake_load_snapshot)
    monkeypatch.setattr(cmd, "replace_players", _fake_replace_players)
    monkeypatch.setattr(db, "load_state", _fake_load_state)
    monkeypatch.setattr(db, "list_saves", _fake_list_saves)
    monkeypatch.setattr(ws_mod, "load_state", _fake_load_state)
    monkeypatch.setattr(rest_mod, "load_state", _fake_load_state)
    monkeypatch.setattr(rest_mod, "list_saves", _fake_list_saves)


def make_test_app(pool: FakePool, lock_mgr: LockManager, conn_mgr: ConnectionManager) -> FastAPI:
    """Build a FastAPI app with no lifespan (pool pre-injected)."""
    test_app = FastAPI()
    test_app.state.pool = pool
    test_app.state.lock_mgr = lock_mgr
    test_app.state.conn_mgr = conn_mgr
    test_app.include_router(rest_router)

    @test_app.websocket("/ws/{client_name}")
    async def ws_endpoint(ws: WebSocket, client_name: str):
        await conn_mgr.handle(ws, client_name, pool, lock_mgr)

    return test_app


@pytest.fixture
def app_client():
    pool = FakePool()
    lock_mgr = LockManager()
    conn_mgr = ConnectionManager()
    test_app = make_test_app(pool, lock_mgr, conn_mgr)
    with TestClient(test_app, raise_server_exceptions=True) as c:
        yield c, pool, lock_mgr, conn_mgr


def test_get_state_empty(app_client):
    client, pool, _, _ = app_client
    resp = client.get("/state")
    assert resp.status_code == 200
    body = resp.json()
    assert body["type"] == "state"
    assert body["players"] == []


def test_get_saves_empty(app_client):
    client, pool, _, _ = app_client
    resp = client.get("/saves")
    assert resp.status_code == 200
    assert resp.json() == []


def test_ws_connect_sends_state_and_presence(app_client):
    client, pool, _, _ = app_client
    with client.websocket_connect("/ws/TestUser") as ws:
        state_frame = json.loads(ws.receive_text())
        presence_frame = json.loads(ws.receive_text())
    assert state_frame["type"] == "state"
    assert "players" in state_frame
    assert presence_frame["type"] == "presence"
    assert "TestUser" in presence_frame["clients"]


def test_ws_add_player_broadcasts_state(app_client):
    client, pool, _, _ = app_client
    with client.websocket_connect("/ws/Alice") as ws:
        ws.receive_text()  # state
        ws.receive_text()  # presence
        ws.send_text(json.dumps({"type": "add_player", "name": "Goblin", "cliche": "Bandit", "dice": 3}))
        state_frame = json.loads(ws.receive_text())
    assert state_frame["type"] == "state"
    names = {p["name"] for p in state_frame["players"]}
    assert "Goblin" in names


def test_ws_duplicate_player_sends_error(app_client):
    client, pool, _, _ = app_client
    pool._players["Goblin"] = {"name": "Goblin", "cliche": "Bandit", "dice": 3, "lost_dice": 0}
    with client.websocket_connect("/ws/Alice") as ws:
        ws.receive_text()  # state
        ws.receive_text()  # presence
        ws.send_text(json.dumps({"type": "add_player", "name": "Goblin"}))
        frame = json.loads(ws.receive_text())
    assert frame["type"] == "error"
    assert "already exists" in frame["message"]


def test_ws_lock_denied_when_held(app_client):
    client, pool, lock_mgr, _ = app_client
    import asyncio
    asyncio.get_event_loop().run_until_complete(
        lock_mgr.acquire("Goblin", "other-client", "Bob")
    )
    pool._players["Goblin"] = {"name": "Goblin", "cliche": "Bandit", "dice": 3, "lost_dice": 0}

    with client.websocket_connect("/ws/Alice") as ws:
        ws.receive_text()  # state
        ws.receive_text()  # presence
        ws.send_text(json.dumps({"type": "lock", "player_name": "Goblin"}))
        frame = json.loads(ws.receive_text())
    assert frame["type"] == "lock_denied"
    assert frame["player_name"] == "Goblin"
    assert frame["locked_by"] == "Bob"


def test_ws_lock_acquired_broadcasts(app_client):
    client, pool, _, _ = app_client
    pool._players["Goblin"] = {"name": "Goblin", "cliche": "Bandit", "dice": 3, "lost_dice": 0}
    with client.websocket_connect("/ws/Alice") as ws:
        ws.receive_text()  # state
        ws.receive_text()  # presence
        ws.send_text(json.dumps({"type": "lock", "player_name": "Goblin"}))
        frame = json.loads(ws.receive_text())
    assert frame["type"] == "lock_acquired"
    assert frame["player_name"] == "Goblin"
    assert frame["locked_by"] == "Alice"


def test_ws_switch_cliche_rejects_without_lock(app_client):
    client, pool, _, _ = app_client
    pool._players["Goblin"] = {"name": "Goblin", "cliche": "Bandit", "dice": 3, "lost_dice": 0}
    with client.websocket_connect("/ws/Alice") as ws:
        ws.receive_text()  # state
        ws.receive_text()  # presence
        ws.send_text(json.dumps({"type": "switch_cliche", "player_name": "Goblin", "cliche": "Wizard"}))
        frame = json.loads(ws.receive_text())
    assert frame["type"] == "error"
    assert "lock required" in frame["message"]
    # DB unchanged
    assert pool._players["Goblin"]["cliche"] == "Bandit"
