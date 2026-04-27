from __future__ import annotations
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket

from .db import create_pool, truncate_locks
from .locks import LockManager
from .ws import ConnectionManager
from .rest import router as rest_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    dsn = os.environ["DATABASE_URL"]
    pool = await create_pool(dsn)
    await truncate_locks(pool)

    lock_mgr = LockManager()
    conn_mgr = ConnectionManager()

    app.state.pool = pool
    app.state.lock_mgr = lock_mgr
    app.state.conn_mgr = conn_mgr

    yield

    await pool.close()


app = FastAPI(lifespan=lifespan)
app.include_router(rest_router)


@app.websocket("/ws/{client_name}")
async def ws_endpoint(ws: WebSocket, client_name: str):
    pool = ws.app.state.pool
    lock_mgr = ws.app.state.lock_mgr
    conn_mgr = ws.app.state.conn_mgr
    await conn_mgr.handle(ws, client_name, pool, lock_mgr)
