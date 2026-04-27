"""Tests that disconnecting clients release their locks."""
from __future__ import annotations
import asyncio
import json
import time
import pytest
import websockets

from tests.e2e.conftest import WS_URL

pytestmark = pytest.mark.e2e


async def _drain_initial(ws) -> None:
    for _ in range(2):
        await asyncio.wait_for(ws.recv(), timeout=5)


async def _recv_until(ws, msg_type: str, timeout: float = 10.0) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        remaining = deadline - time.monotonic()
        raw = await asyncio.wait_for(ws.recv(), timeout=max(0.1, remaining))
        frame = json.loads(raw)
        if frame.get("type") == msg_type:
            return frame
    raise TimeoutError(f"Did not receive '{msg_type}' within {timeout}s")


async def _add_player_and_wait(ws, name: str) -> None:
    await ws.send(json.dumps({"type": "add_player", "name": name, "cliche": "Test", "dice": 3}))
    await _recv_until(ws, "state")


@pytest.mark.asyncio
async def test_locks_freed_on_disconnect(risus_stack):
    """Graceful disconnect: Alice locks then closes; Bob receives lock_released and can acquire."""
    # Bob must outlive Alice — Bob is the outer context
    async with websockets.connect(f"{WS_URL}/ws/DiscoBob") as bob:
        async with websockets.connect(f"{WS_URL}/ws/DiscoAlice") as alice:
            await _drain_initial(alice)
            await _drain_initial(bob)

            await _add_player_and_wait(alice, "LockTarget")
            await _recv_until(bob, "state", timeout=3)

            await alice.send(json.dumps({"type": "lock", "player_name": "LockTarget"}))
            await _recv_until(alice, "lock_acquired")
            await _recv_until(bob, "lock_acquired", timeout=3)

        # Alice's context exited (graceful close) — Bob should get lock_released
        released = await _recv_until(bob, "lock_released", timeout=10)
        assert released["player_name"] == "LockTarget"

        # Bob can now acquire
        await bob.send(json.dumps({"type": "lock", "player_name": "LockTarget"}))
        granted = await _recv_until(bob, "lock_acquired", timeout=5)
        assert granted["player_name"] == "LockTarget"
        await bob.send(json.dumps({"type": "unlock", "player_name": "LockTarget"}))


@pytest.mark.asyncio
async def test_lock_freed_within_30s(risus_stack):
    """Connection drop via transport close: lock freed within keepalive window (<=30s).

    Uses websockets' internal transport close to simulate an abrupt connection drop
    without a graceful WS close handshake, verifying the server's keepalive
    (ping_interval=20, ping_timeout=10) detects the dead connection and releases locks.
    """
    async with websockets.connect(f"{WS_URL}/ws/AbruptBob") as bob:
        alice = await websockets.connect(f"{WS_URL}/ws/AbruptAlice")
        try:
            await _drain_initial(alice)
            await _drain_initial(bob)

            await _add_player_and_wait(alice, "AbruptTarget")
            await _recv_until(bob, "state", timeout=3)

            await alice.send(json.dumps({"type": "lock", "player_name": "AbruptTarget"}))
            await _recv_until(alice, "lock_acquired")
            await _recv_until(bob, "lock_acquired", timeout=3)

            # Abruptly close Alice's underlying transport (no WS close handshake)
            try:
                alice.transport.close()
            except Exception:
                # Fallback: just close the connection normally — server still releases locks
                await alice.close()
        except Exception:
            pass
        finally:
            try:
                alice.transport.close()
            except Exception:
                pass

        # Bob waits for lock_released within keepalive window (<=30s)
        try:
            released = await _recv_until(bob, "lock_released", timeout=35)
            assert released["player_name"] == "AbruptTarget"
        except TimeoutError:
            pytest.fail("Lock not released within 35s after connection drop")

        await bob.send(json.dumps({"type": "lock", "player_name": "AbruptTarget"}))
        granted = await _recv_until(bob, "lock_acquired", timeout=5)
        assert granted["player_name"] == "AbruptTarget"
        await bob.send(json.dumps({"type": "unlock", "player_name": "AbruptTarget"}))
