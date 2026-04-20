"""Interactive REPL for the Risus CLI — cmd.Cmd command dispatcher."""

from __future__ import annotations

import argparse
import cmd
import shlex

from risus import display
from risus import persistence
from risus.models import (
    BattleState,
    DuplicatePlayerError,
    PlayerNotFoundError,
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

    # ------------------------------------------------------------------
    # cliche command
    # ------------------------------------------------------------------

    def do_cliche(self, args: str) -> None:
        """Manage player clichés in the current battle.

        Usage:
            cliche switch --name <cliche-name> --points <n> --target <player>
            cliche reduce-by --amount <n> --target <player>

        Sub-commands:
            switch      Replace a player's active cliché and dice pool.
            reduce-by   Reduce a player's dice pool (clamped at 0).
        """
        try:
            parts = shlex.split(args)
        except ValueError as exc:
            print(f"Parse error: {exc}")
            return

        if not parts:
            print(
                "Usage: cliche switch --name <cliche-name> --points <n> --target <player>\n"
                "       cliche reduce-by --amount <n> --target <player>"
            )
            return

        sub = parts[0]
        if sub == "switch":
            self._cliche_switch(parts[1:])
        elif sub == "reduce-by":
            self._cliche_reduce_by(parts[1:])
        else:
            print(f"Unknown sub-command '{sub}'. Try: cliche switch, cliche reduce-by")

    def _cliche_switch(self, parts: list[str]) -> None:
        """Parse and execute the 'cliche switch' sub-command."""
        parser = _InlineArgumentParser(prog="cliche switch", add_help=False)
        parser.add_argument("--name", required=True)
        parser.add_argument("--points", type=int, required=True)
        parser.add_argument("--target", required=True)

        try:
            ns = parser.parse_args(parts)
        except (argparse.ArgumentError, SystemExit) as exc:
            print(f"Error: {exc}")
            return

        try:
            self.state.switch_cliche(ns.target, cliche_name=ns.name, dice=ns.points)
        except PlayerNotFoundError as exc:
            print(str(exc))
            return

        print(display.render(self.state))

    def _cliche_reduce_by(self, parts: list[str]) -> None:
        """Parse and execute the 'cliche reduce-by' sub-command."""
        parser = _InlineArgumentParser(prog="cliche reduce-by", add_help=False)
        parser.add_argument("--amount", type=int, required=True)
        parser.add_argument("--target", required=True)

        try:
            ns = parser.parse_args(parts)
        except (argparse.ArgumentError, SystemExit) as exc:
            print(f"Error: {exc}")
            return

        try:
            self.state.reduce_dice(ns.target, ns.amount)
        except PlayerNotFoundError as exc:
            print(str(exc))
            return

        print(display.render(self.state))

    # ------------------------------------------------------------------
    # save command
    # ------------------------------------------------------------------

    def do_save(self, args: str) -> None:
        """Persist the current battle state to a named save slot.

        Usage:
            save --name <save-name>

        Flags:
            --name   Save slot name. Overwrites an existing slot with the same name.
        """
        try:
            parts = shlex.split(args)
        except ValueError as exc:
            print(f"Parse error: {exc}")
            return

        parser = _InlineArgumentParser(prog="save", add_help=False)
        parser.add_argument("--name", required=True)

        try:
            ns = parser.parse_args(parts)
        except (argparse.ArgumentError, SystemExit) as exc:
            print(f"Error: {exc}")
            return

        try:
            persistence.save(self.state, ns.name)
        except OSError as exc:
            print(f"Save failed: {exc}")
            return

        self.state.session_name = ns.name
        print(display.render(self.state))

    # ------------------------------------------------------------------
    # load command
    # ------------------------------------------------------------------

    def do_load(self, args: str) -> None:
        """Restore battle state from a named save slot.

        Usage:
            load --name <save-name>

        Flags:
            --name   Save slot name to restore.
        """
        try:
            parts = shlex.split(args)
        except ValueError as exc:
            print(f"Parse error: {exc}")
            return

        parser = _InlineArgumentParser(prog="load", add_help=False)
        parser.add_argument("--name", required=True)

        try:
            ns = parser.parse_args(parts)
        except (argparse.ArgumentError, SystemExit) as exc:
            print(f"Error: {exc}")
            return

        try:
            new_state = persistence.load(ns.name)
        except Exception as exc:
            print(f"Load failed: {exc}")
            return

        self.state = new_state
        print(display.render(self.state))
