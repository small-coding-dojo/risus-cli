# Tasks: Standalone Client Distribution

**Input**: Design documents from `specs/003-standalone-client/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅,
contracts/ ✅

**Note**: Unit test tasks are included because the project constitution
(`.specify/memory/constitution.md` § IV) mandates passing unit tests before
any PR.

**Organization**: Tasks grouped by user story for independent implementation
and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story label (US1, US2, US3)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Build tooling, gitignore, config template, dev dependency.

- [ ] T001 Add `dist/`, `build/risus/`, and `risus.cfg` entries to
  `.gitignore`
- [ ] T002 [P] Create `build/` directory with placeholder `build/README.md`
  (full content added in T013)
- [ ] T003 [P] Create `risus.cfg.example` at project root per
  `specs/003-standalone-client/contracts/config-file.md` — include
  commented `server` and `name` keys with auto-save note
- [ ] T004 Add `pyinstaller` to `[project.optional-dependencies]` `dev`
  list in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: `client/config.py` — shared config read/write used by US1,
US2, and US3. Must be complete before any user story begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T005 Implement `client/config.py` with two public functions:
  `read_config(base_dir: Path) -> tuple[str | None, str | None]` reads
  `[risus]` section keys `server` and `name` from `base_dir/risus.cfg`
  using `configparser`; returns `(None, None)` if file/section/key absent;
  never raises. `write_config(base_dir: Path, server: str, name: str) ->
  None` writes both keys; creates file if absent; silently ignores all
  errors. Follows `specs/003-standalone-client/contracts/config-file.md`
  and `specs/003-standalone-client/data-model.md`.
- [ ] T006 [P] Unit tests for `client/config.py` in
  `tests/unit/test_config.py`: absent file → `(None, None)`; valid file
  with both keys → correct values; file with missing keys → `None` for
  each; write creates file with correct INI content; write with read-only
  path does not raise; existing file is overwritten on write.

**Checkpoint**: `client/config.py` passes `pytest tests/unit/test_config.py
-q` — user story work can now begin.

---

## Phase 3: User Story 1 - Download and Run Client (Priority: P1) 🎯 MVP

**Goal**: Player on a machine without Python downloads the binary, runs it,
is prompted for server address (pre-filled from saved defaults) and display
name, connects, and on exit the values are saved for next session.

**Independent Test**: On a machine with no Python installed, run the built
binary with no CLI args, enter server and name at prompts, verify connection,
quit, relaunch and confirm prompts pre-fill saved values.

### Implementation for User Story 1

- [ ] T007 [US1] Update `risus.py` — replace positional `sys.argv` access
  with `argparse` parsing: optional positional args `server` (default None)
  and `name` (default None). After parsing, call `client.config.read_config`
  with `Path(__file__).parent` to load defaults. Prompt for any missing arg
  per `specs/003-standalone-client/contracts/interactive-prompt.md`: server
  prompt shows `[default]` when available, re-prompts on empty input; same
  for name. Register `atexit` handler calling `client.config.write_config`
  with the resolved server and name.
- [ ] T008 [P] [US1] Unit tests for startup prompt logic in
  `tests/unit/test_startup.py`: no args + no config → both prompts shown
  blank; no args + config with both values → prompts show defaults; server
  arg provided + no name → only name prompted; both args provided → no
  prompts; empty prompt input re-prompts; atexit handler registered after
  successful arg resolution. Mock `input()` and `client.config` in all
  cases.
- [ ] T009 [US1] Create `build/risus.spec` — PyInstaller spec file with:
  `Analysis(['risus.py'], ...)`, `collect_all('websockets')`,
  `EXE(..., name='risus', onefile=True, console=True)`. Follow
  `specs/003-standalone-client/contracts/build-command.md` Decision 4.
  Verify locally with `python -m PyInstaller build/risus.spec` — confirm
  `dist/risus` (or `dist/risus.exe`) is produced and runs.
- [ ] T010 [US1] Improve server-unreachable error message in `risus.py` —
  catch `TimeoutError` from `WSClient.start()` and print a user-friendly
  message (e.g. `Cannot reach server at {server}. Check address and try
  again.`) instead of a raw traceback. Satisfies FR-007.

**Checkpoint**: `dist/risus` built from source, runs on a Python-free
machine, prompts work, saves config on exit — US1 independently complete.

---

## Phase 4: User Story 2 - Developer Builds and Distributes Client (P2)

**Goal**: Developer runs one command to produce a platform binary; CI
produces binaries for all three platforms on tag push and uploads them to a
GitHub Release.

**Independent Test**: Push a version tag; verify GitHub Actions produces
`risus-linux-x86_64`, `risus-macos-arm64`, `risus-macos-x86_64`, and
`risus-windows-x86_64.exe` as release assets with matching `.sha256` files.

### Implementation for User Story 2

- [ ] T011 [US2] Create `.github/workflows/build.yml` — on push/PR to
  `main` and `003-standalone-client` branches: matrix
  `[ubuntu-latest, macos-13, macos-latest, windows-latest]`; install
  `pyinstaller`; run `python -m PyInstaller build/risus.spec`; verify
  `dist/risus[.exe]` is non-empty; upload artifact (no publish). Satisfies
  CI smoke-test requirement from `contracts/build-command.md`.
- [ ] T012 [US2] Create `.github/workflows/release.yml` — trigger on `push`
  to tags matching `v*.*.*`: reuse build matrix from T011; rename each
  artifact per `specs/003-standalone-client/contracts/artifact-naming.md`
  (e.g. `risus-linux-x86_64`); compute `sha256sum` and write
  `{artifact}.sha256`; create GitHub Release via `gh release create` or
  `softprops/action-gh-release`; upload all binaries and checksum files as
  release assets.
- [ ] T013 [US2] Write complete developer build instructions in
  `build/README.md`: prerequisites, `pip install pyinstaller`, build
  command, expected output path, clean command, CI context. Per
  `specs/003-standalone-client/contracts/build-command.md`.

**Checkpoint**: Tag `v0.1.0-test`; verify release workflow succeeds and
GitHub Release contains four platform binaries — US2 independently
complete.

---

## Phase 5: User Story 3 - Clear Download Instructions for Players (P3)

**Goal**: Players can find, download, and run the client following
player-facing instructions without any Python knowledge.

**Independent Test**: Follow only the player instructions from start to
finish on a clean machine (no Python); client connects and saves config.

### Implementation for User Story 3

- [ ] T014 [US3] Create `PLAYER.md` at project root — adapt content from
  `specs/003-standalone-client/quickstart.md`: download table, chmod step,
  macOS Gatekeeper workaround, run options (double-click and CLI), config
  file auto-save explanation with `risus.cfg.example` reference,
  troubleshooting table. This is the file distributed alongside (or linked
  from) the release.
- [ ] T015 [P] [US3] Update project root `README.md` — add a "Playing the
  Game" section that links to `PLAYER.md` and the GitHub Releases page.
  Keep the existing developer sections intact.

**Checkpoint**: `PLAYER.md` and release page together allow a player with
no Python knowledge to connect — US3 independently complete.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validation, gitignore cleanup, final smoke test.

- [ ] T016 [P] Verify `risus.cfg` and `dist/` absent from `git status`
  after a local build (gitignore correct per T001)
- [ ] T017 Run `pytest tests/unit -q` and confirm all new tests pass
  (T006, T008)
- [ ] T018 Run end-to-end smoke test: build binary, copy to temp dir (no
  Python in PATH), run with `--help` or valid server args, confirm no
  traceback on clean exit
- [ ] T019 [P] Run `ruff check` on `risus.py` and `client/config.py`; fix
  any lint errors

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately; T002, T003,
  T004 parallel
- **Foundational (Phase 2)**: Requires Phase 1 complete; T006 parallel
  with T005 if stubs exist
- **US1 (Phase 3)**: Requires Phase 2 complete; T008, T009 parallel after
  T007 drafted
- **US2 (Phase 4)**: Requires T009 (`build/risus.spec`) — can start in
  parallel with Phase 3 polish
- **US3 (Phase 5)**: Independent of US1/US2 content — can start after
  Phase 1; T015 parallel with T014
- **Polish (Phase 6)**: Requires Phase 3 complete for T017/T018

### User Story Dependencies

- **US1 (P1)**: Depends on Phase 2 only — primary MVP
- **US2 (P2)**: Depends on T009 (`build/risus.spec`) from US1
- **US3 (P3)**: Independent — can start after Phase 1

### Within Each User Story

- T007 → T008 (unit tests reference startup logic)
- T009 depends on T007 (spec wraps the updated entry point)
- T011 → T012 (release workflow reuses build steps)
- T014 → T015 (README links to PLAYER.md)

### Parallel Opportunities

- T002, T003, T004 parallel in Phase 1
- T005 + T006 can overlap (write stubs first)
- T008, T009 parallel once T007 is drafted
- T011 + T013 parallel (different files)
- T014 + T015 parallel

---

## Parallel Example: User Story 1

```text
# Once T007 is drafted:
Task T008: tests/unit/test_startup.py   (parallel)
Task T009: build/risus.spec             (parallel)
Task T010: risus.py error message       (independent)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T004)
2. Complete Phase 2: Foundational (T005–T006)
3. Complete Phase 3: User Story 1 (T007–T010)
4. **STOP and VALIDATE**: build binary, run on Python-free machine
5. Tag `v0.1.0-alpha` if validated

### Incremental Delivery

1. Setup + Foundational → `client/config.py` ready
2. US1 → standalone binary with interactive startup + save-on-exit (MVP)
3. US2 → CI release pipeline (developer workflow)
4. US3 → player docs (distribution polish)
5. Phase 6 → final validation

### Parallel Team Strategy

With two developers after Phase 2:

- Developer A: US1 (T007–T010)
- Developer B: US3 (T014–T015) — no dependency on US1

---

## Notes

- `[P]` tasks operate on different files with no incomplete dependencies
- `[US?]` label traces each task to its user story
- Constitution § IV mandates `pytest tests/unit -q` passes before PR
- `client/config.py` never raises — all errors are caught internally
- PyInstaller `--onefile` causes ~2–4 s startup latency (self-extraction);
  acceptable per performance goal of <3 s launch
- `atexit` does not fire on SIGKILL — documented limitation in spec
