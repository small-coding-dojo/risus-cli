# Contributing to Risus CLI

## Prerequisites

- Python 3.12+
- One container runtime:
  - **Docker**: Docker Engine 24+ with the Compose plugin (`docker compose`)
  - **Podman**: Podman 4.7+ (`podman-compose` is installed via `.[dev]` below)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

This installs all development tools including `podman-compose`, `ruff`, and `pytest`.

### Rootless Podman (optional)

For rootless Podman, expose the socket so `pytest-docker` can reach it:

```bash
systemctl --user start podman.socket
export DOCKER_HOST=unix:///run/user/$UID/podman/podman.sock
```

---

## Bring Up the Stack

The server requires a `RISUS_TOKEN` environment variable. Clients must supply the same token to connect.

```bash
export RISUS_TOKEN=your-secret-token-here   # min 16 chars
```

**Docker:**
```bash
docker compose up -d --build
```

**Podman:**
```bash
PATH=$PWD/.venv/bin:$PATH CONTAINER_ENGINE=podman podman-compose up -d --build
```

Both commands build the server image and start `db` (Postgres 16) and `server` (FastAPI on port 8765). Verify:

```bash
curl http://localhost:8765/healthz
# → {"ok":true}
```

---

## Run the CLI

```bash
python risus.py
```

You'll be prompted for server address, display name, and session token. Supply the same `RISUS_TOKEN` value set when starting the stack.

Pass values directly to skip prompts:

```bash
python risus.py localhost:8765 MyName --token your-secret-token-here
```

Token is saved to `risus.cfg` after a successful connection and reused on the next launch.

### Connecting

- Name must be unique per session. If a name is already connected the server closes your WebSocket with code `4409 "name in use"`. Choose a different name or wait ~30 s for the prior session's keepalive to expire.

### Reconnecting

- On reconnect, you start fresh. Any lock you held before the drop is released server-side; you must re-acquire it explicitly.

### CLI UX Limitation

> Remote changes appear after your next keypress, not mid-prompt.

The menu uses blocking `input()` to preserve the original single-player UX. While you're sitting at a prompt, changes from other clients accumulate in a queue and are rendered the next time the menu redraws (after you press Enter). This is intentional.

### Spectating

Any connected client receives all state/presence/lock broadcasts. To spectate, just connect and never lock or edit anything.

---

## Run Tests

### Unit tests (no containers required)

**Docker:**
```bash
pytest tests/unit -q
```

**Podman:**
```bash
pytest tests/unit -q
```

Unit tests are identical for both runtimes — no container dependency.

### E2E tests (require running containers)

**Docker:**
```bash
CONTAINER_ENGINE=docker RISUS_TOKEN=testtoken pytest tests/e2e -m e2e -q
```

**Podman:**
```bash
PATH=$PWD/.venv/bin:$PATH CONTAINER_ENGINE=podman RISUS_TOKEN=testtoken pytest tests/e2e -m e2e -q
```

E2E tests spin up and tear down the full stack automatically using the project's `docker-compose.yml`. `RISUS_TOKEN` is required — the server rejects connections without it.

For rootless Podman, also export:
```bash
export DOCKER_HOST=unix:///run/user/$UID/podman/podman.sock
```

---

## Reset State

Destroy all containers and volumes (wipes the database):

**Docker:**
```bash
docker compose down -v
```

**Podman:**
```bash
PATH=$PWD/.venv/bin:$PATH podman-compose down -v
```

> **Note:** Schema changes require `down -v` because Postgres initialises the schema on first boot from `server/schema.sql`. A running volume will not re-initialise.

---

## Code Style & Commit Conventions

- Format: `black` (or equivalent)
- Commits: [Conventional Commits](https://www.conventionalcommits.org/) — `feat:`, `fix:`, `test:`, `docs:`, `chore:`
- See `AGENTS.md` for AI-agent rules and the hand-off checklist

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| "Connection rejected: invalid or missing token" | Token mismatch — ensure client `--token` matches `RISUS_TOKEN` on the server |
| Port 8765 already in use | `PATH=$PWD/.venv/bin:$PATH podman-compose down` or stop whatever owns 8765 |
| Podman SELinux mount error | Add `:Z` to the volume mount in `docker-compose.yml` for the SQL file |
| Schema init didn't run | Volume already exists; run `down -v` then `up -d` again |
| WS close code `4409 name in use` | Another client is already connected with that name; wait ~30 s or use a different name |
| E2E tests time out on CI | Ensure Docker daemon socket is accessible; for rootless Podman set `DOCKER_HOST` |
