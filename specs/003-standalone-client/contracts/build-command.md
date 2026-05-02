# Contract: Build Command

**Feature**: 003-standalone-client | **Date**: 2026-05-02

## Purpose

Defines the single reproducible command a developer runs to produce the
standalone client binary on any supported platform.

## Command

```bash
python -m PyInstaller build/risus.spec
```

## Preconditions

- Python 3.12+ installed in the developer environment
- `pip install pyinstaller` executed (dev dependency)
- Command run from the project root directory
- No `dist/` or `build/risus/` directories from a stale previous build
  (run `rm -rf dist/ build/risus/` to clean)

## Postconditions

- `dist/risus` (Unix) or `dist/risus.exe` (Windows) exists and is executable
- Binary is self-contained: no Python installation required on the target
  machine to run it
- Binary size is non-zero (CI verifies this)

## Error Conditions

| Condition | Expected behaviour |
|-----------|-------------------|
| `websockets` not collected | Build fails with `ModuleNotFoundError`; fix: verify `--collect-all websockets` in spec |
| Missing hidden import | Runtime crash on first WS connect; fix: add missing module to `hiddenimports` in spec |
| Stale build cache | Unexpected behaviour; fix: clean `dist/` and `build/risus/` and rebuild |

## Spec File Location

`build/risus.spec` — committed to the repository. Contains all PyInstaller
flags so the command above is the single source of truth for build
configuration. No flags are passed on the command line beyond the spec path.

## CI Usage

CI calls the same command in a matrix across three runners. The spec file is
platform-agnostic; PyInstaller writes platform-appropriate output
automatically.
