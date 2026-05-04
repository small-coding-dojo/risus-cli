# Implementation Plan: macOS Zip Directory Structure

**Branch**: `006-zip-directory-structure` | **Date**: 2026-05-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/006-zip-directory-structure/spec.md`

## Summary

Fix the macOS release zip so that extracting `risus-macos-arm64.zip` produces a directory named `risus-macos-arm64` (containing the binary) rather than a `dist` directory. The fix is a one-step change to the `ditto` packaging command in `release.yml`: stage the binary into a temporary directory with the correct name before zipping.

## Technical Context

**Language/Version**: Python 3.12 (build only — no runtime change)
**CI Platform**: GitHub Actions (`macos-latest` runner)
**Packaging Tool**: `ditto` (pre-installed on macOS runners)
**Constraint**: Binary must remain signed after repackaging — `ditto` preserves extended attributes and signatures
**Scale/Scope**: One-line change in `.github/workflows/release.yml`; no src/ or entitlements changes

## Root Cause

`ditto -c -k --keepParent dist/risus-macos-arm64 dist/risus-macos-arm64.zip` preserves the full path `dist/risus-macos-arm64` inside the archive. Unzipping produces `dist/risus-macos-arm64` — the `dist/` prefix is an artifact of the CI build directory layout.

## Fix

Stage the binary into `/tmp/risus-macos-arm64/` before zipping:

```bash
mkdir -p /tmp/risus-macos-arm64
cp dist/risus-macos-arm64 /tmp/risus-macos-arm64/
ditto -c -k --keepParent /tmp/risus-macos-arm64 dist/risus-macos-arm64.zip
rm -rf /tmp/risus-macos-arm64
```

`--keepParent` now preserves `/tmp/risus-macos-arm64` → zip entry becomes `risus-macos-arm64/risus-macos-arm64`. `ditto` preserves the code signature extended attributes during the copy.

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Server Authority | ✅ PASS | Build/release concern only |
| II. Simplicity | ✅ PASS | Single step change in release.yml |
| III. No Duplication | ✅ PASS | Packaging logic in one place |
| IV. Testing Discipline | ✅ PASS | Verified via `unzip -l` and `codesign --verify` |
| V. No Local Persistence | ✅ PASS | Temp dir cleaned up in same step |

## Project Structure

Only `.github/workflows/release.yml` changes (the `Package signed binary` step).

## Notes

- `ditto` preserves extended attributes including code signature — copy does not break signing
- `/tmp/` is writable on GitHub Actions macOS runners
- Cleanup (`rm -rf`) runs in the same shell step — no orphaned temp dirs
- Checksum is computed after the zip is created, so sha256 automatically reflects the new structure
