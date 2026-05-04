---
description: "Task list for automatic client screen refresh"
---

# Tasks: Automatic Client Screen Refresh

**Input**: Design documents from `specs/007-client-screen-sync/`  
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Included — required by constitution (Testing Discipline, Principle IV).

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no incomplete dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Add dirty-flag mechanism to `ClientState`. All user stories depend on this.

**Note**: `tests/unit/` and `tests/e2e/` are pre-existing directories — no setup required.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T001 Add `update_event: threading.Event` field initialized in `ClientState.__init__()` in `client/state.py`
- [x] T002 Call `self.update_event.set()` at the end of every branch in `ClientState.apply()` (after `state`, `presence`, `lock_acquired`, `lock_released` updates) in `client/state.py`

**Checkpoint**: `ClientState.update_event` exists and is set by every incoming frame type. Unit tests can now be written.

---

## Phase 2: User Story 1 — Automatic State Refresh (Priority: P1) 🎯 MVP

**Goal**: Connected clients see battle state changes from other players within 2 seconds, without pressing any key.

**Independent Test**: Open two clients. From client B, add a player. Client A's screen redraws automatically within 2 seconds.

### Tests for User Story 1

- [x] T003 [P] [US1] Write unit test `test_apply_state_sets_update_event` — assert event is set after `state` frame in `tests/unit/test_state_refresh.py`
- [x] T004 [P] [US1] Write unit test `test_apply_presence_sets_update_event` — assert event is set after `presence` frame in `tests/unit/test_state_refresh.py`
- [x] T005 [P] [US1] Write unit test `test_update_event_starts_clear` — assert fresh `ClientState()` has event not set in `tests/unit/test_state_refresh.py`
- [x] T006 [P] [US1] Write unit test `test_rapid_apply_no_updates_dropped` — call `apply()` with 10 distinct `state` frames in rapid succession; assert final `ClientState.players` reflects last frame and `update_event` is set; validates SC-003 in `tests/unit/test_state_refresh.py`
- [x] T007 [P] [US1] Write unit test `test_input_with_refresh_redraws_on_timeout` — mock `select.select` to return timeout on first call and ready-stdin on second; mock `show_state()`; assert `show_state()` called once and prompt reprinted in `tests/unit/test_state_refresh.py`

### Implementation for User Story 1

- [x] T008 [US1] Add `_input_with_refresh(prompt: str) -> str` helper to `risus.py` — uses `select.select([sys.stdin], [], [], 1.0)` loop; on timeout checks `_ws().state.update_event.is_set()`; if set: clears event, prints newline, calls `show_state()`, reprints prompt; returns stripped line when stdin is ready. Add inline comment citing constitution v1.1.1 synchronous-wrapper exemption.
- [x] T009 [US1] Replace the single `choice = input("> ")` call inside the top-level menu loop in `main()` with `choice = _input_with_refresh("> ")` in `risus.py` (all other `input()` calls in submenus are left unchanged)
- [x] T010 [US1] Run unit tests and confirm T003–T007 pass: `pytest tests/unit/test_state_refresh.py -v`

**Checkpoint**: US1 fully functional. Client A auto-refreshes when client B modifies state. All US1 tests green.

---

## Phase 3: User Story 2 — Live Lock Status Visibility (Priority: P2)

**Goal**: Lock acquisition and release events appear automatically on all clients.

**Independent Test**: From one client, acquire a lock. A second client's screen shows the lock indicator automatically within 2 seconds.

**Note**: No new implementation — lock frames already covered by T002 (`lock_acquired`, `lock_released` set `update_event`). This phase adds tests to confirm.

### Tests for User Story 2

- [x] T011 [P] [US2] Write unit test `test_apply_lock_acquired_sets_update_event` in `tests/unit/test_state_refresh.py`
- [x] T012 [P] [US2] Write unit test `test_apply_lock_released_sets_update_event` in `tests/unit/test_state_refresh.py`
- [x] T013 [US2] Run unit tests and confirm T011–T012 pass: `pytest tests/unit/test_state_refresh.py -v`

**Checkpoint**: US2 verified. Lock events auto-refresh client display. All US1 + US2 tests green.

---

## Phase 4: User Story 3 — Own Changes Reflected Immediately (Priority: P3)

**Goal**: After a player submits a command, their own screen shows the result immediately on loop return.

**Independent Test**: From a single client, add a player. The new player appears on screen immediately after returning to the main menu — no manual refresh needed.

**Note**: No new implementation — the top-level `main()` loop already calls `show_state()` at the start of every iteration. Own commands trigger server state broadcasts that set `update_event`. This phase adds a unit test to verify the clear/check cycle.

### Tests for User Story 3

- [x] T014 [US3] Write unit test `test_update_event_cleared_after_check` — assert that after `update_event.is_set()` returns True and `update_event.clear()` is called, event is no longer set in `tests/unit/test_state_refresh.py`
- [x] T015 [US3] Run unit tests and confirm all tests in `tests/unit/test_state_refresh.py` pass

**Checkpoint**: All three user stories verified. Full test suite green.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [x] T016 Update WS Protocol Reference table in `AGENTS.md` — add note that `state`, `presence`, `lock_acquired`, `lock_released` frames set `ClientState.update_event` in `client/state.py`
- [ ] T017 Run full quality gate and confirm all pass:
  ```bash
  pytest tests/unit -q
  # Podman:
  PATH=$PWD/.venv/bin:$PATH CONTAINER_ENGINE=podman pytest tests/e2e -m e2e -q
  podman-compose up -d && curl -fsS http://localhost:8765/healthz
  # Docker:
  CONTAINER_ENGINE=docker pytest tests/e2e -m e2e -q
  docker compose up -d && curl -fsS http://localhost:8765/healthz
  ```
- [ ] T018 Run manual smoke test from `specs/007-client-screen-sync/quickstart.md` to verify two-client auto-refresh end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: No dependencies — can start immediately. BLOCKS all user stories.
- **US1 (Phase 2)**: Depends on Phase 1 — primary MVP deliverable
- **US2 (Phase 3)**: Depends on Phase 1; can run in parallel with Phase 2 (tests only)
- **US3 (Phase 4)**: Depends on Phase 1; can run in parallel with Phases 2–3 (tests only)
- **Polish (Phase 5)**: Depends on all story phases complete

### User Story Dependencies

- **US1 (P1)**: Foundation complete → implementation + tests
- **US2 (P2)**: Foundation complete → tests only (no new implementation)
- **US3 (P3)**: Foundation complete → tests only (no new implementation)

### Parallel Opportunities

- T003, T004, T005, T006, T007 can be written in a single session (same new file, no conflicts when written by one author)
- T011, T012 can run in parallel
- After T001–T002 (Foundation): Phase 2 tests (T003–T007), Phase 3 tests (T011–T012), and Phase 4 test (T014) can all be written in parallel

---

## Parallel Example: User Story 1

```bash
# Write all US1 unit tests in one session (T003–T007):
tests/unit/test_state_refresh.py  ← all five test functions in one file

# Then implement (T008, T009) — both in risus.py (must be sequential):
risus.py ← add helper then replace input call
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Add `update_event` to `client/state.py` (T001–T002)
2. Complete Phase 2: US1 tests + implementation in `risus.py` (T003–T010)
3. **STOP and VALIDATE**: Two-client smoke test from `quickstart.md`
4. Demo: client A auto-refreshes on client B's changes

### Incremental Delivery

1. Phase 1 → `ClientState` foundation ready
2. Phase 2 → US1 working → manual + automated test validation
3. Phase 3 → US2 lock tests → confirm lock refresh already works
4. Phase 4 → US3 test → confirm own-change refresh already works
5. Phase 5 → `AGENTS.md` update + full quality gate

---

## Notes

- [P] tasks = different files or single-author same file, no incomplete dependencies
- Story labels trace tasks to user stories for traceability
- Two source files change: `client/state.py` (T001–T002), `risus.py` (T008–T009)
- All other `input()` calls in submenus are explicitly NOT changed — intentional per spec edge case
- `select.select` on stdin works on Linux and macOS; Windows not a stated target
- Constitution v1.1.1 explicitly permits the synchronous stdlib-only polling wrapper used in T008
- Commit after Phase 1 checkpoint and after Phase 2 checkpoint at minimum
