"""Battle state display renderer for the Risus CLI."""

from __future__ import annotations

from risus.models import BattleState


def render(state: BattleState) -> str:
    """Render the battle state as a formatted string.

    Format:
        Battle latest state [(<session-name>)]
        =======================================
        <player-name>:     <n> dice (<cliche-name>)
        ...

    The separator line of '=' characters matches the header length exactly.
    Only players with dice > 0 are listed.

    Args:
        state: The current BattleState to render.

    Returns:
        A multi-line string ready to print to stdout.
    """
    if state.session_name:
        header = f"Battle latest state ({state.session_name})"
    else:
        header = "Battle latest state"

    separator = "=" * len(header)

    lines = [header, separator]
    for player in state.active_players():
        lines.append(f"{player.name}:     {player.dice} dice ({player.cliche_name})")

    return "\n".join(lines)
