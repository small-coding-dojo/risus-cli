# AGENTS.md — AI Agent Rules for Risus CLI

This file is the runtime companion to `.specify/memory/constitution.md`.
The constitution is ground truth for principles, tech stack, workflow, and
quality gates; this file covers operational detail not appropriate for the
constitution.

A fresh clone plus the constitution plus this file is enough context to
continue the project.

---

## Collaboration with the User

- **Language**: chat is in English.
- **One question at a time**: when asking the user a question, ask one
  question at a time so they can focus.
- **Avoid ambiguity**: if instructions are unclear, contradictory, or
  conflict with rules or earlier instructions, describe the situation and
  ask clarifying questions before proceeding.
- **Custom instructions**: when the user says "follow your custom
  instructions", use the `/memory-bank-by-cline` skill to understand the
  memory bank concept. If no memory bank exists, ask for clarification.
  Otherwise read the memory bank, identify the next action, read the
  applicable rules, summarize understanding ending with the next immediate
  action, then ask whether to execute it.
- **Hidden files**: the LS tool does not show hidden files; use
  `ls -la <path>` via Bash to check for hidden files or directories.

---

## Project at a Glance

Risus CLI is a multiplayer battle tracker for the Risus RPG system. Multiple
CLI clients connect to a shared FastAPI server backed by Postgres. All battle
state is server-authoritative; the CLI is a thin renderer. Locks coordinate
concurrent edits to the same player.

---

## Where Things Live

```text
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

The constitution defines the automated quality gate. In addition, run the
manual smoke checklist on a clean clone:

- `python risus.py` shows startup prompts and connects
- Two terminals running `python risus.py` see the same state and
  `Connected:` line
- One client locks a player; the other sees the lock indicator and gets
  `lock_denied`
- `podman-compose restart server` preserves player state; clients reconnect
- Dropping a client (`Ctrl+C`) frees its locks within ~30 s

---

## Operational Rules

The constitution defines the non-negotiable principles (server authority,
simplicity, no duplication, testing discipline, no local persistence). The
items below are the operational specifics that implement those principles:

1. **Lock-holder check**: `switch_cliche` and `reduce_dice` handlers verify
   `LockManager.holder(player_name) == caller_client_id` and return an
   `error` frame on violation. Locks are never decorative.
2. **One lock store**: `LockManager` (in-memory) is authoritative. The
   `locks` DB table is an audit log, truncated on server startup. Locks do
   NOT survive server restart.
3. **Error frame shape**: `{"type": "error", "message": "<string>"}`.

For workflow steps and Conventional Commits formatting, see the
constitution's "Development Workflow" section.

---

## WS Protocol Reference

### Client → Server

| type | key fields | lock required? |
| --- | --- | --- |
| `add_player` | `name, cliche, dice` | No |
| `switch_cliche` | `player_name, cliche, dice` | Yes |
| `reduce_dice` | `player_name, amount, is_dead` | Yes |
| `lock` | `player_name` | — |
| `unlock` | `player_name` | — |
| `save` | `save_name` | No |
| `load` | `save_name` | No |

### Server → Client (broadcast unless noted)

| type | key fields | notes |
| --- | --- | --- |
| `state` | `players: [{name, cliche, dice, lost_dice}]` | Full sync |
| `presence` | `clients: [names]` | Connected users |
| `lock_acquired` | `player_name, locked_by` | Broadcast |
| `lock_released` | `player_name` | Broadcast |
| `lock_denied` | `player_name, locked_by` | Caller only |
| `error` | `message` | Caller only |

---

## PRD Acceptance Criteria → Tests

| AC | Criterion | Test |
| --- | --- | --- |
| AC1 | Two clients see state within 1 s | `e2e::test_state_propagates_within_one_second` |
| AC2 | Lock blocks concurrent edit | `e2e::test_lock_blocks_concurrent_edit` + `unit::test_switch_cliche_rejects_without_lock` |
| AC3 | State survives server restart | `e2e::test_state_survives_server_restart` |
| AC4 | Named save/load from any client | `e2e::test_named_save_load` |
| AC5 | Disconnect releases locks | `e2e::test_locks_freed_on_disconnect` + `e2e::test_lock_freed_within_30s` |
| AC6 | `docker compose up` starts clean | `e2e::test_stack_starts_clean` |

---

## Hand-Off Checklist (for PR description)

- [ ] `pytest tests/unit -q` — all passing, count reported
- [ ] `CONTAINER_ENGINE=podman pytest tests/e2e -m e2e -q` — all passing,
      count reported
- [ ] `podman-compose up -d && curl -fsS http://localhost:8765/healthz` —
      returns `{"ok":true}`
- [ ] Each AC above maps to a named passing test
- [ ] `CONTRIBUTING.md` and `AGENTS.md` updated if any new setup step was added

<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:ca08a54f -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see
full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or
  markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

## Session Completion

**When ending a work session**, you MUST complete ALL steps below. Work is NOT
complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs
   follow-up
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
