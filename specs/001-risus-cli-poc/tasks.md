# Tasks: Risus CLI POC — Text-Adventure Character Tracker

**Input**: Design documents from `specs/001-risus-cli-poc/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/command-schema.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Exact file paths are included in each description

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and package skeleton

- [x] T001 Create Python package skeleton: `risus/` directory with empty `__init__.py`, `__main__.py`, `repl.py`, `models.py`, `persistence.py`, `display.py` — risus/
- [x] T002 Create `pyproject.toml` with project metadata, `[project.scripts]` entry `cli = "risus.__main__:main"`, and `[project.optional-dependencies] dev = ["pytest"]` — pyproject.toml
- [x] T003 [P] Create `tests/` directory with empty `__init__.py` and placeholder test files: `test_models.py`, `test_persistence.py`, `test_repl.py`, `test_display.py` — tests/
- [x] T004 [P] Create `.gitignore` covering `__pycache__`, `*.pyc`, `.pytest_cache`, `dist/`, `*.egg-info` — .gitignore

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data model and display engine that every user story depends on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Implement `Player` dataclass with fields `name: str`, `cliche_name: str = ""`, `dice: int = 0` and `BattleState` class with `players: dict[str, Player]`, `session_name: str | None = None`; include `DuplicatePlayerError`, `PlayerNotFoundError`, `SaveNotFoundError` exception classes — risus/models.py
- [x] T006 Implement `BattleState` operations: `add_player(name, cliche, dice)`, `switch_cliche(player_name, cliche_name, dice)`, `reduce_dice(player_name, amount)` (clamp ≥ 0, remove from display at 0), `active_players()` (returns players with dice > 0 in insertion order) — risus/models.py
- [x] T007 [P] Implement `render(state: BattleState) -> str` in `display.py`: outputs header `"Battle latest state"` (with session name in parens if set), a `=` separator line matching header length, and one line per active player formatted as `"<name>:     <n> dice (<cliche>)"` — risus/display.py
- [x] T008 [P] Write unit tests for `Player` and `BattleState` operations covering: add duplicate player, switch cliché, reduce dice (normal, clamp to 0, player removed at 0), active_players ordering — tests/test_models.py
- [x] T009 [P] Write unit tests for `display.render`: empty state, single player, multiple players, with/without session name, `=` line length matches header — tests/test_display.py

**Checkpoint**: Foundation ready — data model tested, display tested, user story phases can now begin

---

## Phase 3: User Story 1 — Start a Session and Add Players (Priority: P1) 🎯 MVP

**Goal**: Launch `cli`, enter the `>` REPL prompt, add players with `player add`, see reprinted battle state after each command.

**Independent Test**: Launch `cli`, type `player add --name "Hanne"`, then `player add --name "Zerox" --cliche "Firearms" --points 3`. Verify both characters appear in the reprinted battle state table. Verify duplicate `player add --name "Hanne"` shows error without crashing.

- [x] T010 [US1] Implement `RisusRepl(cmd.Cmd)` class skeleton in `repl.py`: set `prompt = "> "`, implement `__init__(self, state: BattleState)` storing state, implement `do_EOF` and `do_exit`/`do_quit` for clean exit (return True), add `default(line)` to print `"Unknown command. Type 'help' for available commands."` — risus/repl.py
- [x] T011 [US1] Implement `do_player(self, args: str)` in `RisusRepl`: use `shlex.split` to tokenise `args`, dispatch sub-command `add` to `_player_add(parts)`; for `add` parse `--name` (required), `--cliche` (default `""`), `--points` (default `0`, int) using `argparse.ArgumentParser(exit_on_error=False)`; call `state.add_player()`; catch `DuplicatePlayerError` and print inline error; on success call `display.render(state)` and print result — risus/repl.py
- [x] T012 [US1] Implement `main()` in `__main__.py`: parse OS-level args with `argparse` for optional `--load <name>` flag; create a fresh `BattleState`; if no `--load` flag print initial (empty) battle state and start `RisusRepl(state).cmdloop()`; if `--load` given, load save (stub: raise `SaveNotFoundError` for now) and start REPL — risus/__main__.py
- [x] T013 [P] [US1] Write unit tests for `do_player add`: add new player, add player with cliche+points, add duplicate player shows error message without exception, add player with no name shows argparse error inline — tests/test_repl.py *(parallel with T010; requires T011 complete before tests are meaningful)*

**Checkpoint**: US1 complete — `cli` launches, `player add` works, duplicate error handled, battle state reprints after each add

---

## Phase 4: User Story 2 — Switch Active Cliché (Priority: P2)

**Goal**: From within the REPL, type `cliche switch --name "Magic spell" --points 4 --target "Hanne"` and see the updated battle state reprinted.

**Independent Test**: With "Hanne" in session, type `cliche switch --name "Magic spell" --points 4 --target "Hanne"`. Verify reprinted state shows "Hanne: 4 dice (Magic spell)". Verify targeting a non-existent player shows inline error.

- [ ] T014 [US2] Implement `do_cliche(self, args: str)` in `RisusRepl`: use `shlex.split` to tokenise, dispatch sub-commands `switch` and `reduce-by`; for `switch` parse `--name` (required), `--points` (required, int ≥ 0), `--target` (required) with `argparse`; call `state.switch_cliche()`; catch `PlayerNotFoundError` and print inline error; on success call `display.render(state)` and print — risus/repl.py
- [ ] T015 [P] [US2] Write unit tests for `do_cliche switch`: switch cliche on existing player updates state and reprints, targeting unknown player shows error without exception, `--points 0` is accepted — tests/test_repl.py

**Checkpoint**: US2 complete — `cliche switch` updates player's active cliche and reprints state

---

## Phase 5: User Story 3 — Reduce Cliché Dice (Priority: P3)

**Goal**: From within the REPL, type `cliche reduce-by --amount 2 --target "Hanne"` and see reduced dice reprinted; reducing to 0 removes player from display.

**Independent Test**: With "Hanne" at 4 dice, type `cliche reduce-by --amount 2 --target "Hanne"`. Verify state shows "Hanne: 2 dice". Reduce by 5 more and verify Hanne no longer appears.

- [ ] T016 [US3] Implement `reduce-by` dispatch inside `do_cliche` in `RisusRepl`: parse `--amount` (required, int ≥ 1) and `--target` (required) with `argparse`; call `state.reduce_dice()`; catch `PlayerNotFoundError` and print inline error; on success call `display.render(state)` and print — risus/repl.py
- [ ] T017 [P] [US3] Write unit tests for `do_cliche reduce-by`: normal reduction, clamp at 0 (player removed from active list), targeting unknown player shows error, `--amount` missing shows argparse error inline — tests/test_repl.py

**Checkpoint**: US3 complete — `cliche reduce-by` reduces dice, removes eliminated players from display

---

## Phase 6: User Story 4 — Save and Resume a Session (Priority: P4)

**Goal**: `save --name "Builders' Shack"` persists state; `cli --load "Builders' Shack"` restores it with session name in header.

**Independent Test**: In a live session add two players, type `save --name "Builders' Shack"`, quit, relaunch with `cli --load "Builders' Shack"`, verify full battle state and session name in header are restored.

- [ ] T018 [US4] Implement `persistence.py`: `_slug(name: str) -> str` using `re.sub(r'[^a-zA-Z0-9_-]', '_', name).lower()`; `_save_dir() -> Path` returning `Path.home() / ".risus" / "saves"` (creates dir on first call); `save(state: BattleState, name: str)` serialises to JSON `{"name": name, "players": [...]}` and writes to `_save_dir() / (_slug(name) + ".json")`; `load(name: str) -> BattleState` reads file, raises `SaveNotFoundError` if not found, deserialises into `BattleState` with `session_name` set — risus/persistence.py
- [ ] T019 [US4] Implement `do_save(self, args: str)` in `RisusRepl`: parse `--name` (required); call `persistence.save(state, name)`; set `state.session_name = name`; print `display.render(state)` — risus/repl.py
- [ ] T020 [US4] Wire up `--load` in `__main__.py`: replace stub with real `persistence.load(name)` call; on `SaveNotFoundError` print `"Save '<name>' not found"` to stderr and `sys.exit(1)`; on success set loaded state into `RisusRepl` and start `cmdloop()` printing initial battle state first — risus/__main__.py
- [ ] T021 [P] [US4] Write unit tests for `persistence.py`: save round-trip (save then load returns equivalent BattleState), load missing save raises `SaveNotFoundError`, special chars in name are slugified, overwrite same name works, loaded state has `session_name` set — tests/test_persistence.py
- [ ] T022 [P] [US4] Write integration test using `subprocess`: launch `cli`, add players, save, quit, relaunch with `--load`, verify stdout contains player names and session name in header — tests/test_repl.py

**Checkpoint**: US4 complete — save/load cycle works end-to-end across process boundaries

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Wiring, edge cases, and final validation

- [ ] T023 Add `help` text (docstrings) to all `do_*` methods in `RisusRepl` so `cmd.Cmd`'s built-in `help` command displays useful per-command descriptions — risus/repl.py
- [ ] T024 [P] Handle `argparse` errors inline: subclass `ArgumentParser` or set `exit_on_error=False` on all parsers and catch `argparse.ArgumentError` / `SystemExit` to print error message inline rather than exiting the REPL process — risus/repl.py
- [ ] T025 [P] Validate `pyproject.toml` entry point: run `pip install -e .` and confirm `cli` launches without import errors, then run `python -m risus` and confirm equivalent behaviour — pyproject.toml
- [ ] T026 [P] Run `pytest` against all test files and confirm all pass; fix any failures — tests/
- [ ] T027 [P] Manual walkthrough of quickstart.md scenario end-to-end: add Hanne, add Zerox, switch cliche, reduce dice, save, quit, reload — verify output matches expected display format from contracts/command-schema.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — no dependency on other stories
- **US2 (Phase 4)**: Depends on Phase 2 — no dependency on US1 (independently testable)
- **US3 (Phase 5)**: Depends on Phase 2 and US2 (`do_cliche` extends Phase 4's dispatcher)
- **US4 (Phase 6)**: Depends on Phase 2 — no dependency on US1/US2/US3
- **Polish (Phase 7)**: Depends on all user stories complete

### User Story Dependencies

- **US1**: Can start after Phase 2 — independent
- **US2**: Can start after Phase 2 — independent
- **US3**: Can start after US2 (shares `do_cliche` dispatcher)
- **US4**: Can start after Phase 2 — independent

### Within Each User Story

- Models before REPL handlers
- REPL handler before unit tests (or TDD: write test stubs first)
- Core implementation before integration tests

### Parallel Opportunities

- T003, T004 can run in parallel with T002 (Phase 1)
- T007, T008, T009 can run in parallel with T006 (Phase 2)
- T013 can run in parallel with T010–T012 (after T011 exists to test)
- T015 parallel with T014; T017 parallel with T016; T021/T022 parallel with T018–T020

---

## Parallel Example: User Story 1

```bash
# After T005/T006 (models) and T007 (display) complete:

# These can run in parallel:
Task T010: "Implement RisusRepl skeleton in risus/repl.py"
Task T013: "Write unit tests for do_player add in tests/test_repl.py"

# Then sequentially:
Task T011: "Implement do_player in risus/repl.py"
Task T012: "Implement main() in risus/__main__.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: US1 (add players, REPL, display)
4. **STOP and VALIDATE**: `cli` → `player add` → state reprints
5. Demo/review before continuing

### Incremental Delivery

1. Setup + Foundational → skeleton + model + display tested
2. US1 → interactive REPL with player add working
3. US2 → cliche switch working
4. US3 → dice reduction + elimination working
5. US4 → save/load across sessions
6. Polish → help text, error handling, final test pass

### Parallel Team Strategy

With two developers after Phase 2:
- Developer A: US1 + US2 + US3 (REPL commands, sequential)
- Developer B: US4 (persistence, independent)
