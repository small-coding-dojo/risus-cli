"""Tests for ClientState.update_event dirty-flag and _input_with_refresh behavior."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from client.state import ClientState


# ---------------------------------------------------------------------------
# T003 — state frame sets update_event
# ---------------------------------------------------------------------------

def test_apply_state_sets_update_event():
    cs = ClientState()
    assert not cs.update_event.is_set()
    cs.apply({"type": "state", "players": [
        {"name": "Alice", "cliche": "Knight", "dice": 3, "lost_dice": 0},
    ]})
    assert cs.update_event.is_set()


# ---------------------------------------------------------------------------
# T004 — presence frame sets update_event
# ---------------------------------------------------------------------------

def test_apply_presence_sets_update_event():
    cs = ClientState()
    cs.apply({"type": "presence", "clients": ["Alice", "Bob"]})
    assert cs.update_event.is_set()


# ---------------------------------------------------------------------------
# T005 — fresh ClientState has event not set
# ---------------------------------------------------------------------------

def test_update_event_starts_clear():
    cs = ClientState()
    assert not cs.update_event.is_set()


# ---------------------------------------------------------------------------
# T006 — rapid successive apply calls; no updates dropped (SC-003)
# ---------------------------------------------------------------------------

def test_rapid_apply_no_updates_dropped():
    cs = ClientState()
    frames = [
        {"type": "state", "players": [{"name": f"P{i}", "cliche": "x", "dice": i, "lost_dice": 0}]}
        for i in range(10)
    ]
    for f in frames:
        cs.apply(f)
    # All apply() calls must have executed; final state reflects last frame
    players = cs.snapshot_players()
    assert len(players) == 1
    assert players[0].name == "P9"
    assert players[0].dice == 9
    assert cs.update_event.is_set()


# ---------------------------------------------------------------------------
# T007 — _input_with_refresh redraws on timeout then returns input
# ---------------------------------------------------------------------------

def test_input_with_refresh_redraws_on_timeout():
    """select.select times out once (state dirty), then stdin becomes ready."""
    import sys

    # websockets is a runtime dep not needed in unit tests; stub it out
    # so risus.py can be imported without the full async stack installed.
    ws_stub = MagicMock()
    with patch.dict(sys.modules, {"websockets": ws_stub,
                                   "websockets.exceptions": ws_stub,
                                   "client.ws_client": MagicMock()}):
        import importlib
        import risus as _risus_mod
        importlib.reload(_risus_mod)  # ensure it picks up the stubbed modules

    cs = ClientState()
    cs.apply({"type": "state", "players": []})  # sets update_event
    assert cs.update_event.is_set()

    mock_ws_client = MagicMock()
    mock_ws_client.state = cs

    select_results = [
        ([], [], []),           # timeout → triggers redraw
        ([sys.stdin], [], []),  # stdin ready → read line
    ]

    with patch.object(_risus_mod, "_client", mock_ws_client), \
         patch.object(_risus_mod, "show_state") as mock_show, \
         patch.object(_risus_mod, "select") as mock_select_mod, \
         patch("sys.stdin") as mock_stdin:
        mock_select_mod.select.side_effect = select_results
        mock_stdin.readline.return_value = "1\n"

        result = _risus_mod._input_with_refresh("> ")

    assert result == "1"
    mock_show.assert_called_once()
    assert not cs.update_event.is_set()  # cleared after redraw


# ---------------------------------------------------------------------------
# T007b — _input_with_refresh calls redraw kwarg, not show_state, when provided
# ---------------------------------------------------------------------------

def test_input_with_refresh_calls_redraw_kwarg():
    """When redraw callable passed, it is called; show_state is NOT called."""
    import sys

    ws_stub = MagicMock()
    with patch.dict(sys.modules, {"websockets": ws_stub,
                                   "websockets.exceptions": ws_stub,
                                   "client.ws_client": MagicMock()}):
        import importlib
        import risus as _risus_mod
        importlib.reload(_risus_mod)

    cs = ClientState()
    cs.apply({"type": "presence", "clients": ["TestUser", "OtherUser"]})  # sets update_event
    assert cs.update_event.is_set()

    mock_ws_client = MagicMock()
    mock_ws_client.state = cs

    select_results = [
        ([], [], []),           # timeout → triggers redraw
        ([sys.stdin], [], []),  # stdin ready → read line
    ]

    mock_redraw = MagicMock()

    with patch.object(_risus_mod, "_client", mock_ws_client), \
         patch.object(_risus_mod, "show_state") as mock_show, \
         patch.object(_risus_mod, "select") as mock_select_mod, \
         patch("sys.stdin") as mock_stdin:
        mock_select_mod.select.side_effect = select_results
        mock_stdin.readline.return_value = "2\n"

        result = _risus_mod._input_with_refresh("> ", redraw=mock_redraw)

    assert result == "2"
    mock_redraw.assert_called_once()
    mock_show.assert_not_called()
    assert not cs.update_event.is_set()


# ---------------------------------------------------------------------------
# T011 — lock_acquired frame sets update_event
# ---------------------------------------------------------------------------

def test_apply_lock_acquired_sets_update_event():
    cs = ClientState()
    cs.apply({"type": "lock_acquired", "player_name": "Alice", "locked_by": "Bob"})
    assert cs.update_event.is_set()


# ---------------------------------------------------------------------------
# T012 — lock_released frame sets update_event
# ---------------------------------------------------------------------------

def test_apply_lock_released_sets_update_event():
    cs = ClientState()
    # Seed a lock first
    cs.apply({"type": "lock_acquired", "player_name": "Alice", "locked_by": "Bob"})
    cs.update_event.clear()
    cs.apply({"type": "lock_released", "player_name": "Alice"})
    assert cs.update_event.is_set()


# ---------------------------------------------------------------------------
# T014 — update_event is clear after explicit clear()
# ---------------------------------------------------------------------------

def test_update_event_cleared_after_check():
    cs = ClientState()
    cs.apply({"type": "state", "players": []})
    assert cs.update_event.is_set()
    cs.update_event.clear()
    assert not cs.update_event.is_set()
