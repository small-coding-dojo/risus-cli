"""Two-client interaction tests: state propagation, locking, name collision."""
from __future__ import annotations
import asyncio
import json
import time
import pytest
import websockets

from tests.e2e.conftest import TOKEN, WS_URL

pytestmark = pytest.mark.e2e


async def _recv_until(ws, msg_type: str, timeout: float = 5.0) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        remaining = deadline - time.monotonic()
        raw = await asyncio.wait_for(ws.recv(), timeout=max(0.1, remaining))
        frame = json.loads(raw)
        if frame.get("type") == msg_type:
            return frame
    raise TimeoutError(f"Did not receive '{msg_type}' within {timeout}s")


async def _drain_initial(ws) -> None:
    """Consume state + presence frames sent on connect."""
    for _ in range(2):
        await asyncio.wait_for(ws.recv(), timeout=5)


@pytest.mark.asyncio
async def test_state_propagates_within_one_second(risus_stack):
    async with websockets.connect(f"{WS_URL}/ws/Alice?token={TOKEN}") as alice:
        async with websockets.connect(f"{WS_URL}/ws/Bob?token={TOKEN}") as bob:
            await _drain_initial(alice)
            await _drain_initial(bob)

            # Alice adds a player
            await alice.send(json.dumps({
                "type": "add_player",
                "name": "Goblin",
                "cliche": "Bandit",
                "dice": 3,
            }))

            start = time.monotonic()
            frame = await _recv_until(bob, "state", timeout=2.0)
            elapsed = time.monotonic() - start

            assert frame["type"] == "state"
            names = {p["name"] for p in frame["players"]}
            assert "Goblin" in names
            assert elapsed < 1.0, f"State propagation took {elapsed:.2f}s"


@pytest.mark.asyncio
async def test_lock_blocks_concurrent_edit(risus_stack):
    async with websockets.connect(f"{WS_URL}/ws/Alice2?token={TOKEN}") as alice:
        async with websockets.connect(f"{WS_URL}/ws/Bob2?token={TOKEN}") as bob:
            await _drain_initial(alice)
            await _drain_initial(bob)

            # Add a player first
            await alice.send(json.dumps({"type": "add_player", "name": "Orc", "cliche": "Warrior", "dice": 4}))
            await _recv_until(alice, "state")  # wait for confirmation
            # Bob also gets the state broadcast
            await _recv_until(bob, "state", timeout=3)

            # Alice acquires lock
            await alice.send(json.dumps({"type": "lock", "player_name": "Orc"}))
            alice_frame = await _recv_until(alice, "lock_acquired", timeout=3)
            assert alice_frame["player_name"] == "Orc"
            # Bob also receives lock_acquired broadcast
            bob_frame = await _recv_until(bob, "lock_acquired", timeout=3)
            assert bob_frame["player_name"] == "Orc"

            # Bob tries to lock — should be denied
            await bob.send(json.dumps({"type": "lock", "player_name": "Orc"}))
            denied = await _recv_until(bob, "lock_denied", timeout=3)
            assert denied["player_name"] == "Orc"
            assert denied["locked_by"] == "Alice2"

            # Alice releases
            await alice.send(json.dumps({"type": "unlock", "player_name": "Orc"}))
            await _recv_until(alice, "lock_released", timeout=3)

            # Bob can now lock
            await bob.send(json.dumps({"type": "lock", "player_name": "Orc"}))
            granted = await _recv_until(bob, "lock_acquired", timeout=3)
            assert granted["player_name"] == "Orc"
            await bob.send(json.dumps({"type": "unlock", "player_name": "Orc"}))


@pytest.mark.asyncio
async def test_duplicate_name_rejected(risus_stack):
    async with websockets.connect(f"{WS_URL}/ws/UniqueUser?token={TOKEN}") as _ws1:
        await _drain_initial(_ws1)

        # Second connection with same name: server accepts then closes with 4409
        ws2 = await websockets.connect(f"{WS_URL}/ws/UniqueUser?token={TOKEN}")
        try:
            # Drain any frames; expect close code 4409
            close_code = None
            for _ in range(5):
                try:
                    await asyncio.wait_for(ws2.recv(), timeout=2)
                except websockets.exceptions.ConnectionClosed as exc:
                    close_code = exc.rcvd.code if exc.rcvd else None
                    break
                except asyncio.TimeoutError:
                    break
        finally:
            try:
                await ws2.close()
            except Exception:
                pass

        assert close_code == 4409, f"Expected close code 4409, got {close_code}"
