"""JSON persistence layer for Risus CLI save slots.

Save files are stored in ~/.risus/saves/ as <slug>.json.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from risus.models import BattleState, Player, SaveNotFoundError


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _slug(name: str) -> str:
    """Convert an arbitrary save name to a filesystem-safe slug."""
    return re.sub(r"[^a-zA-Z0-9_-]", "_", name).lower()


def _save_dir() -> Path:
    """Return (and create) the directory that holds save files."""
    d = Path.home() / ".risus" / "saves"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def save(state: BattleState, name: str) -> None:
    """Serialise *state* to a JSON file in the save directory.

    Args:
        state: The BattleState to persist.
        name:  Human-readable save name (used as both metadata and filename slug).

    Raises:
        OSError: If the file cannot be written.
    """
    payload = {
        "name": name,
        "players": [
            {
                "name": p.name,
                "cliche_name": p.cliche_name,
                "dice": p.dice,
            }
            for p in state.players.values()
        ],
    }
    path = _save_dir() / (_slug(name) + ".json")
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def load(name: str) -> BattleState:
    """Deserialise a named save into a new BattleState.

    Args:
        name: Human-readable save name (matched by slug).

    Returns:
        A BattleState with session_name set to *name*.

    Raises:
        SaveNotFoundError: If no save with this name exists on disk.
    """
    path = _save_dir() / (_slug(name) + ".json")
    if not path.exists():
        raise SaveNotFoundError(f"Save '{name}' not found")

    raw = json.loads(path.read_text(encoding="utf-8"))
    state = BattleState(session_name=raw.get("name", name))
    for p in raw.get("players", []):
        player = Player(
            name=p["name"],
            cliche_name=p.get("cliche_name", ""),
            dice=p.get("dice", 0),
        )
        state.players[player.name] = player
    return state
