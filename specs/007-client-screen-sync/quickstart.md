# Quickstart: Testing Automatic Client Screen Refresh

**Feature**: 007-client-screen-sync  
**Date**: 2026-05-04

## Prerequisites

- Stack running: `podman-compose up -d` (or `docker compose up -d`)
- Virtual env active: `source .venv/bin/activate`
- Verify health: `curl -fsS http://localhost:8765/healthz` → `{"ok":true}`

## Manual Smoke Test

Open **two terminals**, both in the repo root with the venv active.

**Terminal A** (observer — leave at main menu):
```bash
python risus.py
# Enter name when prompted: Alice
# Leave at the main menu (do not press any keys)
```

**Terminal B** (actor):
```bash
python risus.py
# Enter name when prompted: Bob
# Select option 1 (Add player), enter a player name and cliché
```

**Expected**: Within 2 seconds of Bob adding a player, Alice's terminal automatically redraws and shows the new player — without Alice pressing any key.

**Lock refresh test**:
- From Terminal B: select a player to edit (acquires lock)
- **Expected**: Alice's terminal shows the lock indicator for that player automatically

## Automated Tests

### Unit tests (no containers)

```bash
pytest tests/unit/test_state_refresh.py -v
```

Expected tests:
- `test_apply_state_sets_update_event` — `state` frame sets event
- `test_apply_presence_sets_update_event` — `presence` frame sets event
- `test_apply_lock_acquired_sets_update_event` — `lock_acquired` frame sets event
- `test_apply_lock_released_sets_update_event` — `lock_released` frame sets event
- `test_update_event_starts_clear` — event not set on fresh `ClientState()`

### E2E tests (requires real stack)

```bash
PATH=$PWD/.venv/bin:$PATH CONTAINER_ENGINE=podman pytest tests/e2e/test_auto_refresh.py -m e2e -v
```

Expected test:
- `test_state_change_visible_on_second_client_within_2s` — client A adds player; client B output contains player within 2s

### Full quality gate

```bash
pytest tests/unit -q

# Podman:
PATH=$PWD/.venv/bin:$PATH CONTAINER_ENGINE=podman pytest tests/e2e -m e2e -q
podman-compose up -d && curl -fsS http://localhost:8765/healthz

# Docker:
CONTAINER_ENGINE=docker pytest tests/e2e -m e2e -q
docker compose up -d && curl -fsS http://localhost:8765/healthz
```

## Verifying No Regression

Run the full PRD acceptance criteria suite:

```bash
PATH=$PWD/.venv/bin:$PATH CONTAINER_ENGINE=podman pytest tests/e2e -m e2e -q
```

All 6 ACs (AC1–AC6 in `AGENTS.md`) must remain green. AC1 (`test_state_propagates_within_one_second`) is most relevant to this feature.
