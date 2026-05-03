# Implementation Plan: macOS Signed Release

**Branch**: `005-macos-signed-release` | **Date**: 2026-05-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-macos-signed-release/spec.md`

## Summary

Add Apple code signing and notarization to the macOS job in the existing GitHub Actions release workflow. The binary is built with PyInstaller, signed with a Developer ID Application certificate (hardened runtime + minimal entitlements), zipped, submitted to Apple's notarization service, and distributed as a notarized zip. Gatekeeper verifies the notarization ticket online on first run — no user privacy exceptions required. No runtime code changes.

## Technical Context

**Language/Version**: Python 3.12  
**Build Tool**: PyInstaller 6 (single-file binary, `build/risus.spec`)  
**CI Platform**: GitHub Actions (`macos-latest` runner = Apple Silicon, arm64)  
**Signing Tool**: `codesign` (Xcode Command Line Tools, pre-installed on macOS runners)  
**Notarization Tool**: `xcrun notarytool` (Xcode 13+, pre-installed on macOS runners)  
**Storage**: N/A  
**Testing**: Manual verification via `spctl --assess` and `codesign --verify` on produced artifact  
**Target Platform**: Latest macOS release, arm64 (`macos-latest` runner)  
**Project Type**: CLI binary distribution  
**Performance Goals**: Notarization completes within 15 minutes per release  
**Constraints**: No hard-coded credentials; certificate and API key via GitHub Actions secrets only  
**Scale/Scope**: One artifact per tagged release; macOS runner only (Linux and Windows jobs unchanged)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Server Authority | ✅ PASS | Build/release concern only; no runtime state changes |
| II. Simplicity | ✅ PASS | Touches only `release.yml` (macOS job) and adds `build/entitlements.plist`; zero UX or menu changes |
| III. No Duplication | ✅ PASS | Signing logic lives in one place (`release.yml` macOS job) |
| IV. Testing Discipline | ✅ PASS | No new runtime code; verification via `spctl --assess` on artifact |
| V. No Local Persistence | ✅ PASS | Build artifact, not runtime state |

No violations. Complexity Tracking table omitted.

## Project Structure

### Documentation (this feature)

```text
specs/005-macos-signed-release/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── release-artifact.md   # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
build/
├── risus.spec           # Existing PyInstaller spec (unchanged)
└── entitlements.plist   # NEW: minimal entitlements for signed binary

.github/workflows/
└── release.yml          # MODIFIED: macOS job gains signing + notarization steps
```

**Structure Decision**: Single-project layout. Only build tooling files change; no src/ changes.
