"""Unit tests for risus.models — Player, BattleState, and domain errors."""

import pytest

from risus.models import (
    BattleState,
    DuplicatePlayerError,
    Player,
    PlayerNotFoundError,
)


# ---------------------------------------------------------------------------
# Player dataclass
# ---------------------------------------------------------------------------

class TestPlayer:
    def test_defaults(self):
        p = Player(name="Hanne")
        assert p.name == "Hanne"
        assert p.cliche_name == ""
        assert p.dice == 0

    def test_custom_values(self):
        p = Player(name="Zerox", cliche_name="Firearms", dice=3)
        assert p.name == "Zerox"
        assert p.cliche_name == "Firearms"
        assert p.dice == 3


# ---------------------------------------------------------------------------
# BattleState.add_player
# ---------------------------------------------------------------------------

class TestAddPlayer:
    def test_add_player_returns_player(self):
        state = BattleState()
        player = state.add_player("Hanne")
        assert isinstance(player, Player)
        assert player.name == "Hanne"

    def test_add_player_with_cliche_and_dice(self):
        state = BattleState()
        player = state.add_player("Zerox", cliche="Firearms", dice=3)
        assert player.cliche_name == "Firearms"
        assert player.dice == 3

    def test_add_duplicate_player_raises(self):
        state = BattleState()
        state.add_player("Hanne")
        with pytest.raises(DuplicatePlayerError, match="Hanne"):
            state.add_player("Hanne")

    def test_add_multiple_players(self):
        state = BattleState()
        state.add_player("Hanne")
        state.add_player("Zerox")
        assert len(state.players) == 2


# ---------------------------------------------------------------------------
# BattleState.switch_cliche
# ---------------------------------------------------------------------------

class TestSwitchCliche:
    def test_switch_updates_cliche_and_dice(self):
        state = BattleState()
        state.add_player("Hanne", cliche="Throw stones", dice=4)
        player = state.switch_cliche("Hanne", "Magic spell", 2)
        assert player.cliche_name == "Magic spell"
        assert player.dice == 2

    def test_switch_unknown_player_raises(self):
        state = BattleState()
        with pytest.raises(PlayerNotFoundError, match="Ghost"):
            state.switch_cliche("Ghost", "Something", 3)

    def test_switch_zero_points_accepted(self):
        state = BattleState()
        state.add_player("Hanne", cliche="Throw stones", dice=4)
        player = state.switch_cliche("Hanne", "Empty", 0)
        assert player.dice == 0


# ---------------------------------------------------------------------------
# BattleState.reduce_dice
# ---------------------------------------------------------------------------

class TestReduceDice:
    def test_normal_reduction(self):
        state = BattleState()
        state.add_player("Hanne", cliche="Throw stones", dice=4)
        player = state.reduce_dice("Hanne", 2)
        assert player.dice == 2

    def test_clamp_at_zero(self):
        state = BattleState()
        state.add_player("Hanne", cliche="Throw stones", dice=2)
        player = state.reduce_dice("Hanne", 5)
        assert player.dice == 0

    def test_player_at_zero_removed_from_active(self):
        state = BattleState()
        state.add_player("Hanne", cliche="Throw stones", dice=2)
        state.reduce_dice("Hanne", 2)
        assert state.active_players() == []

    def test_player_object_retained_in_dict_after_elimination(self):
        state = BattleState()
        state.add_player("Hanne", cliche="Throw stones", dice=2)
        state.reduce_dice("Hanne", 2)
        # Object must still be in players dict even at dice=0
        assert "Hanne" in state.players
        assert state.players["Hanne"].dice == 0

    def test_reduce_unknown_player_raises(self):
        state = BattleState()
        with pytest.raises(PlayerNotFoundError, match="Ghost"):
            state.reduce_dice("Ghost", 1)


# ---------------------------------------------------------------------------
# BattleState.active_players — insertion order
# ---------------------------------------------------------------------------

class TestActivePlayers:
    def test_empty_state(self):
        state = BattleState()
        assert state.active_players() == []

    def test_insertion_order_preserved(self):
        state = BattleState()
        state.add_player("Hanne", dice=4)
        state.add_player("Zerox", dice=3)
        state.add_player("Brom", dice=2)
        names = [p.name for p in state.active_players()]
        assert names == ["Hanne", "Zerox", "Brom"]

    def test_eliminated_players_excluded(self):
        state = BattleState()
        state.add_player("Hanne", dice=4)
        state.add_player("Zerox", dice=3)
        state.reduce_dice("Hanne", 4)
        names = [p.name for p in state.active_players()]
        assert names == ["Zerox"]

    def test_players_with_zero_dice_on_add_not_in_active(self):
        state = BattleState()
        state.add_player("Hanne")  # dice defaults to 0
        assert state.active_players() == []
