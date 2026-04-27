import pytest
from client.state import ClientState


def test_state_frame_updates_players():
    cs = ClientState()
    cs.apply({"type": "state", "players": [
        {"name": "Alice", "cliche": "Knight", "dice": 3, "lost_dice": 0},
    ]})
    players = cs.snapshot_players()
    assert len(players) == 1
    assert players[0].name == "Alice"
    assert players[0].dice == 3


def test_state_frame_replaces_players():
    cs = ClientState()
    cs.apply({"type": "state", "players": [{"name": "Alice", "cliche": "Knight", "dice": 3, "lost_dice": 0}]})
    cs.apply({"type": "state", "players": [{"name": "Bob", "cliche": "Wizard", "dice": None, "lost_dice": 2}]})
    players = cs.snapshot_players()
    assert len(players) == 1
    assert players[0].name == "Bob"
    assert players[0].dice is None
    assert players[0].lost_dice == 2


def test_presence_frame():
    cs = ClientState()
    cs.apply({"type": "presence", "clients": ["Alice", "Bob"]})
    assert cs.snapshot_presence() == ["Alice", "Bob"]


def test_lock_acquired_frame():
    cs = ClientState()
    cs.apply({"type": "lock_acquired", "player_name": "Goblin", "locked_by": "Alice"})
    locks = cs.snapshot_locks()
    assert locks == {"Goblin": "Alice"}


def test_lock_released_frame():
    cs = ClientState()
    cs.apply({"type": "lock_acquired", "player_name": "Goblin", "locked_by": "Alice"})
    cs.apply({"type": "lock_released", "player_name": "Goblin"})
    assert cs.snapshot_locks() == {}


def test_unknown_frame_ignored():
    cs = ClientState()
    cs.apply({"type": "unknown_frame", "data": 123})
    assert cs.snapshot_players() == []
