# Data Model: Secure Session

## Entities

### Session Token

Shared secret used to authenticate WebSocket connections.

| Field | Type   | Constraints                                            |
|-------|--------|--------------------------------------------------------|
| value | string | Min 16 printable non-whitespace characters; no max len |

**Lifecycle**: Set by operator via `RISUS_TOKEN` environment variable on server
startup. Distributed out-of-band to players. Never stored on the server beyond
the env var. Never logged.

**State transitions**: None — static for the lifetime of a server deployment.

---

### Client Configuration (extended)

Persistent INI file (`risus.cfg`) in the client's base directory. Stores the
player's last-used connection parameters across launches.

| Key    | Type   | Section   | Constraints                                    |
|--------|--------|-----------|------------------------------------------------|
| server | string | `[risus]` | host:port or bare hostname                     |
| name   | string | `[risus]` | Non-empty display name                         |
| token  | string | `[risus]` | Min 16 printable non-whitespace chars; absent  |
|        |        |           | if never entered                               |

**Read** (`read_config`): Returns `(server, name, token)` — any field is `None`
if absent.
**Write** (`write_config`): Persists all three fields atomically via
`configparser`.
**On rejection**: Token is not saved when connection is rejected with 4401. New
token from re-prompt is saved only on successful connection (atexit).

---

### WebSocket Connection Request (extended)

| Parameter | Location     | Value                          |
|-----------|--------------|--------------------------------|
| name      | URL path     | `ws[s]://{server}/ws/{name}`   |
| token     | Query string | `?token={value}`               |

The token travels inside TLS when using `wss://`. FastAPI reads it via
`websocket.query_params.get("token")`.

---

### Server Validation State (transient)

Not persisted. Evaluated per-connection in `handle()` before the session is
established.

| Check                                 | Result                        |
|---------------------------------------|-------------------------------|
| `RISUS_TOKEN` env var absent or empty | Close 4401 — `token_absent`   |
| `?token` query param absent           | Close 4401 — `token_absent`   |
| `?token` value != `RISUS_TOKEN`       | Close 4401 — `token_mismatch` |
| All checks pass                       | Session proceeds              |

**Invariant**: 3-second `asyncio.sleep` executes before any check result is
acted on, for all connection attempts regardless of outcome.
