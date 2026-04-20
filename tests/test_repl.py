"""Unit tests for risus.repl — RisusRepl command handlers."""

from __future__ import annotations

import io
import subprocess
import sys
import tempfile

import pytest

from risus.models import BattleState, Player
from risus.repl import RisusRepl
from risus import persistence


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

# ---------------------------------------------------------------------------
# do_cliche switch — T015
# ---------------------------------------------------------------------------

class TestDoCliqueSwitch:
    def test_switch_cliche_updates_state(self):
        state = BattleState()
        state.add_player("Hanne", cliche="Old cliche", dice=2)
        repl = make_repl(state)
        output = _run_command(repl, "do_cliche", 'switch --name "Magic spell" --points 4 --target "Hanne"')
        assert "Hanne" in output
        assert "4 dice" in output
        assert "Magic spell" in output
        assert repl.state.players["Hanne"].cliche_name == "Magic spell"
        assert repl.state.players["Hanne"].dice == 4

    def test_switch_cliche_reprints_state(self):
        state = BattleState()
        state.add_player("Zerox", cliche="Firearms", dice=3)
        repl = make_repl(state)
        output = _run_command(repl, "do_cliche", 'switch --name "Swords" --points 2 --target "Zerox"')
        assert "Battle latest state" in output

    def test_switch_unknown_player_shows_error_without_exception(self):
        repl = make_repl()
        try:
            output = _run_command(repl, "do_cliche", 'switch --name "Magic" --points 3 --target "NoOne"')
        except Exception as exc:
            pytest.fail(f"switch on unknown player raised: {exc}")
        assert "not found" in output.lower() or "error" in output.lower()

    def test_switch_unknown_player_does_not_raise(self):
        repl = make_repl()
        # Should not raise PlayerNotFoundError
        output = _run_command(repl, "do_cliche", 'switch --name "Magic" --points 3 --target "NoOne"')
        assert "Battle latest state" not in output  # no success reprint

    def test_switch_points_zero_accepted(self):
        state = BattleState()
        state.add_player("Hanne", cliche="Old", dice=4)
        repl = make_repl(state)
        # --points 0 should be accepted without error
        try:
            output = _run_command(repl, "do_cliche", 'switch --name "Zeroed" --points 0 --target "Hanne"')
        except Exception as exc:
            pytest.fail(f"switch with --points 0 raised: {exc}")
        # player dice=0 → not shown in display
        assert repl.state.players["Hanne"].dice == 0

    def test_switch_missing_name_shows_inline_error(self):
        repl = make_repl()
        output = _run_command(repl, "do_cliche", 'switch --points 3 --target "Hanne"')
        assert "error" in output.lower() or "required" in output.lower()

    def test_switch_missing_name_does_not_exit(self):
        repl = make_repl()
        try:
            _run_command(repl, "do_cliche", 'switch --points 3 --target "Hanne"')
        except SystemExit:
            pytest.fail("switch with missing --name called sys.exit")


# ---------------------------------------------------------------------------
# do_cliche reduce-by — T017
# ---------------------------------------------------------------------------

class TestDoCliqueReduceBy:
    def test_reduce_normal(self):
        state = BattleState()
        state.add_player("Hanne", cliche="Magic spell", dice=4)
        repl = make_repl(state)
        output = _run_command(repl, "do_cliche", 'reduce-by --amount 2 --target "Hanne"')
        assert "Hanne" in output
        assert "2 dice" in output
        assert repl.state.players["Hanne"].dice == 2

    def test_reduce_clamps_at_zero(self):
        state = BattleState()
        state.add_player("Hanne", cliche="Magic spell", dice=3)
        repl = make_repl(state)
        _run_command(repl, "do_cliche", 'reduce-by --amount 10 --target "Hanne"')
        assert repl.state.players["Hanne"].dice == 0

    def test_reduce_to_zero_removes_from_display(self):
        state = BattleState()
        state.add_player("Hanne", cliche="Magic spell", dice=3)
        repl = make_repl(state)
        output = _run_command(repl, "do_cliche", 'reduce-by --amount 10 --target "Hanne"')
        # Hanne at 0 dice → not shown in active list
        assert "Hanne" not in output

    def test_reduce_unknown_player_shows_error_without_exception(self):
        repl = make_repl()
        try:
            output = _run_command(repl, "do_cliche", 'reduce-by --amount 2 --target "NoOne"')
        except Exception as exc:
            pytest.fail(f"reduce-by on unknown player raised: {exc}")
        assert "not found" in output.lower() or "error" in output.lower()

    def test_reduce_unknown_player_does_not_raise(self):
        repl = make_repl()
        output = _run_command(repl, "do_cliche", 'reduce-by --amount 2 --target "Ghost"')
        assert "Battle latest state" not in output  # no success reprint

    def test_reduce_missing_amount_shows_inline_error(self):
        repl = make_repl()
        output = _run_command(repl, "do_cliche", 'reduce-by --target "Hanne"')
        assert "error" in output.lower() or "required" in output.lower()

    def test_reduce_missing_amount_does_not_exit(self):
        repl = make_repl()
        try:
            _run_command(repl, "do_cliche", 'reduce-by --target "Hanne"')
        except SystemExit:
            pytest.fail("reduce-by with missing --amount called sys.exit")


# ---------------------------------------------------------------------------
# Integration test — T022
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_save_and_reload_via_subprocess(self, tmp_path, monkeypatch):
        """Full round-trip: add players → save → quit → reload with --load."""
        import os
        # Use tmp_path as home dir to isolate saves
        fake_home = tmp_path / "home"
        fake_home.mkdir()

        env = os.environ.copy()
        env["HOME"] = str(fake_home)

        save_name = "TestSession"

        # First session: add players and save
        commands = (
            'player add --name "Hanne" --cliche "Throw stones" --points 4\n'
            'player add --name "Zerox" --cliche "Firearms" --points 3\n'
            f'save --name "{save_name}"\n'
            "quit\n"
        )
        result1 = subprocess.run(
            [sys.executable, "-m", "risus"],
            input=commands,
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
        )
        assert result1.returncode == 0, f"First session failed:\n{result1.stderr}"
        assert "Hanne" in result1.stdout
        assert "Zerox" in result1.stdout
        assert save_name in result1.stdout

        # Second session: reload and verify
        result2 = subprocess.run(
            [sys.executable, "-m", "risus", "--load", save_name],
            input="quit\n",
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
        )
        assert result2.returncode == 0, f"Reload session failed:\n{result2.stderr}"
        assert "Hanne" in result2.stdout
        assert "Zerox" in result2.stdout
        assert save_name in result2.stdout

    def test_load_missing_save_exits_with_code_1(self, tmp_path):
        import os
        env = os.environ.copy()
        env["HOME"] = str(tmp_path / "home2")
        result = subprocess.run(
            [sys.executable, "-m", "risus", "--load", "NonExistentSave"],
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
        )
        assert result.returncode == 1
        assert "not found" in result.stderr.lower()


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


# ---------------------------------------------------------------------------
# do_load — in-REPL load command
# ---------------------------------------------------------------------------

class TestDoLoad:
    def test_load_restores_state_and_sets_session_name(self, tmp_path, monkeypatch):
        save_dir = tmp_path / "saves"
        save_dir.mkdir()
        monkeypatch.setattr(persistence, "_save_dir", lambda: save_dir)

        state = BattleState()
        state.add_player("Hanne", cliche="Throw stones", dice=4)
        persistence.save(state, "MySession")

        repl = make_repl()
        output = _run_command(repl, "do_load", '--name "MySession"')
        assert "Hanne" in output
        assert "MySession" in output
        assert repl.state.session_name == "MySession"
        assert "Hanne" in repl.state.players

    def test_load_missing_save_shows_inline_error(self, tmp_path, monkeypatch):
        save_dir = tmp_path / "saves"
        save_dir.mkdir()
        monkeypatch.setattr(persistence, "_save_dir", lambda: save_dir)

        repl = make_repl()
        output = _run_command(repl, "do_load", '--name "NoSuchSave"')
        assert "failed" in output.lower() or "not found" in output.lower()

    def test_load_missing_save_does_not_raise(self, tmp_path, monkeypatch):
        save_dir = tmp_path / "saves"
        save_dir.mkdir()
        monkeypatch.setattr(persistence, "_save_dir", lambda: save_dir)

        repl = make_repl()
        try:
            _run_command(repl, "do_load", '--name "NoSuchSave"')
        except Exception as exc:
            pytest.fail(f"do_load on missing save raised: {exc}")

    def test_load_missing_name_shows_inline_error(self, tmp_path, monkeypatch):
        repl = make_repl()
        output = _run_command(repl, "do_load", "")
        assert "error" in output.lower() or "required" in output.lower()

    def test_load_missing_name_does_not_exit(self):
        repl = make_repl()
        try:
            _run_command(repl, "do_load", "")
        except SystemExit:
            pytest.fail("do_load with no --name called sys.exit")
