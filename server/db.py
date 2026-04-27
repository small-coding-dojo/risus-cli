from __future__ import annotations
import asyncpg
from typing import Any, Optional


async def create_pool(dsn: str) -> asyncpg.Pool:
    return await asyncpg.create_pool(dsn, min_size=1, max_size=5)


async def truncate_locks(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        await conn.execute("TRUNCATE locks")


async def load_state(pool: asyncpg.Pool) -> list[dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT name, cliche, dice, lost_dice FROM players ORDER BY name"
        )
    return [dict(r) for r in rows]


async def upsert_player(pool: asyncpg.Pool, name: str, cliche: str, dice: Optional[int], lost_dice: int) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO players (name, cliche, dice, lost_dice)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (name) DO UPDATE
            SET cliche = EXCLUDED.cliche,
                dice = EXCLUDED.dice,
                lost_dice = EXCLUDED.lost_dice
            """,
            name, cliche, dice, lost_dice,
        )


async def delete_player(pool: asyncpg.Pool, name: str) -> None:
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM players WHERE name = $1", name)


async def player_exists(pool: asyncpg.Pool, name: str) -> bool:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT 1 FROM players WHERE name = $1", name)
    return row is not None


async def save_snapshot(pool: asyncpg.Pool, save_name: str, data: Any) -> None:
    import json
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO saves (save_name, data)
            VALUES ($1, $2::jsonb)
            ON CONFLICT (save_name) DO UPDATE
            SET data = EXCLUDED.data, saved_at = now()
            """,
            save_name, json.dumps(data),
        )


async def load_snapshot(pool: asyncpg.Pool, save_name: str) -> Optional[Any]:
    import json
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT data FROM saves WHERE save_name = $1", save_name
        )
    if row is None:
        return None
    return json.loads(row["data"])


async def list_saves(pool: asyncpg.Pool) -> list[dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT save_name, saved_at FROM saves ORDER BY saved_at DESC"
        )
    return [{"save_name": r["save_name"], "saved_at": r["saved_at"].isoformat()} for r in rows]


async def replace_players(pool: asyncpg.Pool, players: list[dict]) -> None:
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("TRUNCATE players CASCADE")
            for p in players:
                await conn.execute(
                    "INSERT INTO players (name, cliche, dice, lost_dice) VALUES ($1, $2, $3, $4)",
                    p["name"], p.get("cliche", ""), p.get("dice"), p.get("lost_dice", 0),
                )
