# Contract: Configuration File

**Feature**: 003-standalone-client | **Date**: 2026-05-02

## Purpose

Defines the format, location, and keys of the `risus.cfg` file used to
persist connection defaults between sessions. The client reads it at startup
and writes it on normal exit.

## Format

INI format with a single `[risus]` section:

```ini
[risus]
server = host:port
name = display-name
```

Example:

```ini
[risus]
server = 192.168.1.10:8765
name = Conan
```

## Keys

| Key    | Type   | Required | Description                                   |
|--------|--------|----------|-----------------------------------------------|
| server | string | No       | Default server address in `host:port` form    |
| name   | string | No       | Default display name                          |

## Location

Same directory as the running process:

- **Packaged binary**: directory containing `risus[.exe]`
- **Source run**: project root (same directory as `risus.py`)

Filename: `risus.cfg` (case-sensitive on Linux/macOS).

## Behaviour Rules

### Read (startup)

1. File absence is not an error — startup continues with no defaults.
2. Missing `[risus]` section or key → treated as absent (no default shown).
3. Malformed `server` value is passed through unchanged; connection failure
   is reported at connect time, not at parse time.
4. File is read once at startup; runtime changes require restart.
5. CLI arguments always override config file values.

### Write (on normal exit)

1. On normal exit the client writes both `server` and `name` using the
   values entered or provided by the player for that session.
2. If the file does not exist it is created; if it exists it is overwritten.
3. Write errors (permissions, read-only filesystem) are silently ignored —
   the application closes normally regardless.
4. Forceful termination (SIGKILL, Task Manager kill) skips the write; the
   file retains values from the last successful write.

## Distributed Files

| File               | Purpose                        | Git status   |
|--------------------|--------------------------------|--------------|
| `risus.cfg`        | Player's local config          | `.gitignore` |
| `risus.cfg.example`| Template bundled in the repo   | Committed    |

`risus.cfg.example` content:

```ini
[risus]
# Default server address (host:port). Updated automatically on exit.
# Copy this file to risus.cfg to set initial defaults.
server = localhost:8765
# Default display name. Updated automatically on exit.
# name = YourName
```
