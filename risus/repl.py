"""Interactive REPL for the Risus CLI — cmd.Cmd command dispatcher."""

from __future__ import annotations

import argparse
import cmd
import shlex

from risus import display
from risus.models import (
    BattleState,
    DuplicatePlayerError,
)


# ---------------------------------------------------------------------------
# Inline-safe ArgumentParser
# ---------------------------------------------------------------------------

class _InlineArgumentParser(argparse.ArgumentParser):
    """ArgumentParser that raises instead of calling sys.exit on errors.

    This lets the REPL catch errors and print them inline without terminating
    the process.
    """

    def error(self, message: str) -> None:  # type: ignore[override]
        raise argparse.ArgumentError(None, message)

    def exit(self, status: int = 0, message: str | None = None) -> None:  # type: ignore[override]
        if message:
            raise argparse.ArgumentError(None, message.strip())
        if status != 0:
            raise SystemExit(status)


# ---------------------------------------------------------------------------
# REPL
# ---------------------------------------------------------------------------

class RisusRepl(cmd.Cmd):
    """Interactive REPL for managing Risus RPG battle state."""

    prompt = "> "

    def __init__(self, state: BattleState) -> None:
        super().__init__()
        self.state = state

    # ------------------------------------------------------------------
    # Exit commands
    # ------------------------------------------------------------------

    def do_EOF(self, _args: str) -> bool:
        """Exit the interactive session (Ctrl-D)."""
        print()  # newline after ^D
        return True

    def do_exit(self, _args: str) -> bool:
        """Exit the interactive session."""
        return True

    def do_quit(self, _args: str) -> bool:
        """Exit the interactive session."""
        return True

    # ------------------------------------------------------------------
    # Unknown commands
    # ------------------------------------------------------------------

    def default(self, line: str) -> None:
        """Handle unrecognised commands."""
        print("Unknown command. Type 'help' for available commands.")

    # ------------------------------------------------------------------
    # player command
    # ------------------------------------------------------------------

    def do_player(self, args: str) -> None:
        """Manage players in the current battle.

        Usage:
            player add --name <name> [--cliche <cliche>] [--points <n>]

        Sub-commands:
            add   Add a new player to the battle.
        """
        try:
            parts = shlex.split(args)
        except ValueError as exc:
            print(f"Parse error: {exc}")
            return

        if not parts:
            print("Usage: player add --name <name> [--cliche <cliche>] [--points <n>]")
            return

        sub = parts[0]
        if sub == "add":
            self._player_add(parts[1:])
        else:
            print(f"Unknown sub-command '{sub}'. Try: player add")

    def _player_add(self, parts: list[str]) -> None:
        """Parse and execute the 'player add' sub-command."""
        parser = _InlineArgumentParser(prog="player add", add_help=False)
        parser.add_argument("--name", required=True)
        parser.add_argument("--cliche", default="")
        parser.add_argument("--points", type=int, default=0)

        try:
            ns = parser.parse_args(parts)
        except (argparse.ArgumentError, SystemExit) as exc:
            print(f"Error: {exc}")
            return

        try:
            self.state.add_player(ns.name, cliche=ns.cliche, dice=ns.points)
        except DuplicatePlayerError as exc:
            print(str(exc))
            return

        print(display.render(self.state))
