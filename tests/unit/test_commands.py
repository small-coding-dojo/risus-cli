"""Unit tests for server command handlers using fake DB and ConnectionManager."""
from __future__ import annotations
import json
import pytest

from server.locks import LockManager
from server.commands import (
    handle_add_player,
    handle_switch_cliche,
    handle_reduce_dice,
    handle_lock,
    handle_unlock,
    dispatch,
)


# ---------------------------------------------------------------------------
# Fake infrastructure
# ---------------------------------------------------------------------------

class FakePool:
    """In-memory asyncpg pool replacement."""

    def __init__(self, players=None):
        self._players: dict[str, dict] = {}
        for p in (players or []):
            self._players[p["name"]] = dict(p)
        self._saves: dict[str, list] = {}

    def _get(self, name):
        return self._players.get(name)

    def _all(self):
        return list(self._players.values())


class FakeConnMgr:
    def __init__(self):
        self.broadcasts: list[str] = []
        self.sends: dict[str, list[str]] = {}
        # FakePool reference set by tests
        self.pool: FakePool | None = None

    async def broadcast(self, message: str, except_id: str | None = None):
        self.broadcasts.append(message)

    async def send(self, client_id: str, message: str):
        self.sends.setdefault(client_id, []).append(message)

    @property
    def clients(self):
        return {}


# ---------------------------------------------------------------------------
# Patching db helpers
# ---------------------------------------------------------------------------

async def _fake_load_state(pool: FakePool):
    return pool._all()


async def _fake_upsert_player(pool: FakePool, name, cliche, dice, lost_dice):
    pool._players[name] = {"name": name, "cliche": cliche, "dice": dice, "lost_dice": lost_dice}


async def _fake_delete_player(pool: FakePool, name):
    pool._players.pop(name, None)


async def _fake_player_exists(pool: FakePool, name):
    return name in pool._players


async def _fake_save_snapshot(pool, save_name, data):
    pool._saves[save_name] = data


async def _fake_load_snapshot(pool, save_name):
    return pool._saves.get(save_name)


async def _fake_replace_players(pool, players):
    pool._players = {p["name"]: dict(p) for p in players}


@pytest.fixture(autouse=True)
def patch_db(monkeypatch):
    import server.commands as cmd
    monkeypatch.setattr(cmd, "load_state", _fake_load_state)
    monkeypatch.setattr(cmd, "upsert_player", _fake_upsert_player)
    monkeypatch.setattr(cmd, "delete_player", _fake_delete_player)
    monkeypatch.setattr(cmd, "player_exists", _fake_player_exists)
    monkeypatch.setattr(cmd, "save_snapshot", _fake_save_snapshot)
    monkeypatch.setattr(cmd, "load_snapshot", _fake_load_snapshot)
    monkeypatch.setattr(cmd, "replace_players", _fake_replace_players)


# ---------------------------------------------------------------------------
# add_player
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_add_player_broadcasts_state():
    pool = FakePool()
    mgr = LockManager()
    conn = FakeConnMgr()
    await handle_add_player(
        {"type": "add_player", "name": "Alice", "cliche": "Knight", "dice": 3},
        "c1", pool, mgr, conn
    )
    assert "Alice" in pool._players
    assert any("state" in b for b in conn.broadcasts)


@pytest.mark.asyncio
async def test_add_player_duplicate_sends_error():
    pool = FakePool([{"name": "Alice", "cliche": "", "dice": None, "lost_dice": 0}])
    mgr = LockManager()
    conn = FakeConnMgr()
    await handle_add_player(
        {"type": "add_player", "name": "Alice"},
        "c1", pool, mgr, conn
    )
    assert "c1" in conn.sends
    error_frames = [json.loads(s) for s in conn.sends["c1"]]
    assert any(f["type"] == "error" for f in error_frames)
    # DB unchanged: still only one Alice
    assert len(pool._players) == 1


# ---------------------------------------------------------------------------
# switch_cliche — lock enforcement
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_switch_cliche_rejects_without_lock():
    pool = FakePool([{"name": "Goblin", "cliche": "Bandit", "dice": 3, "lost_dice": 0}])
    mgr = LockManager()
    conn = FakeConnMgr()
    await handle_switch_cliche(
        {"type": "switch_cliche", "player_name": "Goblin", "cliche": "Wizard", "dice": 2},
        "c1", pool, mgr, conn
    )
    # DB must be unchanged
    assert pool._players["Goblin"]["cliche"] == "Bandit"
    # Error sent to caller
    assert "c1" in conn.sends
    frames = [json.loads(s) for s in conn.sends["c1"]]
    assert any(f["type"] == "error" and "lock required" in f["message"] for f in frames)


@pytest.mark.asyncio
async def test_switch_cliche_succeeds_with_lock():
    pool = FakePool([{"name": "Goblin", "cliche": "Bandit", "dice": 3, "lost_dice": 0}])
    mgr = LockManager()
    await mgr.acquire("Goblin", "c1", "Alice")
    conn = FakeConnMgr()
    await handle_switch_cliche(
        {"type": "switch_cliche", "player_name": "Goblin", "cliche": "Wizard", "dice": 2},
        "c1", pool, mgr, conn
    )
    assert pool._players["Goblin"]["cliche"] == "Wizard"
    assert any("state" in b for b in conn.broadcasts)


# ---------------------------------------------------------------------------
# reduce_dice — lock enforcement
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_reduce_dice_rejects_without_lock():
    pool = FakePool([{"name": "Goblin", "cliche": "Bandit", "dice": 3, "lost_dice": 0}])
    mgr = LockManager()
    conn = FakeConnMgr()
    await handle_reduce_dice(
        {"type": "reduce_dice", "player_name": "Goblin", "amount": 1},
        "c1", pool, mgr, conn
    )
    # DB unchanged
    assert pool._players["Goblin"]["dice"] == 3
    frames = [json.loads(s) for s in conn.sends.get("c1", [])]
    assert any(f["type"] == "error" and "lock required" in f["message"] for f in frames)


@pytest.mark.asyncio
async def test_reduce_dice_known_pool():
    pool = FakePool([{"name": "Goblin", "cliche": "Bandit", "dice": 3, "lost_dice": 0}])
    mgr = LockManager()
    await mgr.acquire("Goblin", "c1", "Alice")
    conn = FakeConnMgr()
    await handle_reduce_dice(
        {"type": "reduce_dice", "player_name": "Goblin", "amount": 2},
        "c1", pool, mgr, conn
    )
    assert pool._players["Goblin"]["dice"] == 1


@pytest.mark.asyncio
async def test_reduce_dice_to_zero_removes_player():
    pool = FakePool([{"name": "Goblin", "cliche": "Bandit", "dice": 1, "lost_dice": 0}])
    mgr = LockManager()
    await mgr.acquire("Goblin", "c1", "Alice")
    conn = FakeConnMgr()
    await handle_reduce_dice(
        {"type": "reduce_dice", "player_name": "Goblin", "amount": 1},
        "c1", pool, mgr, conn
    )
    assert "Goblin" not in pool._players


@pytest.mark.asyncio
async def test_reduce_dice_unknown_pool():
    pool = FakePool([{"name": "Goblin", "cliche": "Bandit", "dice": None, "lost_dice": 0}])
    mgr = LockManager()
    await mgr.acquire("Goblin", "c1", "Alice")
    conn = FakeConnMgr()
    await handle_reduce_dice(
        {"type": "reduce_dice", "player_name": "Goblin", "amount": 2, "is_dead": False},
        "c1", pool, mgr, conn
    )
    assert pool._players["Goblin"]["lost_dice"] == 2


@pytest.mark.asyncio
async def test_reduce_dice_is_dead_removes():
    pool = FakePool([{"name": "Goblin", "cliche": "Bandit", "dice": None, "lost_dice": 1}])
    mgr = LockManager()
    await mgr.acquire("Goblin", "c1", "Alice")
    conn = FakeConnMgr()
    await handle_reduce_dice(
        {"type": "reduce_dice", "player_name": "Goblin", "amount": 0, "is_dead": True},
        "c1", pool, mgr, conn
    )
    assert "Goblin" not in pool._players


# ---------------------------------------------------------------------------
# lock / unlock
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_lock_broadcasts_lock_acquired():
    pool = FakePool()
    mgr = LockManager()
    conn = FakeConnMgr()
    await handle_lock({"type": "lock", "player_name": "Goblin"}, "c1", "Alice", pool, mgr, conn)
    assert mgr.holder("Goblin") == "c1"
    assert any("lock_acquired" in b for b in conn.broadcasts)


@pytest.mark.asyncio
async def test_lock_denied_sends_to_caller():
    pool = FakePool()
    mgr = LockManager()
    await mgr.acquire("Goblin", "c1", "Alice")
    conn = FakeConnMgr()
    await handle_lock({"type": "lock", "player_name": "Goblin"}, "c2", "Bob", pool, mgr, conn)
    frames = [json.loads(s) for s in conn.sends.get("c2", [])]
    assert any(f["type"] == "lock_denied" for f in frames)


@pytest.mark.asyncio
async def test_unlock_broadcasts_lock_released():
    pool = FakePool()
    mgr = LockManager()
    await mgr.acquire("Goblin", "c1", "Alice")
    conn = FakeConnMgr()
    await handle_unlock({"type": "unlock", "player_name": "Goblin"}, "c1", pool, mgr, conn)
    assert mgr.holder("Goblin") is None
    assert any("lock_released" in b for b in conn.broadcasts)


# ---------------------------------------------------------------------------
# dispatch — unknown type
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dispatch_unknown_type():
    pool = FakePool()
    mgr = LockManager()
    conn = FakeConnMgr()
    await dispatch(json.dumps({"type": "bogus"}), "c1", "Alice", pool, mgr, conn)
    frames = [json.loads(s) for s in conn.sends.get("c1", [])]
    assert any(f["type"] == "error" for f in frames)


@pytest.mark.asyncio
async def test_dispatch_invalid_json():
    pool = FakePool()
    mgr = LockManager()
    conn = FakeConnMgr()
    await dispatch("not-json", "c1", "Alice", pool, mgr, conn)
    frames = [json.loads(s) for s in conn.sends.get("c1", [])]
    assert any(f["type"] == "error" for f in frames)
