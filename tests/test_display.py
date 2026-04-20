"""Unit tests for risus.display.render."""

import pytest

from risus.display import render
from risus.models import BattleState


class TestRender:
    def test_empty_state_no_session(self):
        state = BattleState()
        output = render(state)
        lines = output.splitlines()
        assert lines[0] == "Battle latest state"
        assert lines[1] == "=" * len("Battle latest state")
        assert len(lines) == 2

    def test_empty_state_with_session(self):
        state = BattleState(session_name="My Session")
        output = render(state)
        lines = output.splitlines()
        assert lines[0] == "Battle latest state (My Session)"
        assert lines[1] == "=" * len("Battle latest state (My Session)")

    def test_single_player(self):
        state = BattleState()
        state.add_player("Hanne", cliche="Throw stones", dice=4)
        output = render(state)
        lines = output.splitlines()
        assert lines[0] == "Battle latest state"
        assert lines[1] == "=" * len("Battle latest state")
        assert lines[2] == "Hanne:     4 dice (Throw stones)"

    def test_multiple_players(self):
        state = BattleState()
        state.add_player("Hanne", cliche="Throw stones", dice=4)
        state.add_player("Zerox", cliche="Firearms", dice=3)
        output = render(state)
        lines = output.splitlines()
        assert "Hanne:     4 dice (Throw stones)" in lines
        assert "Zerox:     3 dice (Firearms)" in lines

    def test_with_session_name(self):
        state = BattleState(session_name="Builders' Shack")
        state.add_player("Hanne", cliche="Throw stones", dice=4)
        state.add_player("Zerox", cliche="Firearms", dice=3)
        output = render(state)
        lines = output.splitlines()
        assert lines[0] == "Battle latest state (Builders' Shack)"
        assert lines[1] == "=" * len("Battle latest state (Builders' Shack)")
        assert lines[2] == "Hanne:     4 dice (Throw stones)"
        assert lines[3] == "Zerox:     3 dice (Firearms)"

    def test_separator_length_matches_header_no_session(self):
        state = BattleState()
        output = render(state)
        lines = output.splitlines()
        assert len(lines[1]) == len(lines[0])

    def test_separator_length_matches_header_with_session(self):
        state = BattleState(session_name="Epic Battle 2026")
        output = render(state)
        lines = output.splitlines()
        assert len(lines[1]) == len(lines[0])

    def test_eliminated_players_not_shown(self):
        state = BattleState()
        state.add_player("Hanne", cliche="Throw stones", dice=2)
        state.reduce_dice("Hanne", 2)  # eliminate
        state.add_player("Zerox", cliche="Firearms", dice=3)
        output = render(state)
        assert "Hanne" not in output
        assert "Zerox" in output
