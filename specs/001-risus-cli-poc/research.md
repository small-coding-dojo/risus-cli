# Research: Risus CLI POC

**Feature**: 001-risus-cli-poc  
**Date**: 2026-04-20  
**Branch**: 002-risus-cli-poc

---

## Decision 1: Language Choice

**Decision**: Python 3.11+

**Rationale**:
- The README lists `python click` as a candidate library. Python has the fastest path to a working interactive REPL with minimal boilerplate.
- `prompt_toolkit` provides a rich readline-style REPL loop (history, arrow keys, Ctrl-C handling) out of the box.
- The spec is explicitly a POC — no compilation step, no binary distribution needed.
- Python ships on most developer machines; no toolchain setup required.

**Alternatives considered**:
- **Go + Cobra**: Excellent for distribution but Cobra is command-routing focused, not REPL-focused. Building an interactive loop is more boilerplate.
- **Rust + clap**: High-quality CLI parsing but a heavier compile+link cycle and steeper learning curve for a POC.
- **Node + Commander**: Viable but adds npm/node version management overhead.
- **C# + System.CommandLine / DragonFruit**: Heaviest toolchain; not appropriate for a POC.

---

## Decision 2: CLI / REPL Library

**Decision**: `cmd.Cmd` from Python stdlib (with optional `prompt_toolkit` upgrade path)

**Rationale**:
- `cmd.Cmd` is zero-dependency, ships with Python, and provides a command dispatch loop, `help` command generation, and prompt customisation out of the box.
- For a POC it is sufficient; if arrow-key history or syntax highlighting is later desired, `prompt_toolkit` can be dropped in as a replacement `input()` source.
- `click` is good at building traditional argument-parsing CLIs but does not provide a REPL loop; it would require wrapping with a manual `while True` loop and manual argument parsing — more work for equivalent result.

**Alternatives considered**:
- **click**: Great for static commands, not optimised for interactive REPL.
- **prompt_toolkit**: More powerful but heavier for a POC; keep as upgrade path.
- **raw `input()` loop**: Possible but requires reinventing help dispatch and error handling that `cmd.Cmd` provides for free.

---

## Decision 3: Argument Parsing Inside the REPL

**Decision**: `shlex.split` + `argparse.ArgumentParser` per sub-command

**Rationale**:
- The spec commands use `--flag value` syntax (e.g., `--name "Hanne" --points 4`). `argparse` natively handles this.
- `shlex.split` correctly tokenises quoted strings (handles `"Builders' Shack"` with spaces).
- Each command object owns its own `ArgumentParser`, giving clean `--help` output per command automatically.

**Alternatives considered**:
- **Manual string splitting**: Fragile, especially for quoted values with spaces.
- **click in REPL mode**: Requires `standalone_mode=False` and custom invocation — more complexity for equivalent result.

---

## Decision 4: Persistence Format

**Decision**: JSON files in `~/.risus/saves/`

**Rationale**:
- Human-readable (a GM can inspect/edit a save in any text editor).
- No dependencies beyond the Python stdlib `json` module.
- Safe filename encoding: save names are sanitised to filesystem-safe slugs (alphanumeric + hyphens/underscores); the original name is stored inside the JSON.
- Save directory `~/.risus/saves/` is user-local, avoids permission issues, and survives CWD changes.

**Alternatives considered**:
- **SQLite**: Overkill for key-value battle state; adds `sqlite3` dependency (though it is stdlib, it adds conceptual complexity).
- **pickle**: Not human-readable; brittle across Python versions.
- **CWD flat files**: Fragile if the user launches from different directories.
- **TOML**: Requires a third-party library on Python < 3.11 (`tomllib` only reads, `tomli-w` needed for writing).

---

## Decision 5: Project / Package Structure

**Decision**: Single flat Python package `risus/` with a `__main__.py` entry point + `pyproject.toml`

**Rationale**:
- A POC with 4 user stories fits cleanly in a single package.
- `python -m risus` works without installation; `pip install -e .` makes `cli` available on PATH.
- `pyproject.toml` (PEP 517/518) with `hatchling` or `setuptools` is the modern standard.

**Structure**:
```
risus/
├── __main__.py       # Entry: parses --load, launches REPL
├── repl.py           # Cmd.Cmd subclass — command dispatch loop
├── models.py         # Player, BattleState dataclasses
├── persistence.py    # save/load to ~/.risus/saves/
└── display.py        # Battle state table renderer
tests/
├── test_models.py
├── test_persistence.py
├── test_repl.py
└── test_display.py
pyproject.toml
```

---

## Decision 6: Testing Framework

**Decision**: `pytest` with no additional plugins for the POC

**Rationale**:
- Industry-standard Python test runner; terse syntax; good error output.
- `cmd.Cmd` dispatch can be tested by calling `onecmd(line)` directly, making unit tests straightforward without spawning subprocesses.
- Integration tests for the `--load` entry point use `subprocess` from stdlib.

**Alternatives considered**:
- **unittest**: Verbose; pytest is strictly better for a new project.
- **hypothesis**: Property-based testing is useful but out of scope for a POC.

---

## Decision 7: save name → filename encoding

**Decision**: `re.sub(r'[^a-zA-Z0-9_-]', '_', name).lower()` + collision guard via stored `"name"` field in JSON

**Rationale**:
- Deterministic, reversible enough for display (original name lives in JSON).
- Handles special characters (apostrophes, spaces, accents) without filesystem issues.
- Overwrite semantics: same encoded filename = overwrite, matching the spec ("two saves with the same name → overwrite existing").

---

## Summary of Resolved Unknowns

| # | Unknown | Resolution |
|---|---------|-----------|
| 1 | Language | Python 3.11+ |
| 2 | REPL library | `cmd.Cmd` (stdlib) |
| 3 | Arg parsing in REPL | `shlex` + `argparse` per command |
| 4 | Persistence | JSON in `~/.risus/saves/` |
| 5 | Project structure | Single `risus/` package |
| 6 | Testing | `pytest` |
| 7 | Save filename encoding | slug via regex, original name in JSON |
