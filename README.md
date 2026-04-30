# Risus CLI — Multiplayer Battle Tracker

A multiplayer CLI battle tracker for the [Risus RPG](http://www.risusiverse.com/) system. Multiple players connect from separate terminals to a shared server and manage a single battle in real time.

## Features

- Shared battle state — all clients see the same players and dice counts
- Per-player edit locks — prevents two players from editing the same character simultaneously
- Named server-side save/load — battle snapshots persist across sessions
- Presence indicator — see who else is connected

## Quickstart

See [CONTRIBUTING.md](CONTRIBUTING.md) for full setup, running, and testing instructions.

```bash
# Start the stack
podman-compose up -d   # or: docker compose up -d

# Run the CLI (in each terminal)
python risus.py
# → Server address [localhost:8765]: 
# → Your name: Alice
```

## Architecture

```
risus.py (CLI)  ◄── WebSocket ──►  risus-server (FastAPI)  ◄── SQL ──►  Postgres 16
```

- `risus-server`: FastAPI app on port 8765, WebSocket endpoint `/ws/{name}`, REST at `/state`, `/saves`, `/healthz`
- `Postgres`: stores players, locks (audit), and named saves
- `risus.py`: thin WS client; all state comes from server broadcasts

## Features

Specifications and design for features are stored in [docs/features](./docs/features).

## For AI Agents

See [AGENTS.md](AGENTS.md) for project rules, file layout, WS protocol reference, and the hand-off checklist.
