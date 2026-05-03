# Contract: WebSocket Token Authentication

## Connection URI

```text
ws[s]://{server}/ws/{name}?token={session_token}
```

| Part      | Rule                                                             |
| --------- | ---------------------------------------------------------------- |
| scheme    | `ws://` when server contains `:` (host:port); `wss://` otherwise |
| `{name}`  | Player display name (unchanged from prior spec)                  |
| `?token=` | Required query parameter; value is the shared session token      |

---

## Server Behaviour

### Handshake sequence

```text
Client                        Server
  |── WS Upgrade ──────────────>|
  |                             |  await ws.accept()
  |                             |  await asyncio.sleep(3)   ← FR-010 delay (all connections)
  |                             |  validate token
  |  if invalid ────────────────|
  |<── Close(4401, "unauthorized") ──|
  |  if valid ──────────────────|
  |<── StateMsg ────────────────|
  |<── PresenceMsg ─────────────|
```

### Close codes

| Code | Reason string    | Meaning                               |
| ---- | ---------------- | ------------------------------------- |
| 4401 | `"unauthorized"` | Token absent, empty, or wrong         |
| 4409 | `"name in use"`  | Duplicate display name (pre-existing) |

### Logging on rejection

```text
WARNING  server.ws: ws auth rejected: {client_ip} reason={reason}
```

- `reason` is exactly `token_absent` or `token_mismatch`
- Token value MUST NOT appear in any log line

---

## Client Behaviour

### Token resolution (in priority order)

1. `--token` CLI argument
2. Stored value in `risus.cfg` `[risus] token`
3. Interactive prompt (`_prompt_token`)

### Token validation at prompt

- Empty input with saved value → use saved value
- Empty input with no saved value → re-prompt
- Value shorter than 16 printable non-whitespace characters →
  reject with message, re-prompt

### On receiving Close(4401)

- `WSClient.start()` raises `AuthError`
- `connect_or_die()` catches `AuthError`, clears saved token, re-prompts player
- New token is NOT saved until next successful connection (atexit)
- `WSClient` does NOT attempt reconnection after 4401

---

## Environment Variable

| Variable      | Required     | Description                                                  |
| ------------- | ------------ | ------------------------------------------------------------ |
| `RISUS_TOKEN` | Yes (server) | Shared session secret; min 16 printable non-whitespace chars |

Server rejects ALL connections when `RISUS_TOKEN` is unset or empty (FR-002).
