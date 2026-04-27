from __future__ import annotations
from fastapi import APIRouter, Request

from .db import load_state, list_saves
from .models import PlayerData

router = APIRouter()


@router.get("/healthz")
async def healthz(request: Request):
    # Pool availability confirms DB is reachable
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        await conn.fetchval("SELECT 1")
    return {"ok": True}


@router.get("/state")
async def get_state(request: Request):
    pool = request.app.state.pool
    rows = await load_state(pool)
    players = [PlayerData(**r).model_dump() for r in rows]
    return {"type": "state", "players": players}


@router.get("/saves")
async def get_saves(request: Request):
    pool = request.app.state.pool
    saves = await list_saves(pool)
    return saves
