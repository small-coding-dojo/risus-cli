"""Core data model for Risus CLI battle state tracking."""

from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Domain Exceptions
# ---------------------------------------------------------------------------

class DuplicatePlayerError(Exception):
    """Raised when adding a player whose name already exists in the battle."""


class PlayerNotFoundError(Exception):
    """Raised when referencing a player that does not exist in the battle."""


class SaveNotFoundError(Exception):
    """Raised when loading a save slot that does not exist on disk."""


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------

@dataclass
class Player:
    """A single character participating in a Risus battle."""

    name: str
    cliche_name: str = ""
    dice: int = 0


@dataclass
class BattleState:
    """Aggregate root for an interactive Risus session."""

    # Ordered dict preserves insertion order (Python 3.7+)
    players: dict[str, Player] = field(default_factory=dict)
    session_name: str | None = None

    # ------------------------------------------------------------------
    # Mutating operations
    # ------------------------------------------------------------------

    def add_player(self, name: str, cliche: str = "", dice: int = 0) -> Player:
        """Add a new player to the battle.

        Args:
            name: Player name (must be unique within this state).
            cliche: Starting active cliché (default empty string).
            dice: Starting dice count (default 0).

        Returns:
            The newly created Player.

        Raises:
            DuplicatePlayerError: If a player with this name already exists.
        """
        if name in self.players:
            raise DuplicatePlayerError(f"Player '{name}' already exists")
        player = Player(name=name, cliche_name=cliche, dice=dice)
        self.players[name] = player
        return player

    def switch_cliche(
        self, player_name: str, cliche_name: str, dice: int
    ) -> Player:
        """Update a player's active cliché and dice pool.

        Args:
            player_name: Name of the player to update.
            cliche_name: New cliché name.
            dice: New dice count (≥ 0).

        Returns:
            The updated Player.

        Raises:
            PlayerNotFoundError: If no player with this name exists.
        """
        if player_name not in self.players:
            raise PlayerNotFoundError(f"Player '{player_name}' not found")
        player = self.players[player_name]
        player.cliche_name = cliche_name
        player.dice = dice
        return player

    def reduce_dice(self, player_name: str, amount: int) -> Player:
        """Reduce a player's dice pool, clamped at 0.

        When dice reach 0 the player is considered eliminated and will be
        excluded from active_players() / the display, but the object is
        retained in memory.

        Args:
            player_name: Name of the player to update.
            amount: Number of dice to remove (≥ 1).

        Returns:
            The updated Player.

        Raises:
            PlayerNotFoundError: If no player with this name exists.
        """
        if player_name not in self.players:
            raise PlayerNotFoundError(f"Player '{player_name}' not found")
        player = self.players[player_name]
        player.dice = max(0, player.dice - amount)
        return player

    # ------------------------------------------------------------------
    # Query operations
    # ------------------------------------------------------------------

    def active_players(self) -> list[Player]:
        """Return players with dice > 0 in insertion order."""
        return [p for p in self.players.values() if p.dice > 0]
