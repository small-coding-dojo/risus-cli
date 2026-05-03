from __future__ import annotations
import asyncio
import json
import queue
import threading
import time

import websockets

from .state import ClientState

RECONNECT_DELAYS = [1, 2, 4, 8]


class AuthError(Exception):
    pass


class WSClient:
    def __init__(self) -> None:
        self.state = ClientState()
        self._outbox: queue.Queue[str] = queue.Queue()
        self._inbox: queue.Queue[dict] = queue.Queue()
        self._thread: threading.Thread | None = None
        self._uri: str = ""
        self._stop = threading.Event()

    def start(self, server: str, name: str, token: str, timeout: float = 10.0) -> None:
        scheme = "ws://" if ":" in server else "wss://"
        self._uri = f"{scheme}{server}/ws/{name}?token={token}"
        self._stop.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                frame = self._inbox.get(timeout=0.2)
                ft = frame.get("type")
                if ft == "auth_failed":
                    raise AuthError("token rejected by server")
                if ft == "disconnected":
                    raise TimeoutError(f"No response from server at {server} within {timeout}s")
                if ft != "connected":
                    self._inbox.put(frame)
                return
            except queue.Empty:
                pass
        raise TimeoutError(f"No response from server at {server} within {timeout}s")

    def send(self, payload: dict) -> None:
        self._outbox.put(json.dumps(payload))

    def recv(self, timeout: float = 5.0) -> dict | None:
        try:
            return self._inbox.get(timeout=timeout)
        except queue.Empty:
            return None

    def drain_inbox(self) -> list[dict]:
        frames: list[dict] = []
        while True:
            try:
                frames.append(self._inbox.get_nowait())
            except queue.Empty:
                break
        return frames

    def stop(self) -> None:
        self._stop.set()

    def _run_loop(self) -> None:
        asyncio.run(self._async_run())

    async def _async_run(self) -> None:
        delay_idx = 0
        while not self._stop.is_set():
            try:
                async with websockets.connect(self._uri) as ws:
                    delay_idx = 0
                    self._inbox.put({"type": "connected"})
                    await asyncio.gather(
                        self._reader(ws),
                        self._writer(ws),
                    )
            except websockets.exceptions.ConnectionClosedError as e:
                if e.rcvd is not None and e.rcvd.code == 4401:
                    self._inbox.put({"type": "auth_failed"})
                    return
            except Exception:
                pass
            if self._stop.is_set():
                break
            self._inbox.put({"type": "disconnected"})
            delay = RECONNECT_DELAYS[min(delay_idx, len(RECONNECT_DELAYS) - 1)]
            delay_idx += 1
            await asyncio.sleep(delay)

    async def _reader(self, ws) -> None:
        async for raw in ws:
            try:
                frame = json.loads(raw)
            except Exception:
                continue
            self.state.apply(frame)
            self._inbox.put(frame)

    async def _writer(self, ws) -> None:
        loop = asyncio.get_event_loop()
        while True:
            try:
                raw = await loop.run_in_executor(None, self._outbox.get, True, 0.1)
                await ws.send(raw)
            except queue.Empty:
                pass
            except Exception:
                break
