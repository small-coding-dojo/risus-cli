# Tasks: Secure Session

Input: Design documents from `/specs/004-secure-session/`

Prerequisites: plan.md, spec.md, research.md, data-model.md,
contracts/ws-token-auth.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to
- File paths relative to repository root

---

## Phase 1: Setup (Shared Infrastructure)

Purpose: Create new file stubs before implementation begins

- [ ] T001 [P] Create `tests/unit/test_token_auth.py`
  - Module-level docstring and empty test skeleton
- [ ] T002 [P] Create `tests/e2e/test_token_auth.py`
  - Module-level docstring and empty test skeleton

---

## Phase 2: Foundational (Blocking Prerequisites)

Purpose: Cross-story primitives that US1–US4 all depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Add `class AuthError(Exception): pass` to `client/ws_client.py`
- [ ] T004 [P] Implement `_prompt_token(saved: str | None) -> str` in
  `risus.py`
  - Loop until value has ≥16 printable non-whitespace chars
  - On empty input use `saved` as default only when `saved` is not `None`
  - Print informative message on short input
- [ ] T005 [P] Extend `read_config()` and `write_config()` in
  `client/config.py` to accept and return a `token` field
  - Third positional value; `None` if key absent in file

Checkpoint: Foundation ready — user story implementation can begin

---

## Phase 3: User Story 1 — Authorized Player Connects (Priority: P1) MVP

Goal: Server validates `RISUS_TOKEN` on every connection; wrong or absent
token → `close(4401)`; client re-prompts and retries.

Independent test: Start protected server
(`RISUS_TOKEN=dev-token-for-testing docker compose up -d`); attempt
connection with correct, wrong, and absent tokens.

### Implementation for User Story 1

- [ ] T006 [US1] Add token validation to `server/ws.py` in `handle()`
  - After `await ws.accept()` run `await asyncio.sleep(3)`
  - Check `os.environ.get("RISUS_TOKEN")` and
    `ws.query_params.get("token")`
  - On absent/mismatch: `await ws.close(code=4401, reason="unauthorized")`
  - Log: `logger.warning("ws auth rejected: %s reason=%s", ws.client.host,
    reason)` where reason is `token_absent` or `token_mismatch`
  - Add module-level `logger = logging.getLogger(__name__)`
- [ ] T007 [US1] Pass `?token={token}` query parameter when building
  WebSocket URI in `client/ws_client.py` `start()` method
- [ ] T008 [US1] Catch `websockets.exceptions.ConnectionClosedError` with
  `rcvd.code == 4401` in `client/ws_client.py` `_async_run()`
  - Put `{"type": "auth_failed"}` in inbox and return without reconnect
  - In `start()` raise `AuthError` when `auth_failed` frame arrives
- [ ] T009 [US1] Implement `connect_or_die(server, name, token)` in
  `risus.py`
  - Catches `AuthError`, prints rejection message
  - Calls `_prompt_token(None)` to get new token, retries connection

### Tests for User Story 1

- [ ] T010 [P] [US1] Write server token validation unit tests in
  `tests/unit/test_token_auth.py`
  - Correct token accepted; wrong token → 4401; absent `?token` → 4401
  - `RISUS_TOKEN` env unset → 4401 (mock `ws.query_params` and
    `os.environ`)
- [ ] T011 [P] [US1] Write E2E tests in `tests/e2e/test_token_auth.py`
  - Correct token connects and receives state
  - Wrong token rejected; absent token rejected

Checkpoint: US1 fully functional — security gate active

---

## Phase 4: User Story 2 — Token Remembered Between Sessions (Priority: P2)

Goal: Token persisted to `risus.cfg` on exit; subsequent launches reuse it
without prompting.

Independent test: Enter token, quit, relaunch — no prompt, successful
connection.

### Implementation for User Story 2

- [ ] T012 [US2] Wire token into `risus.py` startup flow
  - Read token from config
  - Call `_prompt_token(saved_token)` only when no token available
  - Register `atexit` handler to call `write_config(server, name, token)`
    on clean exit
  - Rejected token (after AuthError) is NOT saved

### Tests for User Story 2

- [ ] T013 [P] [US2] Add token read/write cases to
  `tests/unit/test_config.py`
  - `write_config` persists token
  - `read_config` returns stored token
  - `read_config` returns `None` when token key absent
- [ ] T014 [P] [US2] Add token prompt cases to
  `tests/unit/test_startup.py`
  - No saved token → prompt shown; saved token → no prompt
  - Empty input with saved token → saved token used
  - Short input → rejected with message and re-prompted
  - Empty input with no default → re-prompted

Checkpoint: US1 + US2 functional — returning players not re-prompted

---

## Phase 5: User Story 3 — Command-Line Token Override (Priority: P3)

Goal: `--token` CLI argument bypasses prompt and stored value.

Independent test: `python risus.py --token my-super-secret-game-token`
— no prompt, supplied token used for connection.

### Implementation for User Story 3

- [ ] T015 [US3] Add `--token` argument to `argparse.ArgumentParser` in
  `risus.py`
  - Wire precedence: CLI arg > config value > `_prompt_token()` prompt

### Tests for User Story 3

- [ ] T016 [US3] Add `--token` cases to `tests/unit/test_startup.py`
  - `--token` suppresses interactive prompt
  - `--token` value overrides stored config value
  - `--token` value is saved to config on clean exit after successful
    connection
  - Rejected `--token` (4401) is NOT saved to config

Checkpoint: US1 + US2 + US3 functional — headless/scripted use supported

---

## Phase 6: User Story 4 — Encrypted Transport for Public Servers (P4)

Goal: Bare hostname → `wss://`; `host:port` → `ws://`; `load_battle()`
works with both schemes; deployment artifacts ready.

Independent test: Build URI with `localhost:8765` → `ws://`; build URI with
`risus.boos.systems` → `wss://`.

### Implementation for User Story 4

- [ ] T017 [P] [US4] Implement scheme detection in `client/ws_client.py`
  - Derive scheme as `"ws://"` when `":" in server` else `"wss://"`
- [ ] T018 [P] [US4] Fix `load_battle()` in `risus.py`
  - Replace `wss://` → `https://` before `ws://` → `http://` to avoid
    double-replace bug
- [ ] T019 [US4] Update `docker-compose.yml`
  - Change server port binding from `"8765:8765"` to
    `"127.0.0.1:8765:8765"`
  - Add `RISUS_TOKEN: ${RISUS_TOKEN}` to server environment
  - Add Caddy service with `network_mode: host`, `./Caddyfile` volume
    mount, and `caddy_data` named volume
- [ ] T020 [P] [US4] Create `Caddyfile` with Caddy reverse proxy
  - TLS via Let's Encrypt for bare domain
  - Reverse proxy to `127.0.0.1:8765`
  - `caddy_data` volume for cert persistence
- [ ] T021 [P] [US4] Write scheme detection unit tests in
  `tests/unit/test_token_auth.py`
  - `"localhost:8765"` → `ws://`; `"risus.boos.systems"` → `wss://`
  - `"[::1]:8765"` → `ws://`
- [ ] T022 [P] [US4] Write `load_battle()` URL derivation unit tests in
  `tests/unit/test_token_auth.py`
  - `ws://host/ws/Name` → `http://host`
  - `wss://host/ws/Name` → `https://host` (verify no double-replace)

Checkpoint: Full feature complete — all four user stories functional

---

## Phase 7: Polish & Cross-Cutting Concerns

Purpose: Final validation across all stories

- [ ] T023 [P] Run full unit test suite: `pytest tests/unit -q`
- [ ] T024 Run E2E test suite with container stack
  - `RISUS_TOKEN=testtoken docker compose up -d`
  - Run pytest with env: `CONTAINER_ENGINE=podman` `RISUS_TOKEN=testtoken`
    `PATH=$PWD/.venv/bin:$PATH pytest tests/e2e -m e2e -q`
- [ ] T025 [P] Verify server logs show `reason=token_absent` or
  `reason=token_mismatch` but never the token value
- [ ] T026 [P] Validate quickstart.md local dev scenario end-to-end
  - `python risus.py localhost:8765 Conan --token dev-token-for-testing`
    uses `ws://`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — **BLOCKS** all user
  stories
- **US1 (Phase 3)**: Depends on Phase 2 — MVP; delivers standalone
  security value
- **US2 (Phase 4)**: Depends on Phase 2; integrates with US1
  `connect_or_die` (rejected token cleared)
- **US3 (Phase 5)**: Depends on Phase 2; extends US2 startup flow (token
  precedence)
- **US4 (Phase 6)**: Depends on Phase 2; independent of US1–US3 (different
  code paths: scheme detection + URL fix + deployment)
- **Polish (Phase 7)**: Depends on all desired user stories complete

### User Story Dependencies

- **US1 (P1)**: Foundational only — no dependency on US2/US3/US4
- **US2 (P2)**: Foundational + US1 `connect_or_die` signature
- **US3 (P3)**: Foundational + US2 startup flow (adds precedence layer)
- **US4 (P4)**: Foundational only — entirely separate code paths

### Within Each User Story

- Server changes (T006) before client integration (T007–T009)
- Implementation complete before writing its tests
- Foundation (T003–T005) before any user story task

### Parallel Opportunities

- Phase 1: T001 and T002 in parallel
- Phase 2: T004 and T005 in parallel (different files)
- Phase 3 tests: T010 and T011 in parallel after T006–T009
- Phase 4 tests: T013 and T014 in parallel after T012
- Phase 6: T017, T018, T020, T021, T022 in parallel; T019 independent

---

## Parallel Example: User Story 1

```bash
# After T006–T009 complete, run tests in parallel:
Task T010: Server unit tests  → tests/unit/test_token_auth.py
Task T011: E2E tests          → tests/e2e/test_token_auth.py
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1
4. STOP and VALIDATE: `pytest tests/unit -q` + E2E against protected server
5. Demo: correct token connects; wrong/absent tokens rejected; client
   re-prompts

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. US1 → security gate active (MVP)
3. US2 → returning players not re-prompted
4. US3 → headless/scripted deployments work
5. US4 → public server with TLS fully supported

### Parallel Team Strategy

After Phase 2 (Foundational) completes:

- **Dev A**: US1 — `server/ws.py` + `ws_client.py` + `connect_or_die` in
  `risus.py`
- **Dev B**: US4 — scheme detection + URL fix + `docker-compose.yml` +
  `Caddyfile`
- Then sequentially: US2 → US3 (both modify `risus.py` startup flow)

---

## Notes

- `[P]` tasks touch different files with no outstanding dependencies
- Each user story is independently testable via its acceptance scenarios in
  spec.md
- Token MUST NOT appear in server logs — enforced by logging pattern in T006
- E2E tests require `RISUS_TOKEN` set and container stack running (see
  quickstart.md)
- `_prompt_token()` is shared by US1 re-prompt-on-rejection and US2 initial
  prompt — implement once in Foundational phase
