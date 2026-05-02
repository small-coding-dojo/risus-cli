# Data Model: Standalone Client Distribution

**Date**: 2026-05-02 | **Feature**: 003-standalone-client

## Runtime Entities

### ConfigFile

Read at startup and written on normal exit by `client/config.py`. Players
may also edit it manually between sessions.

| Field          | Type           | Description                                      |
|----------------|----------------|--------------------------------------------------|
| server_address | string or None | `host:port` default, e.g. `localhost:8765`       |
| display_name   | string or None | Last-used display name default                   |

**Location**: Same directory as the running executable (or project root
when running from source). Filename: `risus.cfg`.

**Format**: INI with a `[risus]` section:

```ini
[risus]
server = localhost:8765
name = Conan
```

**Validation rules**:

- If the file is absent, `server_address` is `None` (prompt shows no
  default).
- If the `[risus]` section or `server` key is absent, `server_address` is
  `None`.
- Malformed values are passed through as-is; connection failure is reported
  at connect time, not at read time.
- The file is read once per startup; changes require restarting the client.
- On normal exit the application writes both `server` and `name` back to
  the file. If the file does not exist it is created. Write errors are
  silently ignored.

## Build-Time Entities

### DistributablePackage

Produced by the CI build process. Not stored by the application.

| Field        | Type   | Description                                      |
|--------------|--------|--------------------------------------------------|
| name         | string | `risus-{os}-{arch}[.exe]`                        |
| os           | enum   | `linux` \| `macos` \| `windows`                  |
| arch         | enum   | `x86_64` \| `arm64`                              |
| version      | string | Semver tag from git (e.g., `0.1.0`)              |
| sha256       | string | Hex digest for integrity verification            |
| release_url  | string | GitHub Release asset download URL                |

### BuildArtifact

Intermediate output produced by PyInstaller. Discarded after upload.

| Field        | Type   | Description                                      |
|--------------|--------|--------------------------------------------------|
| path         | string | Local path (`dist/risus[.exe]`)                  |
| platform     | string | Runner OS label from CI matrix                   |
| size_bytes   | int    | Verified non-zero before upload                  |

## State Transitions (CI workflow)

```text
source code
    │
    ▼ (build-job per platform)
BuildArtifact (local to runner)
    │
    ▼ (upload-artifact)
GitHub Actions artifact store
    │
    ▼ (create-release job)
DistributablePackage (GitHub Release asset)
```

## Startup + Exit Flow (runtime)

```text
executable launched
    │
    ├─ CLI arg: server? ──yes──► use arg
    │                  no
    │                   ▼
    │            read ConfigFile
    │                   │
    │            server_address?
    │            ├─ Some(v) ──► prompt "Server address [v]: "
    │            └─ None   ──► prompt "Server address: "
    │                   │
    │            player input (re-prompt if empty; Enter accepts default)
    │                   ▼
    ├─ CLI arg: name? ──yes──► use arg
    │                 no
    │                  ▼
    │            display_name? (from ConfigFile)
    │            ├─ Some(n) ──► prompt "Your name [n]: "
    │            └─ None   ──► prompt "Your name: "
    │                   │
    │            player input (re-prompt if empty; Enter accepts default)
    │                   ▼
    │     register atexit: write(server, name) → risus.cfg (silent on error)
    │                   ▼
    └──────────► connect(server, name)
                        │
                  [session runs]
                        │
                  normal exit
                        │
                  atexit fires ──► write ConfigFile(server, name)
                                   (silently ignored on error)
```
