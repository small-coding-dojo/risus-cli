from __future__ import annotations
import threading
from dataclasses import dataclass
from typing import Optional


@dataclass
class PlayerSnapshot:
    name: str
    cliche: str = ""
    dice: Optional[int] = None
    lost_dice: int = 0


class ClientState:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.players: list[PlayerSnapshot] = []
        self.presence: list[str] = []
        self.locks: dict[str, str] = {}  # player_name -> display_name of holder

    def apply(self, frame: dict) -> None:
        msg_type = frame.get("type", "")
        with self._lock:
            if msg_type == "state":
                self.players = [
                    PlayerSnapshot(
                        name=p["name"],
                        cliche=p.get("cliche", ""),
                        dice=p.get("dice"),
                        lost_dice=p.get("lost_dice", 0),
                    )
                    for p in frame.get("players", [])
                ]
            elif msg_type == "presence":
                self.presence = list(frame.get("clients", []))
            elif msg_type == "lock_acquired":
                self.locks[frame["player_name"]] = frame["locked_by"]
            elif msg_type == "lock_released":
                self.locks.pop(frame.get("player_name", ""), None)

    def snapshot_players(self) -> list[PlayerSnapshot]:
        with self._lock:
            return list(self.players)

    def snapshot_presence(self) -> list[str]:
        with self._lock:
            return list(self.presence)

    def snapshot_locks(self) -> dict[str, str]:
        with self._lock:
            return dict(self.locks)
