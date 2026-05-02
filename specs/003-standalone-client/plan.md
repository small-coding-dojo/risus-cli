# Implementation Plan: Standalone Client Distribution

**Branch**: `003-standalone-client` | **Date**: 2026-05-02 |
**Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-standalone-client/spec.md`

## Summary

Package the Risus CLI client (`risus.py` + `client/`) as a self-contained
executable for Windows, macOS, and Linux using PyInstaller so players can run
the battle manager without a Python installation. When CLI arguments are
omitted, the client prompts interactively for server address and display name,
pre-filling defaults from `risus.cfg` when present. On normal exit the client
writes the last-used values back to `risus.cfg`. The server stack is unchanged;
only the client delivery mechanism, startup UX, and exit behaviour change.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: websockets>=12 (only runtime client dep);
  PyInstaller (build-time only)
**Storage**: Plain-text config file (`risus.cfg`, INI key=value) — read at
  startup, written on normal exit; stores server address and display name;
  not battle state
**Testing**: pytest 8+; unit (no containers); smoke test for built binary
**Target Platform**: Windows 10+, macOS 12+, Linux (Ubuntu 22.04+,
  Fedora 38+)
**Project Type**: CLI tool → standalone executable + config file
**Performance Goals**: Launch in <3 s; interactive prompt appears
  immediately on startup
**Constraints**: Single-command build; no Python runtime on target machine;
  config file editable with any text editor
**Scale/Scope**: One executable per OS/arch; one optional config file per
  installation; distributed via GitHub Releases

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| --------- | ------ | ----- |
| I. Server Authority | ✅ PASS | No server or state logic touched |
| II. Simplicity | ✅ PASS | No menu/UX/`input()` changes beyond new startup prompts |
| III. No Duplication | ✅ PASS | Config read+write logic lives in one new module (`client/config.py`) |
| IV. Testing Discipline | ✅ PASS | Unit tests cover prompt + save logic; binary smoke test added |
| V. No Local Persistence | ✅ PASS (scoped) | Config file stores connection *defaults* only (server address + display name), not battle state. App reads at startup and writes on exit. Principle V explicitly targets battle state I/O. |

**Principle V interpretation**: The constitution states "The CLI MUST NOT
perform local JSON or file I/O for *battle state*." A config file for
connection defaults (server address, display name) is configuration, not
battle state. The app reads it at startup and writes it on clean exit — both
operations are purely for UX convenience. If a future reviewer disagrees,
a minor amendment ("Configuration file for connection defaults is permitted")
resolves it without touching any core principle.

No complexity violations. Complexity Tracking table not required.

## Project Structure

### Documentation (this feature)

```text
specs/003-standalone-client/
├── plan.md              # This file (/speckit-plan output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output — player instructions
├── contracts/           # Phase 1 output
│   ├── build-command.md
│   ├── artifact-naming.md
│   ├── config-file.md   # NEW: config file format contract
│   └── interactive-prompt.md  # NEW: startup prompt contract
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
risus.py                 # Entry point — updated: reads CLI args + prompts
client/
├── __init__.py
├── state.py
└── ws_client.py

client/config.py         # NEW: reads risus.cfg at startup; writes on exit

build/                   # NEW: build tooling
├── risus.spec           # PyInstaller spec file
└── README.md            # Developer build instructions

dist/                    # Build output (git-ignored)
└── risus[.exe]          # Produced binary

risus.cfg                # NEW: optional player config file (git-ignored
                         #      except for risus.cfg.example)
risus.cfg.example        # NEW: example config committed to repo
```

**Structure Decision**: Single-project layout. New `client/config.py` module
handles config file reading. New `build/` directory holds PyInstaller
configuration. `dist/` and `risus.cfg` are git-ignored; `risus.cfg.example`
is committed as a template for players.
