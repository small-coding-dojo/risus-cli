from __future__ import annotations
import json
from typing import TYPE_CHECKING

from .db import (
    load_state, upsert_player, delete_player, player_exists,
    save_snapshot, load_snapshot, replace_players,
)
from .models import (
    PlayerData, StateMsg, ErrorMsg,
    LockAcquiredMsg, LockReleasedMsg, LockDeniedMsg,
)

if TYPE_CHECKING:
    import asyncpg
    from .locks import LockManager
    from .ws import ConnectionManager


def _error(message: str) -> str:
    return ErrorMsg(message=message).model_dump_json()


async def _broadcast_state(pool: "asyncpg.Pool", mgr: "ConnectionManager") -> None:
    rows = await load_state(pool)
    players = [PlayerData(**r) for r in rows]
    await mgr.broadcast(StateMsg(players=players).model_dump_json())


async def handle_add_player(
    payload: dict,
    client_id: str,
    pool: "asyncpg.Pool",
    lock_mgr: "LockManager",
    conn_mgr: "ConnectionManager",
) -> None:
    name = (payload.get("name") or "").strip()
    if not name:
        await conn_mgr.send(client_id, _error("player name required"))
        return
    if await player_exists(pool, name):
        await conn_mgr.send(client_id, _error(f"player already exists: {name}"))
        return
    cliche = (payload.get("cliche") or "").strip()
    dice = payload.get("dice")
    await upsert_player(pool, name, cliche, dice, 0)
    await _broadcast_state(pool, conn_mgr)


async def handle_switch_cliche(
    payload: dict,
    client_id: str,
    pool: "asyncpg.Pool",
    lock_mgr: "LockManager",
    conn_mgr: "ConnectionManager",
) -> None:
    player_name = (payload.get("player_name") or "").strip()
    holder_id = lock_mgr.holder(player_name)
    if holder_id != client_id:
        holder_dn = lock_mgr.holder_display(player_name) or "unlocked"
        await conn_mgr.send(client_id, _error(
            f"lock required — {player_name} locked by {holder_dn} or unlocked"
        ))
        return
    if not await player_exists(pool, player_name):
        await conn_mgr.send(client_id, _error(f"no such player: {player_name}"))
        return
    cliche = (payload.get("cliche") or "").strip()
    dice = payload.get("dice")
    rows = await load_state(pool)
    player_row = next((r for r in rows if r["name"] == player_name), None)
    if player_row is None:
        await conn_mgr.send(client_id, _error(f"no such player: {player_name}"))
        return
    await upsert_player(pool, player_name, cliche, dice, player_row["lost_dice"])
    await _broadcast_state(pool, conn_mgr)


async def handle_reduce_dice(
    payload: dict,
    client_id: str,
    pool: "asyncpg.Pool",
    lock_mgr: "LockManager",
    conn_mgr: "ConnectionManager",
) -> None:
    player_name = (payload.get("player_name") or "").strip()
    holder_id = lock_mgr.holder(player_name)
    if holder_id != client_id:
        holder_dn = lock_mgr.holder_display(player_name) or "unlocked"
        await conn_mgr.send(client_id, _error(
            f"lock required — {player_name} locked by {holder_dn} or unlocked"
        ))
        return
    rows = await load_state(pool)
    player_row = next((r for r in rows if r["name"] == player_name), None)
    if player_row is None:
        await conn_mgr.send(client_id, _error(f"no such player: {player_name}"))
        return
    amount = int(payload.get("amount") or 0)
    is_dead = bool(payload.get("is_dead", False))

    dice = player_row["dice"]
    lost_dice = player_row["lost_dice"]

    if dice is None:
        lost_dice += max(0, amount)
        if is_dead:
            await delete_player(pool, player_name)
        else:
            await upsert_player(pool, player_name, player_row["cliche"], None, lost_dice)
    else:
        new_dice = max(0, dice - amount)
        if new_dice == 0:
            await delete_player(pool, player_name)
        else:
            await upsert_player(pool, player_name, player_row["cliche"], new_dice, lost_dice)
    await _broadcast_state(pool, conn_mgr)


async def handle_lock(
    payload: dict,
    client_id: str,
    display_name: str,
    pool: "asyncpg.Pool",
    lock_mgr: "LockManager",
    conn_mgr: "ConnectionManager",
) -> None:
    player_name = (payload.get("player_name") or "").strip()
    acquired = await lock_mgr.acquire(player_name, client_id, display_name)
    if acquired:
        await conn_mgr.broadcast(
            LockAcquiredMsg(player_name=player_name, locked_by=display_name).model_dump_json()
        )
    else:
        holder_dn = lock_mgr.holder_display(player_name) or "unknown"
        await conn_mgr.send(
            client_id,
            LockDeniedMsg(player_name=player_name, locked_by=holder_dn).model_dump_json(),
        )


async def handle_unlock(
    payload: dict,
    client_id: str,
    pool: "asyncpg.Pool",
    lock_mgr: "LockManager",
    conn_mgr: "ConnectionManager",
) -> None:
    player_name = (payload.get("player_name") or "").strip()
    await lock_mgr.release(player_name, client_id)
    await conn_mgr.broadcast(LockReleasedMsg(player_name=player_name).model_dump_json())


async def handle_save(
    payload: dict,
    client_id: str,
    pool: "asyncpg.Pool",
    lock_mgr: "LockManager",
    conn_mgr: "ConnectionManager",
) -> None:
    save_name = (payload.get("save_name") or "").strip()
    if not save_name:
        await conn_mgr.send(client_id, _error("save_name required"))
        return
    rows = await load_state(pool)
    await save_snapshot(pool, save_name, rows)
    rows2 = await load_state(pool)
    players = [PlayerData(**r) for r in rows2]
    await conn_mgr.send(client_id, StateMsg(players=players).model_dump_json())


async def handle_load(
    payload: dict,
    client_id: str,
    pool: "asyncpg.Pool",
    lock_mgr: "LockManager",
    conn_mgr: "ConnectionManager",
) -> None:
    save_name = (payload.get("save_name") or "").strip()
    data = await load_snapshot(pool, save_name)
    if data is None:
        await conn_mgr.send(client_id, _error(f"no save named: {save_name}"))
        return
    # Release all locks before replacing state
    all_clients = list(conn_mgr.clients.keys())
    for cid in all_clients:
        freed = await lock_mgr.release_all(cid)
        for pname in freed:
            await conn_mgr.broadcast(LockReleasedMsg(player_name=pname).model_dump_json())
    await replace_players(pool, data)
    await _broadcast_state(pool, conn_mgr)


async def dispatch(
    raw: str,
    client_id: str,
    display_name: str,
    pool: "asyncpg.Pool",
    lock_mgr: "LockManager",
    conn_mgr: "ConnectionManager",
) -> None:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        await conn_mgr.send(client_id, _error("invalid JSON"))
        return

    msg_type = payload.get("type", "")
    kwargs = dict(
        payload=payload,
        client_id=client_id,
        pool=pool,
        lock_mgr=lock_mgr,
        conn_mgr=conn_mgr,
    )

    if msg_type == "add_player":
        await handle_add_player(**kwargs)
    elif msg_type == "switch_cliche":
        await handle_switch_cliche(**kwargs)
    elif msg_type == "reduce_dice":
        await handle_reduce_dice(**kwargs)
    elif msg_type == "lock":
        await handle_lock(display_name=display_name, **kwargs)
    elif msg_type == "unlock":
        await handle_unlock(**kwargs)
    elif msg_type == "save":
        await handle_save(**kwargs)
    elif msg_type == "load":
        await handle_load(**kwargs)
    else:
        await conn_mgr.send(client_id, _error(f"unknown message type: {msg_type}"))
