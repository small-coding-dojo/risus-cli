"""Unit tests for risus.repl — RisusRepl command handlers."""

from __future__ import annotations

import io
import sys

import pytest

from risus.models import BattleState
from risus.repl import RisusRepl


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_command(repl: RisusRepl, method: str, args: str) -> str:
    """Call a do_* method and capture printed output."""
    buf = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buf
    try:
        getattr(repl, method)(args)
    finally:
        sys.stdout = old_stdout
    return buf.getvalue()


def make_repl(state: BattleState | None = None) -> RisusRepl:
    if state is None:
        state = BattleState()
    return RisusRepl(state)


# ---------------------------------------------------------------------------
# do_player add — T013
# ---------------------------------------------------------------------------

class TestDoPlayerAdd:
    def test_add_new_player_minimal(self):
        repl = make_repl()
        output = _run_command(repl, "do_player", 'add --name "Hanne"')
        assert "Battle latest state" in output
        # player has dice=0, so not shown in active list — just verify no crash

    def test_add_player_with_cliche_and_points(self):
        repl = make_repl()
        output = _run_command(repl, "do_player", 'add --name "Zerox" --cliche "Firearms" --points 3')
        assert "Zerox" in output
        assert "3 dice" in output
        assert "Firearms" in output

    def test_add_duplicate_player_shows_error_without_exception(self):
        repl = make_repl()
        _run_command(repl, "do_player", 'add --name "Hanne" --points 3')
        output = _run_command(repl, "do_player", 'add --name "Hanne"')
        assert "already exists" in output
        # State should be unchanged — still only 1 player
        assert len(repl.state.players) == 1

    def test_add_duplicate_does_not_raise_exception(self):
        repl = make_repl()
        _run_command(repl, "do_player", 'add --name "Hanne" --points 3')
        # Should not raise — must be caught inline
        try:
            _run_command(repl, "do_player", 'add --name "Hanne"')
        except Exception as exc:
            pytest.fail(f"add duplicate raised an exception: {exc}")

    def test_add_player_with_no_name_shows_argparse_error_inline(self):
        repl = make_repl()
        output = _run_command(repl, "do_player", "add --points 3")
        assert "Error" in output or "error" in output.lower() or "required" in output.lower()

    def test_add_player_with_no_name_does_not_exit(self):
        repl = make_repl()
        try:
            _run_command(repl, "do_player", "add --points 3")
        except SystemExit:
            pytest.fail("do_player with missing --name called sys.exit")

    def test_add_player_updates_state(self):
        repl = make_repl()
        _run_command(repl, "do_player", 'add --name "Hanne" --cliche "Stones" --points 4')
        assert "Hanne" in repl.state.players
        assert repl.state.players["Hanne"].dice == 4

    def test_add_multiple_players_both_appear_in_output(self):
        repl = make_repl()
        _run_command(repl, "do_player", 'add --name "Hanne" --cliche "Throw stones" --points 4')
        output = _run_command(repl, "do_player", 'add --name "Zerox" --cliche "Firearms" --points 3')
        assert "Hanne" in output
        assert "Zerox" in output

    def test_unknown_subcommand_shows_error(self):
        repl = make_repl()
        output = _run_command(repl, "do_player", "remove --name Hanne")
        assert "Unknown" in output or "unknown" in output.lower()

    def test_empty_args_shows_usage(self):
        repl = make_repl()
        output = _run_command(repl, "do_player", "")
        # Should print some usage info, not crash
        assert "player add" in output or "Usage" in output


# ---------------------------------------------------------------------------
# REPL skeleton — default / exit
# ---------------------------------------------------------------------------

class TestReplSkeleton:
    def test_default_unknown_command(self):
        repl = make_repl()
        output = _run_command(repl, "default", "foo bar")
        assert "Unknown command" in output
        assert "help" in output

    def test_do_exit_returns_true(self):
        repl = make_repl()
        result = repl.do_exit("")
        assert result is True

    def test_do_quit_returns_true(self):
        repl = make_repl()
        result = repl.do_quit("")
        assert result is True

    def test_do_eof_returns_true(self):
        repl = make_repl()
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            result = repl.do_EOF("")
        finally:
            sys.stdout = old_stdout
        assert result is True
