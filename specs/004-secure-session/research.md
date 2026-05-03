# Research: Secure Session

## Token Validation in FastAPI WebSocket

**Decision**: Validate token from `ws.query_params.get("token")` before proceeding.

**Rationale**: FastAPI's `WebSocket` exposes `query_params` as a
`starlette.datastructures.QueryParams` object (dict-like `.get()` works).
Token must travel in the query string because the WS handshake HTTP `Upgrade`
request cannot carry a custom `Authorization` header in the standard
browser/websockets-client flow.

**Pattern confirmed** from Starlette source: `websocket.query_params` is
available before `ws.accept()`.

**Close-before-accept problem**: To send a WebSocket close frame, the
connection must be accepted first. Pattern used throughout the existing
codebase (see `code=4409` collision check in `server/ws.py:50-53`).
Confirmed: must call `await ws.accept()` before
`await ws.close(code=4401, ...)`.

---

## Brute-Force Delay (FR-010)

**Decision**: `await asyncio.sleep(3)` immediately after `ws.accept()`,
before token check.

**Rationale**: Applying the delay before the check means it runs for all
connections (valid, invalid, absent) — no timing oracle. If the delay were
after the check, an attacker could distinguish "fast reject" from "slow
accept" to confirm correct tokens.

**Confirmed**: SC-001 says correct-token connection delivers state within "3–4 seconds",
consistent with this approach.

---

## 4401 Propagation to Client

**Decision**: In `WSClient._async_run()`, catch
`websockets.exceptions.ConnectionClosedError` with `rcvd.code == 4401`, put
`{"type": "auth_failed"}` in the inbox, and return (no reconnect). In
`start()`, raise `AuthError` when `auth_failed` frame arrives.

**Rationale**: The existing reconnection loop in `_async_run` must NOT retry
on 4401 — a wrong token will not fix itself. All other disconnects keep the
current exponential backoff reconnect logic.

**API**: `websockets.exceptions.ConnectionClosedError` has `.rcvd` (`Frames`)
attribute. When server calls `ws.close(code=4401)`, `.rcvd.code == 4401` on
the client side.

**Exception class**: `class AuthError(Exception): pass` defined in `client/ws_client.py`;
imported by `risus.py`.

---

## Scheme Detection Heuristic (FR-006)

**Decision**: `":" in server` → `ws://`, else → `wss://`.

**Rationale**: `"localhost:8765"` contains a colon; `"risus.boos.systems"`
does not. IPv6 addresses (`[::1]:8765`) also contain a colon and should use
plain WS for local dev. The spec acceptance criteria (US4) use exactly this
heuristic.

**Alternative rejected**: Regex on hostname — over-engineered for this use case.

---

## load_battle() URL Derivation

**Current** (broken for wss://):

```python
server_base = ws._uri.replace("ws://", "http://").rsplit("/ws/", 1)[0]
```

`wss://risus.boos.systems/ws/Conan` → `ws://risus.boos.systems/ws/Conan`
(broken — ws:// not replaced).

**Fixed**:

```python
server_base = (
    ws._uri
    .replace("wss://", "https://")
    .replace("ws://", "http://")
    .rsplit("/ws/", 1)[0]
)
```

Replace `wss://` first, then `ws://` — avoids double-replace.

---

## Token Validation in Client (FR-003)

**Decision**: Dedicated `_prompt_token(saved: str | None) -> str` function in `risus.py`.

**Rules**:

- Min 16 printable non-whitespace characters (reject shorter with informative
  message)
- Empty input with a `saved` default → use saved (normal `_prompt_required`
  behaviour)
- Empty input with no default → re-prompt

**Re-prompt on rejection**: When server returns 4401, `connect_or_die`
catches `AuthError`, clears the token (no default), and calls
`_prompt_token(None)` before retrying. The rejected token is not shown as a
default.

---

## Server Logging (FR-009)

**Decision**: Use Python stdlib `logging` (module-level logger
`logger = logging.getLogger(__name__)`).

**Format**: `logger.warning("ws auth rejected: %s reason=%s", client_ip,
reason)` where `reason` is `"token_absent"` or `"token_mismatch"`. Token
value MUST NOT appear.

**`client_ip`**: Available as `ws.client.host` in FastAPI/Starlette WebSocket.

---

## docker-compose.yml Changes

**Server binding**: Change `ports: "8765:8765"` → `"127.0.0.1:8765:8765"`
so the raw port is not reachable from outside the host.

**Token env**: `RISUS_TOKEN: ${RISUS_TOKEN}` — standard compose env-var substitution.
Compose raises an error if `RISUS_TOKEN` is unset and no default is specified. Acceptable:
operators must set the token explicitly (spec: secure by default).

**Caddy service**: `network_mode: host` lets Caddy reach `127.0.0.1:8765` directly.
Ports 80/443 are bound by Caddy on the host network. Volumes: `./Caddyfile` and
`caddy_data` for Let's Encrypt cert persistence.

---

## Alternatives Considered

| Question | Chosen | Rejected |
| -------- | ------ | -------- |
| Token in query string vs. header | Query string | Custom header — not portable in WS handshake |
| Delay before or after check | Before (uniform) | After — creates timing oracle |
| 4401 in WSClient: raise vs. frame | Raise `AuthError` in `start()` | Caller checking inbox — leaks protocol detail |
| Reconnect on 4401 | No reconnect | Reconnect — wrong token won't fix itself |
