"""Unit tests for risus.persistence — save/load round trips."""

from __future__ import annotations

import pytest

from risus.models import BattleState, SaveNotFoundError
from risus import persistence


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _isolated_save_dir(tmp_path, monkeypatch):
    """Monkeypatch _save_dir to use a temp directory."""
    save_dir = tmp_path / "saves"
    save_dir.mkdir()
    monkeypatch.setattr(persistence, "_save_dir", lambda: save_dir)
    return save_dir


def _make_state(*players) -> BattleState:
    """Build a BattleState from (name, cliche, dice) tuples."""
    state = BattleState()
    for name, cliche, dice in players:
        state.add_player(name, cliche=cliche, dice=dice)
    return state


# ---------------------------------------------------------------------------
# T021: persistence tests
# ---------------------------------------------------------------------------

class TestPersistence:
    def test_save_round_trip_returns_equivalent_state(self, tmp_path, monkeypatch):
        _isolated_save_dir(tmp_path, monkeypatch)
        state = _make_state(
            ("Hanne", "Throw stones", 4),
            ("Zerox", "Firearms", 3),
        )
        persistence.save(state, "TestSlot")
        loaded = persistence.load("TestSlot")

        assert loaded.session_name == "TestSlot"
        assert "Hanne" in loaded.players
        assert "Zerox" in loaded.players
        assert loaded.players["Hanne"].cliche_name == "Throw stones"
        assert loaded.players["Hanne"].dice == 4
        assert loaded.players["Zerox"].cliche_name == "Firearms"
        assert loaded.players["Zerox"].dice == 3

    def test_load_missing_save_raises_save_not_found_error(self, tmp_path, monkeypatch):
        _isolated_save_dir(tmp_path, monkeypatch)
        with pytest.raises(SaveNotFoundError):
            persistence.load("DoesNotExist")

    def test_special_chars_in_name_are_slugified(self, tmp_path, monkeypatch):
        save_dir = _isolated_save_dir(tmp_path, monkeypatch)
        state = _make_state(("Hanne", "Magic", 4))
        persistence.save(state, "Builders' Shack")
        # Verify the file uses the slugified name
        files = list(save_dir.iterdir())
        assert len(files) == 1
        assert files[0].name == "builders__shack.json"
        # Load should still work with original name
        loaded = persistence.load("Builders' Shack")
        assert loaded.session_name == "Builders' Shack"
        assert "Hanne" in loaded.players

    def test_overwrite_same_name_works(self, tmp_path, monkeypatch):
        _isolated_save_dir(tmp_path, monkeypatch)
        state1 = _make_state(("Hanne", "Throw stones", 4))
        persistence.save(state1, "Slot")

        state2 = _make_state(("Zerox", "Firearms", 3))
        persistence.save(state2, "Slot")  # overwrite

        loaded = persistence.load("Slot")
        assert "Zerox" in loaded.players
        assert "Hanne" not in loaded.players

    def test_loaded_state_has_session_name_set(self, tmp_path, monkeypatch):
        _isolated_save_dir(tmp_path, monkeypatch)
        state = _make_state(("Hanne", "Magic", 2))
        persistence.save(state, "MySession")
        loaded = persistence.load("MySession")
        assert loaded.session_name == "MySession"

    def test_save_preserves_player_with_zero_dice(self, tmp_path, monkeypatch):
        """Players with dice=0 are saved and restored (even if not shown in display)."""
        _isolated_save_dir(tmp_path, monkeypatch)
        state = _make_state(("Ghost", "Haunting", 0))
        persistence.save(state, "GhostSlot")
        loaded = persistence.load("GhostSlot")
        assert "Ghost" in loaded.players
        assert loaded.players["Ghost"].dice == 0

    def test_save_empty_state(self, tmp_path, monkeypatch):
        _isolated_save_dir(tmp_path, monkeypatch)
        state = BattleState()
        persistence.save(state, "Empty")
        loaded = persistence.load("Empty")
        assert len(loaded.players) == 0
        assert loaded.session_name == "Empty"

    def test_slug_function_lowercases_and_replaces_special_chars(self):
        assert persistence._slug("Hello World!") == "hello_world_"
        assert persistence._slug("Builders' Shack") == "builders__shack"
        assert persistence._slug("test-123_ok") == "test-123_ok"
        assert persistence._slug("UPPER") == "upper"
