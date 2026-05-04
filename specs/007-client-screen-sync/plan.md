# Implementation Plan: Automatic Client Screen Refresh

**Branch**: `007-client-screen-sync` | **Date**: 2026-05-04 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `specs/007-client-screen-sync/spec.md`

## Summary

When the server broadcasts a state change (player update, lock event), the CLI client must automatically refresh the battle display without requiring user input. The current architecture already updates `ClientState` in the background thread on every incoming frame but never signals the main thread. This plan adds a lightweight dirty-flag mechanism to `ClientState` and replaces the single blocking `input()` call in the main menu loop with a polling variant that redraws the screen on timeout when state has changed.

## Technical Context

**Language/Version**: Python 3.12+  
**Primary Dependencies**: stdlib only — `threading`, `select`, `asyncio`, `websockets`  
**Storage**: No local state; server-authoritative via Postgres (no change)  
**Testing**: pytest 8+ — unit (no containers), E2E (real stack via podman-compose/docker compose)  
**Target Platform**: Linux/macOS terminal (client); Linux container (server)  
**Project Type**: CLI client + FastAPI server  
**Performance Goals**: State changes visible on all clients within 2 seconds of server broadcast  
**Constraints**: `input()` calls MUST remain synchronous; no `prompt_toolkit` or async input libraries; no local persistence; menu UX (options 1–6) MUST NOT change  
**Scale/Scope**: Single shared session; small number of concurrent CLI clients (PRD)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Server Authority | PASS | No local state mutations; only display update; server remains sole source of truth |
| II. Simplicity | PASS | Minimal scope: one new `threading.Event` on `ClientState`, one helper function in `risus.py`; no new libraries; menu UX unchanged. `_input_with_refresh()` replaces `input()` with a synchronous stdlib-only wrapper — explicitly permitted by constitution v1.1.1 |
| III. No Duplication | PASS | `show_state()` reused as-is; no new display logic |
| IV. Testing Discipline | PASS | Unit tests for new dirty-flag behavior; E2E test covers AC1 (state propagation) |
| V. No Local Persistence | PASS | No file/JSON I/O introduced |

No violations. No Complexity Tracking entries required.

## Project Structure

### Documentation (this feature)

```text
specs/007-client-screen-sync/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── ws-refresh-triggers.md   # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (files changed by this feature)

```text
client/
  state.py          # Add update_event: threading.Event; set it in apply()
risus.py            # Replace input("> ") in main loop with _input_with_refresh()

tests/
  unit/
    test_state_refresh.py     # New: dirty-flag unit tests
  e2e/
    test_auto_refresh.py      # New: end-to-end display refresh test
```

**Structure Decision**: Single-project layout (existing). Only two source files modified; two test files added. All existing files untouched.

## Implementation Phases

### Phase 0 → Research

See [research.md](research.md) — all unknowns resolved.

### Phase 1 → Design & Contracts

See:
- [data-model.md](data-model.md) — `ClientState` additions and data flow
- [contracts/ws-refresh-triggers.md](contracts/ws-refresh-triggers.md) — which WS frames trigger a refresh
- [quickstart.md](quickstart.md) — how to test manually and run automated tests

### Implementation Steps (for /speckit-tasks)

1. **`client/state.py`** — Add `update_event: threading.Event` to `__init__`; call `self.update_event.set()` at the end of every branch in `apply()`.

2. **`risus.py`** — Add `_input_with_refresh(prompt: str) -> str` helper that polls `stdin` via `select.select` with a 1-second timeout; on timeout, checks `_ws().state.update_event.is_set()`, and if set: clears event, prints newline, calls `show_state()`, reprints prompt. Replace the single `choice = input("> ")` call in `main()` (inside the top-level menu loop) with `choice = _input_with_refresh("> ")`. All other `input()` calls (inside submenus) are left unchanged.

3. **`tests/unit/test_state_refresh.py`** — Tests: `apply("state", ...)` sets `update_event`; `apply("presence", ...)` sets `update_event`; `apply("lock_acquired", ...)` sets `update_event`; `apply("lock_released", ...)` sets `update_event`; event is clear after `update_event.clear()`.

4. **`tests/e2e/test_auto_refresh.py`** — E2E test: launch two client processes; client A sends a state-changing command; assert client B's process output reflects the change within 2 seconds (leverages existing container stack).

5. **`AGENTS.md`** — Add note to WS Protocol Reference that `state`, `presence`, `lock_acquired`, `lock_released` frames trigger `update_event` in `ClientState.apply()`.
