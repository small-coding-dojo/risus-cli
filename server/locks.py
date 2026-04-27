from __future__ import annotations
import asyncio
from typing import Optional


class LockManager:
    """In-memory lock store. Authoritative at runtime. Locks are session-scoped."""

    def __init__(self) -> None:
        # player_name -> (display_name, client_id)
        self._locks: dict[str, tuple[str, str]] = {}
        self._mu = asyncio.Lock()

    async def acquire(self, player_name: str, client_id: str, display_name: str) -> bool:
        async with self._mu:
            if player_name in self._locks:
                return False
            self._locks[player_name] = (display_name, client_id)
            return True

    async def release(self, player_name: str, client_id: str) -> bool:
        async with self._mu:
            entry = self._locks.get(player_name)
            if entry is None or entry[1] != client_id:
                return False
            del self._locks[player_name]
            return True

    async def release_all(self, client_id: str) -> list[str]:
        async with self._mu:
            freed = [name for name, (_, cid) in self._locks.items() if cid == client_id]
            for name in freed:
                del self._locks[name]
            return freed

    def holder(self, player_name: str) -> Optional[str]:
        """Return client_id of holder or None."""
        entry = self._locks.get(player_name)
        return entry[1] if entry else None

    def holder_display(self, player_name: str) -> Optional[str]:
        """Return display_name of holder or None."""
        entry = self._locks.get(player_name)
        return entry[0] if entry else None

    def snapshot(self) -> dict[str, str]:
        """Return {player_name: display_name} for all current locks."""
        return {name: dn for name, (dn, _) in self._locks.items()}
