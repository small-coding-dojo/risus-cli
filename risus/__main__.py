"""Entry point for the Risus CLI.

Usage:
    cli [--load <save-name>]
"""

from __future__ import annotations

import argparse
import sys

from risus import display
from risus.models import BattleState, SaveNotFoundError
from risus.repl import RisusRepl


def main() -> None:
    """Parse OS-level args, optionally load a save, and start the REPL."""
    parser = argparse.ArgumentParser(
        prog="cli",
        description="Risus RPG battle state tracker",
    )
    parser.add_argument("--load", metavar="NAME", help="Load a named save slot")
    args = parser.parse_args()

    if args.load:
        try:
            from risus import persistence  # noqa: PLC0415
            state = persistence.load(args.load)
        except SaveNotFoundError:
            print(f"Save '{args.load}' not found", file=sys.stderr)
            sys.exit(1)
    else:
        state = BattleState()

    print(display.render(state))
    RisusRepl(state).cmdloop()


if __name__ == "__main__":
    main()
