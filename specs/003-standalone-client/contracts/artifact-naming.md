# Contract: Artifact Naming

**Feature**: 003-standalone-client | **Date**: 2026-05-02

## Purpose

Defines the canonical name for each platform's distributable binary so
players and automation can unambiguously identify the correct file to download.

## Pattern

```text
risus-{os}-{arch}[.exe]
```

## Values

| OS      | arch    | Filename                  | Runner label         |
|---------|---------|---------------------------|----------------------|
| linux   | x86_64  | `risus-linux-x86_64`      | `ubuntu-latest`      |
| macos   | x86_64  | `risus-macos-x86_64`      | `macos-13`           |
| macos   | arm64   | `risus-macos-arm64`       | `macos-latest`       |
| windows | x86_64  | `risus-windows-x86_64.exe`| `windows-latest`     |

## Rules

1. The `.exe` suffix MUST be appended for Windows artifacts only.
2. The artifact name MUST NOT include a version string — version is conveyed
   by the GitHub Release tag that contains the asset.
3. CI MUST rename the PyInstaller output (`dist/risus[.exe]`) to the
   canonical name before uploading.
4. A checksum file `{artifact-name}.sha256` MUST be published alongside each
   binary in the release.

## Checksum File Format

```text
<hex-sha256>  <artifact-name>
```

Example:

```text
d3b4c2a1...  risus-linux-x86_64
```

## Versioning

The GitHub Release tag (e.g., `v0.2.0`) is the version identifier. There is
no version embedded in the binary filename. Players who need to verify their
version can run:

```bash
./risus-linux-x86_64 --version   # if --version flag is implemented
```

or check the release page from which they downloaded the file.
