"""E2E tests for token authentication against a real container stack."""
from __future__ import annotations
import asyncio
import json
import pytest
import websockets

from tests.e2e.conftest import TOKEN, WS_URL

pytestmark = pytest.mark.e2e


async def _recv_with_timeout(ws, timeout: float = 10.0) -> dict:
    raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
    return json.loads(raw)


async def _expect_close_4401(uri: str) -> None:
    ws = await websockets.connect(uri)
    close_code = None
    try:
        for _ in range(5):
            try:
                await asyncio.wait_for(ws.recv(), timeout=10)
            except websockets.exceptions.ConnectionClosed as exc:
                close_code = exc.rcvd.code if exc.rcvd else None
                break
    finally:
        try:
            await ws.close()
        except Exception:
            pass
    assert close_code == 4401, f"Expected close code 4401, got {close_code}"


@pytest.mark.asyncio
async def test_correct_token_connects_and_receives_state(risus_stack):
    """Correct token: connection accepted, state frame received."""
    async with websockets.connect(f"{WS_URL}/ws/TokenTestUser?token={TOKEN}") as ws:
        frame = await _recv_with_timeout(ws, timeout=10)
    assert frame["type"] == "state"


@pytest.mark.asyncio
async def test_wrong_token_rejected(risus_stack):
    """Wrong token: server closes connection with code 4401."""
    await _expect_close_4401(f"{WS_URL}/ws/TokenTestWrong?token=wrong-token-value")


@pytest.mark.asyncio
async def test_absent_token_rejected(risus_stack):
    """No token: server closes connection with code 4401."""
    await _expect_close_4401(f"{WS_URL}/ws/TokenTestAbsent")
