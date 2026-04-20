# Feature Specification: Risus CLI POC — Text-Adventure Character Tracker

**Feature Branch**: `001-risus-cli-poc`  
**Created**: 2026-04-20  
**Status**: Draft  
**Input**: User description: "textadventure like cli POC for risus character tracking"

## User Scenarios & Testing *(mandatory)*

The tool is an **interactive REPL** (text-adventure style shell). The user launches it once from the OS prompt — either starting fresh or loading a named save — and then types commands at an interactive `>` prompt until they quit. Commands inside the shell do not require a `cli` prefix.

**Entry points** (OS shell):

- `cli` — start a new empty session and enter the interactive shell
- `cli --load "Builders' Shack"` — load a named save and enter the interactive shell

**Exit**: typing `quit` or `exit` at the `>` prompt ends the session.

---

### User Story 1 - Start a Session and Add Players (Priority: P1)

The GM launches the tool, which displays a `>` prompt. They add characters by typing `player add` commands. After each command the current battle state is printed above the prompt.

**Why this priority**: Core entry point — the interactive session cannot function without it.

**Independent Test**: Launch `cli`, type `player add --name "Hanne"`, then `player add --name "Zerox" --cliche "Firearms" --points 3`. Verify both characters appear in the reprinted battle state table.

**Acceptance Scenarios**:

1. **Given** the tool is launched fresh, **When** the user is at the `>` prompt, **Then** an empty battle state table (or welcome header) is displayed
2. **Given** the user is at the `>` prompt, **When** they type `player add --name "Hanne"`, **Then** the battle state is reprinted showing "Hanne: 0 dice ()"
3. **Given** "Hanne" already exists, **When** the user types `player add --name "Hanne"` again, **Then** an inline error is shown: "Player 'Hanne' already exists" and the prompt returns

---

### User Story 2 - Switch Active Cliché (Priority: P2)

Inside the interactive session, the GM updates a player's active cliché and dice pool with a single command. The battle state is reprinted immediately.

**Why this priority**: Cliché switching is the primary in-battle mechanic.

**Independent Test**: With "Hanne" in the session, type `cliche switch --name "Magic spell" --points 4 --target "Hanne"`. Verify the reprinted state shows "Hanne: 4 dice (Magic spell)".

**Acceptance Scenarios**:

1. **Given** "Hanne" exists, **When** the user types `cliche switch --name "Magic spell" --points 4 --target "Hanne"`, **Then** the state reprints with "Hanne: 4 dice (Magic spell)"
2. **Given** a non-existent player name, **When** a switch targets them, **Then** an inline error is shown: "Player '[name]' not found"

---

### User Story 3 - Reduce Cliché Dice (Priority: P3)

Inside the session, the GM records damage by reducing a player's active dice pool. When a player reaches 0 dice they are removed from the battle state display.

**Why this priority**: Models combat damage — essential for tracking who is winning or losing.

**Independent Test**: With "Hanne" at 4 dice, type `cliche reduce-by --amount 2 --target "Hanne"`. Verify state shows "Hanne: 2 dice (Magic spell)". Then reduce by 2 more and verify Hanne no longer appears in the table.

**Acceptance Scenarios**:

1. **Given** "Hanne" has 4 dice, **When** the user types `cliche reduce-by --amount 2 --target "Hanne"`, **Then** the state reprints with "Hanne: 2 dice"
2. **Given** "Hanne" has 2 dice, **When** `cliche reduce-by --amount 5 --target "Hanne"` is typed, **Then** dice clamp to 0 and Hanne is removed from the battle state display

---

### User Story 4 - Save and Resume a Session (Priority: P4)

The GM saves the current battle state to a named slot from within the shell. To resume, they launch the tool with `--load` at the OS prompt, which drops them directly back into the named session at the interactive `>` prompt.

**Why this priority**: Supports pausing mid-battle and resuming across OS sessions.

**Independent Test**: In a live session, type `save --name "Builders' Shack"`. Quit the tool. Relaunch with `cli --load "Builders' Shack"`. Verify the full battle state is restored and the header shows the session name.

**Acceptance Scenarios**:

1. **Given** an active battle, **When** the user types `save --name "Builders' Shack"`, **Then** state is persisted and the battle state header shows "Builders' Shack"
2. **Given** a saved session, **When** the user launches `cli --load "Builders' Shack"`, **Then** the battle state is restored and the interactive prompt appears with the session name in the header
3. **Given** `cli --load "Missing"` is run, **Then** an error is printed and the tool exits: "Save 'Missing' not found"
4. **Given** a session is loaded, **When** the user makes further changes (e.g., reduces dice), **Then** the session name remains in the header until the user saves under a different name or starts a new session

---

### Edge Cases

- What happens when dice are reduced below zero? → Clamp to 0, then remove player from the display.
- What happens if `--points` is omitted from `player add`? → Default to 0 dice with empty cliché.
- What if the save name contains special characters? → Accept any printable string; use safe filename encoding internally.
- What if two saves share the same name? → Overwrite the existing save.
- What if the user types an unrecognised command at the `>` prompt? → Print "Unknown command. Type `help` for available commands." and re-display the prompt.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST launch into an interactive `>` prompt when invoked (with or without `--load`).
- **FR-002**: System MUST allow adding a named player to the active session, with an optional starting cliché and dice count.
- **FR-003**: System MUST display the current battle state (player name, dice count, active cliché) after every mutating command, before returning to the `>` prompt.
- **FR-004**: System MUST allow switching a player's active cliché and dice count via a single interactive command.
- **FR-005**: System MUST allow reducing a player's active cliché dice pool by a specified integer amount, clamped at 0; a player at 0 dice is removed from the battle state display.
- **FR-006**: System MUST persist the current battle state to a named save slot on disk when the `save` command is issued.
- **FR-007**: System MUST accept `--load <name>` at launch, restore the named session, and enter the interactive prompt showing that session's state.
- **FR-008**: System MUST report a clear inline error and re-display the `>` prompt when a command targets a player that does not exist.
- **FR-009**: System MUST display the save name in the battle state header for the duration of the interactive session once a save is active (loaded or saved).
- **FR-010**: System MUST exit cleanly when the user types `quit` or `exit`.

### Key Entities

- **Player**: A named character in the session. Has a name (string), active cliché name (string, can be empty), and active dice count (non-negative integer).
- **Battle State**: The complete set of players and their current stats; also holds an optional session name.
- **Save Slot**: A named, persistent snapshot of the battle state stored on disk between tool invocations.
- **Interactive Session**: The running instance of the tool from launch to quit; holds the in-memory battle state.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A GM can launch the tool, add two players, switch a cliché, reduce dice, save, quit, reload, and see the restored state — all in under 2 minutes with no documentation.
- **SC-002**: Each interactive command produces a reprinted battle state within 500 ms.
- **SC-003**: All invalid inputs (unknown player, unknown command, missing required arg) produce a descriptive inline error without crashing or exiting the shell.
- **SC-004**: Saved state survives the tool process exiting and is correctly restored on the next `--load` invocation.

## Clarifications

### Session 2026-04-20

- Q: When a player reaches 0 dice, how should they appear in the battle state display? → A: Remove from the display entirely.
- Q: Does the session name persist in the header after loading a save and making further changes, or does it clear? → A: The session is interactive; loading drops the user into the tool — the session name persists in the header for the entire interactive session.

## Assumptions

- This is a **proof-of-concept** — no production hardening, auth, or network features are required.
- The tool is an interactive REPL (text-adventure style); commands within the shell omit the `cli` prefix.
- State is held in memory during the session; disk persistence only happens on an explicit `save` command or at launch via `--load`.
- A single active session exists at a time; no multi-session concurrency is needed.
- Commands within the shell use the same resource-action syntax as the README (e.g., `player add`, `cliche switch`, `cliche reduce-by`, `save`, `load`), without the leading `cli` token.
- Output format is human-readable plain text; JSON/TOML output is a future extension.
- Players cannot be removed mid-session in this POC (removal is a future extension).
- A `help` command listing available commands is included for discoverability.
