# Feature Specification: macOS Zip Directory Structure

**Feature Branch**: `006-zip-directory-structure`
**Created**: 2026-05-04
**Status**: Draft
**Input**: "When unzipping the release for macOS, the files shall be unzipped into a directory named as the basename of the zip file."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Unzip Produces Named Directory (Priority: P1)

A macOS user downloads `risus-macos-arm64.zip` and unzips it. The result is a directory named `risus-macos-arm64` containing the binary — not a `dist` directory or bare file.

**Why this priority**: Users who double-click the zip or run `unzip` get a sensible directory layout. A `dist/` directory appearing in the user's Downloads folder is confusing and looks like a build artifact leak.

**Independent Test**: Download `risus-macos-arm64.zip`, run `unzip risus-macos-arm64.zip`, confirm the result is `risus-macos-arm64/risus-macos-arm64` (directory named after the zip basename containing the binary).

**Acceptance Scenarios**:

1. **Given** a user unzips `risus-macos-arm64.zip`, **When** extraction completes, **Then** a directory named `risus-macos-arm64` exists containing the binary `risus-macos-arm64`.
2. **Given** a user double-clicks the zip in Finder, **When** extraction completes, **Then** a folder named `risus-macos-arm64` appears — no `dist` folder.
3. **Given** the zip file, **When** `unzip -l risus-macos-arm64.zip` is run, **Then** the listing shows `risus-macos-arm64/risus-macos-arm64` (not `dist/risus-macos-arm64`).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The macOS release zip MUST unzip into a directory whose name matches the zip file basename (`risus-macos-arm64`).
- **FR-002**: The binary inside the zip MUST be at path `risus-macos-arm64/risus-macos-arm64` within the archive.
- **FR-003**: The zip MUST remain a valid signed artifact — the binary inside must pass `codesign --verify` after extraction.
- **FR-004**: The sha256 checksum file MUST be recomputed after the zip is rebuilt with the new structure.

### Key Entities

- **Release Zip**: `risus-macos-arm64.zip` — the distributable macOS archive uploaded to GitHub Releases.
- **Staging Directory**: Temporary directory used during CI to produce the correct zip structure before signing/packaging.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `unzip -l risus-macos-arm64.zip` lists `risus-macos-arm64/risus-macos-arm64` as the only entry (or top-level directory).
- **SC-002**: After extraction, `codesign --verify --deep --strict risus-macos-arm64/risus-macos-arm64` exits 0.
- **SC-003**: No `dist/` directory appears in the zip or after extraction.

## Assumptions

- Only the macOS artifact is affected — Linux and Windows artifacts are bare binaries, unchanged.
- The binary filename inside the zip remains `risus-macos-arm64` (same as the zip basename).
- Change is confined to the `ditto` packaging step in `.github/workflows/release.yml`.
