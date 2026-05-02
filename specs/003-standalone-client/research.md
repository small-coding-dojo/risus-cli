# Research: Standalone Client Distribution

**Date**: 2026-05-02 | **Feature**: 003-standalone-client

## Decision 1: Packaging Tool

**Decision**: PyInstaller
**Rationale**: Most mature Python-to-binary tool; handles asyncio + threading
(both used in `ws_client.py`); excellent `websockets` support via
`--collect-all websockets`; cross-platform (Windows/macOS/Linux); large
community; single `--onefile` flag produces a single executable.
**Alternatives considered**:

- *Nuitka*: Compiles to C, produces smaller/faster binaries. Rejected —
  higher complexity, longer build times, less predictable behavior with
  asyncio internals. Appropriate for a future optimization pass.
- *cx_Freeze*: Older, less actively maintained. Rejected — no advantage
  over PyInstaller for this use case.
- *shiv / zipapp*: Produces a zip-based bundle; still requires Python on
  the target machine. Rejected — does not satisfy the core requirement.
- *Briefcase (BeeWare)*: Targets full app packaging with installers. Rejected
  — over-engineered for a CLI tool; adds unnecessary dependency.

## Decision 2: Build Mode (onefile vs onedir)

**Decision**: `--onefile`
**Rationale**: Single executable is the simplest distribution artifact for
players — download, mark executable (Unix), run. No extraction step needed.
**Alternatives considered**:

- *onedir*: Faster startup (no self-extraction), easier debugging. Rejected
  for player distribution — requires distributing a directory/zip. Can be
  offered as a developer debug build if needed.

## Decision 3: Cross-Platform Build Strategy

**Decision**: Build each platform binary on its native OS via CI matrix
(GitHub Actions: ubuntu-latest, macos-latest, windows-latest).
**Rationale**: PyInstaller does not support cross-compilation. Each runner
produces the binary for its own platform. Artifacts are uploaded to a GitHub
Release.
**Alternatives considered**:

- *Docker cross-build*: Feasible for Linux targets only. Rejected as
  insufficient.
- *Manual developer builds*: Fragile, not reproducible. Rejected.

## Decision 4: Hidden Imports for websockets

**Decision**: Use `--collect-all websockets` in the PyInstaller spec.
**Rationale**: `websockets` uses dynamic imports internally that PyInstaller
static analysis may miss. `--collect-all` captures all submodules and data
files without manual enumeration.
**Alternatives considered**:

- Manual `--hidden-import` enumeration: Brittle — breaks on websockets
  version bumps. Rejected.

## Decision 5: Entry Point

**Decision**: `risus.py` at project root (existing entry point, updated to
handle interactive prompts and config file reading).
**Rationale**: Already the single entry point for the CLI. Minimal change —
add argument parsing and conditional prompting before the existing connect
call.

## Decision 6: Distribution Channel

**Decision**: GitHub Releases — one release per version, platform binaries
as release assets.
**Rationale**: Free, native to the repository, familiar to developers and
technically-minded players. URLs are stable.
**Alternatives considered**:

- *Itch.io*: Adds a platform dependency for a CLI tool. Rejected.
- *Self-hosted*: Maintenance burden. Rejected.

## Decision 7: Binary Naming Convention

**Decision**: `risus-{os}-{arch}[.exe]` (e.g., `risus-linux-x86_64`,
`risus-macos-arm64`, `risus-windows-x86_64.exe`).
**Rationale**: Unambiguous, grep-friendly, consistent with common CLI tool
distribution patterns (kubectl, gh, golangci-lint).

## Decision 8: Interactive Prompt Behaviour

**Decision**: `risus.py` checks `sys.argv`. If server address or display
name are missing, print prompts via `input()` (synchronous, per
constitution). Both prompts pre-fill defaults from the config file when
values are present (`server` key for address, `name` key for display name).
**Rationale**: `input()` is already used throughout the CLI (constitution
mandates synchronous input). Extending startup to use `input()` is the
zero-friction path.
**Alternatives considered**:

- *prompt_toolkit or similar*: Richer UX (arrow keys, history). Rejected —
  constitution explicitly prohibits `prompt_toolkit` or async input
  libraries.

## Decision 9: Config File Format

**Decision**: Simple key=value plain text (`server=localhost:8765`). Python's
`configparser` reads it with no new dependencies.
**Rationale**: Editable with any text editor on any platform. No JSON/TOML
parser needed. `configparser` is stdlib.
**Alternatives considered**:

- *TOML*: Requires `tomllib` (stdlib in 3.11+, acceptable) but adds
  complexity for a single key. Rejected.
- *JSON*: Familiar to developers but intimidating to players who just want
  to change a server address. Rejected.
- *INI with sections*: `configparser` supports this natively; a `[risus]`
  section keeps the namespace clean. Adopted (see contract).

## Decision 10: Config File Location

**Decision**: Same directory as the executable (or project root when running
from source). Filename: `risus.cfg`.
**Rationale**: Simplest to find and edit — players see it next to the binary
they downloaded. No platform-specific path resolution needed. Consistent
between source and packaged runs.
**Alternatives considered**:

- *Platform config dir* (`~/.config/risus/`, `%APPDATA%\risus\`): More
  "correct" but players cannot find it without instructions. Rejected —
  Principle II favors simplicity.
- *Next to executable only*: Chosen. Works for both source runs (project
  root) and packaged runs (dir containing the binary).

## Decision 11: Save-on-Exit Implementation Strategy

**Decision**: Register a save function via Python's `atexit` module in
`risus.py`. The function writes the last-used server address and display name
to `risus.cfg` using `configparser`. Errors are caught and silently ignored.
**Rationale**: `atexit` handlers run on normal interpreter exit (including
`sys.exit()`, end-of-script, and unhandled exceptions). This covers all
graceful shutdown paths without requiring explicit cleanup calls throughout
the codebase. Silently ignoring write errors honours Principle II (simplicity)
— a failed config save must not disrupt the player's session.
**Known limitation**: `atexit` does NOT run on SIGKILL or OS-level process
termination. Previously saved defaults are retained in that case, which is
acceptable.
**Alternatives considered**:

- *Signal handler (SIGTERM/SIGINT)*: More explicit, handles Ctrl-C. Rejected
  for primary mechanism — `atexit` already covers SIGINT (KeyboardInterrupt
  propagates to atexit). Adding explicit signal handlers adds complexity with
  minimal gain.
- *Explicit `try/finally` in main()*: Equivalent to `atexit` for normal flow
  but misses exception-path exits. Rejected as inferior to `atexit`.

## Resolved Unknowns

All items from the initial plan and post-clarification spec are resolved.
No user input outstanding.
