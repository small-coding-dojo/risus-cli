# AGENTS.md — AI Agent Rules for Risus CLI

This file is self-contained. A fresh clone plus this file is enough context to continue the project.

---

## Project at a Glance

Risus CLI is a multiplayer battle tracker for the Risus RPG system. Multiple CLI clients connect to a shared FastAPI server backed by Postgres. All battle state is server-authoritative; the CLI is a thin renderer. Locks coordinate concurrent edits to the same player.

---

## Where Things Live

```
risus.py              CLI entry point — thin client over WebSocket
client/
  ws_client.py        asyncio WS client; background thread + two queues
  state.py            ClientState — thread-safe mirror of server state
server/
  app.py              FastAPI factory + lifespan (opens DB pool, starts WS endpoint)
  ws.py               ConnectionManager — WS routing, disconnect/lock handling
  commands.py         One async handler per WS message type
  locks.py            LockManager — in-memory, authoritative, session-scoped
  db.py               asyncpg pool + query helpers
  rest.py             GET /state, /saves, /healthz
  models.py           Pydantic message models
  schema.sql          Postgres schema (mounted via Docker initdb.d)
docker/
  server.Dockerfile   Server image build
docker-compose.yml    Stack definition (db + server)
tests/
  unit/               Fast tests — mocked DB, no containers
  e2e/                Container tests — real stack via podman-compose/docker compose
CONTRIBUTING.md       Setup, running, testing, troubleshooting
AGENTS.md             This file
```

---

## Definition of Done

A change is ready for review when ALL of the following pass on a clean clone:

```bash
pytest tests/unit -q
CONTAINER_ENGINE=podman pytest tests/e2e -m e2e -q
podman-compose up -d && curl -fsS http://localhost:8765/healthz
```

Plus the manual smoke checklist:
- `python risus.py` shows startup prompts and connects
- Two terminals running `python risus.py` see the same state and `Connected:` line
- One client locks a player; the other sees the lock indicator and gets `lock_denied`
- `podman-compose restart server` preserves player state; clients reconnect
- Dropping a client (`Ctrl+C`) frees its locks within ~30 s

---

## Hard Rules

1. **Server is the only source of truth.** Never mutate `ClientState` locally and hope the server agrees. All mutations go through WS commands.
2. **Preserve menu UX.** Options 1–6 labels, prompts, and ordering must not change. The `input()` calls must stay synchronous (no `prompt_toolkit`).
3. **No local JSON file I/O.** Save/load are server-side operations only.
4. **Lock enforcement is server-side.** `switch_cliche` and `reduce_dice` handlers verify `LockManager.holder(player_name) == caller_client_id` and return an `error` frame on violation. Locks are never decorative.
5. **One lock store.** `LockManager` (in-memory) is authoritative. The `locks` DB table is an audit log, truncated on server startup. Locks do NOT survive server restart.
6. **Docker and Podman are equal peers.** Every command in docs appears for both runtimes. No "or Podman" footnotes.
7. **No auth, no multiple battles.** Out of scope per PRD. Do not add authentication or multi-battle support.

---

## Workflow

1. Branch from `main`: `git checkout -b feat/my-change`
2. Make changes
3. Run unit tests: `pytest tests/unit -q`
4. Start stack and run e2e: `podman-compose up -d && CONTAINER_ENGINE=podman pytest tests/e2e -m e2e -q`
5. Commit with Conventional Commits format: `feat: add X`, `fix: Y`, `test: cover Z`
6. Open PR

---

## WS Protocol Reference

### Client → Server

| type | key fields | lock required? |
|---|---|---|
| `add_player` | `name, cliche, dice` | No |
| `switch_cliche` | `player_name, cliche, dice` | Yes |
| `reduce_dice` | `player_name, amount, is_dead` | Yes |
| `lock` | `player_name` | — |
| `unlock` | `player_name` | — |
| `save` | `save_name` | No |
| `load` | `save_name` | No |

### Server → Client (broadcast unless noted)

| type | key fields | notes |
|---|---|---|
| `state` | `players: [{name, cliche, dice, lost_dice}]` | Full sync |
| `presence` | `clients: [names]` | Connected users |
| `lock_acquired` | `player_name, locked_by` | Broadcast |
| `lock_released` | `player_name` | Broadcast |
| `lock_denied` | `player_name, locked_by` | Caller only |
| `error` | `message` | Caller only |

Error frame shape: `{"type": "error", "message": "<string>"}`

---

## PRD Acceptance Criteria → Tests

| AC | Criterion | Test |
|---|---|---|
| AC1 | Two clients see state within 1 s | `e2e::test_state_propagates_within_one_second` |
| AC2 | Lock blocks concurrent edit | `e2e::test_lock_blocks_concurrent_edit` + `unit::test_switch_cliche_rejects_without_lock` |
| AC3 | State survives server restart | `e2e::test_state_survives_server_restart` |
| AC4 | Named save/load from any client | `e2e::test_named_save_load` |
| AC5 | Disconnect releases locks | `e2e::test_locks_freed_on_disconnect` + `e2e::test_lock_freed_within_30s` |
| AC6 | `docker compose up` starts clean | `e2e::test_stack_starts_clean` |

---

## Hand-Off Checklist (for PR description)

- [ ] `pytest tests/unit -q` — all passing, count reported
- [ ] `CONTAINER_ENGINE=podman pytest tests/e2e -m e2e -q` — all passing, count reported
- [ ] `podman-compose up -d && curl -fsS http://localhost:8765/healthz` — returns `{"ok":true}`
- [ ] Each AC above maps to a named passing test
- [ ] `CONTRIBUTING.md` and `AGENTS.md` updated if any new setup step was added

<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:ca08a54f -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

## Session Completion

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd dolt push
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
<!-- END BEADS INTEGRATION -->
