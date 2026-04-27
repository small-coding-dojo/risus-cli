"""Persistence tests: server restart, named save/load."""
from __future__ import annotations
import asyncio
import json
import os
import subprocess
import time
import pytest
import websockets

from tests.e2e.conftest import WS_URL, COMPOSE_FILE

pytestmark = pytest.mark.e2e

_CONTAINER_ENGINE = os.environ.get("CONTAINER_ENGINE", "docker")


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


def _restart_server():
    if _CONTAINER_ENGINE == "podman":
        subprocess.run(["podman-compose", "-f", COMPOSE_FILE, "restart", "server"], check=True)
    else:
        subprocess.run(
            ["docker", "compose", "-f", COMPOSE_FILE, "restart", "server"],
            check=True,
        )
    # Wait for server to come back healthy
    import urllib.request, urllib.error
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen("http://localhost:8765/healthz", timeout=3) as r:
                if r.status == 200:
                    return
        except Exception:
            pass
        time.sleep(1)
    pytest.fail("Server did not recover within 60s after restart")


@pytest.mark.asyncio
async def test_state_survives_server_restart(risus_stack):
    # Add players
    async with websockets.connect(f"{WS_URL}/ws/RestartTester") as ws:
        await _drain_initial(ws)
        await ws.send(json.dumps({"type": "add_player", "name": "Survivor", "cliche": "Warrior", "dice": 5}))
        await _recv_until(ws, "state")

    # Restart server
    _restart_server()

    # Reconnect and verify state
    async with websockets.connect(f"{WS_URL}/ws/RestartTester2") as ws:
        state = await _recv_until(ws, "state")
        names = {p["name"] for p in state["players"]}
        assert "Survivor" in names, f"Expected Survivor in {names}"


@pytest.mark.asyncio
async def test_named_save_load(risus_stack):
    async with websockets.connect(f"{WS_URL}/ws/SaveUser") as alice:
        async with websockets.connect(f"{WS_URL}/ws/LoadUser") as bob:
            await _drain_initial(alice)
            await _drain_initial(bob)

            # Alice adds a player
            await alice.send(json.dumps({"type": "add_player", "name": "SavedHero", "cliche": "Paladin", "dice": 6}))
            await _recv_until(alice, "state")
            await _recv_until(bob, "state", timeout=3)

            # Alice saves
            await alice.send(json.dumps({"type": "save", "save_name": "test_save_1"}))
            # Save sends state back to caller only
            await _recv_until(alice, "state")

            # Alice adds another player (mutates state)
            await alice.send(json.dumps({"type": "add_player", "name": "Mutant", "cliche": "Rogue", "dice": 2}))
            await _recv_until(alice, "state")
            await _recv_until(bob, "state", timeout=3)

            # Bob loads the old save
            await bob.send(json.dumps({"type": "load", "save_name": "test_save_1"}))
            loaded = await _recv_until(bob, "state", timeout=5)
            names = {p["name"] for p in loaded["players"]}
            assert "SavedHero" in names
            assert "Mutant" not in names

            # Alice also gets the broadcast
            alice_reload = await _recv_until(alice, "state", timeout=5)
            names2 = {p["name"] for p in alice_reload["players"]}
            assert "Mutant" not in names2
