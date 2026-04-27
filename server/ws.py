from __future__ import annotations
import uuid
from fastapi import WebSocket, WebSocketDisconnect

from .models import StateMsg, PresenceMsg, PlayerData
from .db import load_state


class ConnectionManager:
    def __init__(self) -> None:
        # client_id -> (WebSocket, display_name)
        self.clients: dict[str, tuple[WebSocket, str]] = {}
        # display_name -> client_id (for collision detection)
        self._names: dict[str, str] = {}

    def _presence_payload(self) -> str:
        names = [dn for _, dn in self.clients.values()]
        return PresenceMsg(clients=names).model_dump_json()

    async def broadcast(self, message: str, except_id: str | None = None) -> None:
        dead: list[str] = []
        for cid, (ws, _) in list(self.clients.items()):
            if cid == except_id:
                continue
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(cid)
        for cid in dead:
            self.clients.pop(cid, None)

    async def send(self, client_id: str, message: str) -> None:
        entry = self.clients.get(client_id)
        if entry:
            try:
                await entry[0].send_text(message)
            except Exception:
                pass

    async def handle(
        self,
        ws: WebSocket,
        client_name: str,
        pool,
        lock_mgr,
    ) -> None:
        from . import commands as cmd

        # Collision check — must accept first to send a proper WS close frame
        if client_name in self._names:
            await ws.accept()
            await ws.close(code=4409, reason="name in use")
            return

        await ws.accept()
        client_id = str(uuid.uuid4())
        self.clients[client_id] = (ws, client_name)
        self._names[client_name] = client_id

        # Send initial state + presence
        rows = await load_state(pool)
        players = [PlayerData(**r) for r in rows]
        await ws.send_text(StateMsg(players=players).model_dump_json())
        await ws.send_text(self._presence_payload())
        # Broadcast updated presence to others
        await self.broadcast(self._presence_payload(), except_id=client_id)

        try:
            async for raw in ws.iter_text():
                await cmd.dispatch(raw, client_id, client_name, pool, lock_mgr, self)
        except WebSocketDisconnect:
            pass
        except Exception:
            pass
        finally:
            await self._disconnect(client_id, client_name, lock_mgr)

    async def _disconnect(self, client_id: str, client_name: str, lock_mgr) -> None:
        # 1. Release all locks
        freed = await lock_mgr.release_all(client_id)
        # 2. Broadcast lock_released per freed player
        from .models import LockReleasedMsg
        for player_name in freed:
            await self.broadcast(LockReleasedMsg(player_name=player_name).model_dump_json())
        # 3. Remove client from map
        self.clients.pop(client_id, None)
        self._names.pop(client_name, None)
        # 4. Broadcast updated presence
        await self.broadcast(self._presence_payload())
