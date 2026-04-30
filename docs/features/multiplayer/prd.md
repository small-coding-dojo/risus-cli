# PRD: Risus CLI — Multiplayer Increment

## Goal

Multiple CLI clients connect to shared infrastructure and manipulate a single battle state in real time.

---

## Constraints

- Existing CLI UX (`risus.py`) preserved — menu flow unchanged.
- No authentication. Any client may connect.
- Docker Compose hosts all infrastructure.

---

## User Stories

1. **Connect** — User launches CLI, enters a display name, and connects to the server. No password.
2. **Shared view** — All connected clients see the same battle state. When any client changes state, all others update within ~1 second.
3. **Safe edit** — When a client begins editing a player (reduce dice, switch cliche, add player), that player is locked. Other clients see the lock. Lock releases on action completion or client disconnect.
4. **Persistence** — Battle state survives server restart (stored in Postgres). Save/load is server-side only; no local JSON export.
5. **Presence** — CLI shows list of currently connected users.

---

## Architecture

### Components

```
┌─────────────┐     WebSocket      ┌──────────────────┐     SQL      ┌──────────────┐
│  risus.py   │ ◄────────────────► │  risus-server    │ ◄──────────► │  Postgres    │
│  (CLI)      │                    │  (FastAPI)        │              │              │
└─────────────┘                    └──────────────────┘              └──────────────┘
```

- **risus-server**: FastAPI app with WebSocket endpoint + REST fallback for initial state load.
- **Postgres**: Single `battle_state` table + `locks` table.
- **risus.py**: Gains WebSocket client; menu actions send commands to server instead of mutating local state.

### Docker Compose services

| Service | Image | Port |
|---|---|---|
| `server` | Python 3.12 / FastAPI | 8765 |
| `db` | postgres:16 | 5432 (internal) |

---

## API Design

### WebSocket `/ws/{client_name}`

All messages are JSON with a `type` field.

#### Client → Server

| type | payload | description |
|---|---|---|
| `add_player` | `name, cliche, dice` | Add player to battle |
| `switch_cliche` | `player_name, cliche, dice` | Change player cliche/dice |
| `reduce_dice` | `player_name, amount, is_dead` | Reduce dice or mark dead |
| `lock` | `player_name` | Acquire edit lock |
| `unlock` | `player_name` | Release edit lock |
| `save` | `save_name` | Persist named snapshot server-side |
| `load` | `save_name` | Restore named snapshot |

#### Server → Client (broadcast)

| type | payload | description |
|---|---|---|
| `state` | full battle state | Full sync on connect or after any mutation |
| `lock_acquired` | `player_name, locked_by` | Broadcast when lock taken |
| `lock_released` | `player_name` | Broadcast when lock freed |
| `lock_denied` | `player_name, locked_by` | Sent only to requester when lock unavailable |
| `presence` | `[client_names]` | Connected user list |
| `error` | `message` | Command rejected |

### REST

| Method | Path | Description |
|---|---|---|
| `GET` | `/state` | Current battle state (HTTP, for initial load) |
| `GET` | `/saves` | List saved snapshots |

---

## Data Model (Postgres)

```sql
-- Active battle (single shared state)
CREATE TABLE players (
    name        TEXT PRIMARY KEY,
    cliche      TEXT NOT NULL DEFAULT '',
    dice        INTEGER,          -- NULL = unknown
    lost_dice   INTEGER NOT NULL DEFAULT 0
);

-- Edit locks
CREATE TABLE locks (
    player_name TEXT PRIMARY KEY REFERENCES players(name) ON DELETE CASCADE,
    locked_by   TEXT NOT NULL,
    acquired_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Named snapshots
CREATE TABLE saves (
    save_name   TEXT NOT NULL,
    saved_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    data        JSONB NOT NULL,
    PRIMARY KEY (save_name)
);
```

---

## CLI Changes (`risus.py`)

- New startup prompt: `Server address (default: localhost:8765):` and `Your name:`.
- WebSocket connection established before main menu.
- Local `Battle` object replaced by server-authoritative state received via WebSocket.
- All menu actions send a command message; UI updates only on `state` broadcast from server.
- Before editing a player, CLI sends `lock`; if `lock_denied` received, shows `"[name] is being edited by [user]"` and returns to menu.
- Presence line added above battle state: `Connected: Alice, Bob`.
- Save/load menu items call server-side save/load commands; local file I/O removed.
- On disconnect/reconnect, CLI re-sends connect and re-receives full state.

---

## Out of Scope

- Auth / roles / GM permissions
- Multiple concurrent battles
- Local JSON export/import
- CLI config file (server address passed at startup only)

---

## Acceptance Criteria

- [ ] Two CLI clients on same LAN both reflect state changes within 1 second.
- [ ] Lock prevents second client from editing same player until first finishes.
- [ ] Battle state survives `docker compose restart server`.
- [ ] Named save/load works from any client.
- [ ] Client disconnect releases all locks held by that client.
- [ ] `docker compose up` starts fully working stack with no manual steps.
