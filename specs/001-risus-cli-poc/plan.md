# Implementation Plan: Risus CLI POC — Text-Adventure Character Tracker

**Branch**: `002-risus-cli-poc` | **Date**: 2026-04-20 | **Spec**: specs/001-risus-cli-poc/spec.md  
**Input**: Feature specification from `/specs/001-risus-cli-poc/spec.md`

## Summary

Build a Python-based interactive REPL (text-adventure style shell) that lets a GM manage Risus tabletop RPG battle state — adding players, switching clichés, reducing dice, and saving/loading named sessions — using `cmd.Cmd` for the REPL loop, `argparse` + `shlex` for in-shell argument parsing, and JSON files in `~/.risus/saves/` for persistence.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: stdlib only (`cmd`, `argparse`, `shlex`, `json`, `pathlib`, `dataclasses`); `pytest` for tests  
**Storage**: JSON files in `~/.risus/saves/`  
**Testing**: pytest  
**Target Platform**: Linux/macOS developer workstation  
**Project Type**: CLI / interactive REPL  
**Performance Goals**: Command response < 500 ms (SC-002); trivially met by in-memory state  
**Constraints**: POC — no auth, no network, no production hardening; single active session  
**Scale/Scope**: Single-user local tool; handful of players per session

## Constitution Check

The project constitution is currently a blank template with no enforced principles. No gate violations apply.

*Post-design re-check*: The single-package structure, stdlib-first dependency strategy, and `pytest` test setup are consistent with common POC/YAGNI principles. No violations identified.

## Project Structure

### Documentation (this feature)

```text
specs/001-risus-cli-poc/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── command-schema.md  # Phase 1 output
└── tasks.md             # Phase 2 output (speckit-tasks)
```

### Source Code (repository root)

```text
risus/
├── __main__.py       # Entry point: parses --load flag, launches REPL
├── repl.py           # cmd.Cmd subclass — command dispatch loop
├── models.py         # Player, BattleState dataclasses + domain errors
├── persistence.py    # save/load JSON to ~/.risus/saves/
└── display.py        # Battle state table renderer

tests/
├── test_models.py
├── test_persistence.py
├── test_repl.py
└── test_display.py

pyproject.toml
```

**Structure Decision**: Single Python package (Option 1). The feature is a self-contained CLI POC with four user stories, all operating on a single in-memory aggregate. A flat `risus/` package with one module per concern (models, repl, persistence, display) is the simplest correct structure.

## Complexity Tracking

*No constitution violations to justify.*
