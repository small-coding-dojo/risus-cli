from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class PlayerData(BaseModel):
    name: str
    cliche: str = ""
    dice: Optional[int] = None
    lost_dice: int = 0


class StateMsg(BaseModel):
    type: str = "state"
    players: list[PlayerData]


class PresenceMsg(BaseModel):
    type: str = "presence"
    clients: list[str]


class LockAcquiredMsg(BaseModel):
    type: str = "lock_acquired"
    player_name: str
    locked_by: str


class LockReleasedMsg(BaseModel):
    type: str = "lock_released"
    player_name: str


class LockDeniedMsg(BaseModel):
    type: str = "lock_denied"
    player_name: str
    locked_by: str


class ErrorMsg(BaseModel):
    type: str = "error"
    message: str
