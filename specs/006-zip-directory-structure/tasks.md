# Tasks: macOS Zip Directory Structure

**Input**: Design documents from `/specs/006-zip-directory-structure/`
**Prerequisites**: plan.md ✅, spec.md ✅

---

## Phase 1: Implementation

- [ ] T001 Update the `Package signed binary` step in `.github/workflows/release.yml` — replace the single `ditto` line with a 4-line sequence: (1) `mkdir -p /tmp/risus-macos-arm64`, (2) `cp dist/risus-macos-arm64 /tmp/risus-macos-arm64/`, (3) `ditto -c -k --keepParent /tmp/risus-macos-arm64 dist/risus-macos-arm64.zip`, (4) `rm -rf /tmp/risus-macos-arm64`

---

## Phase 2: Verification

- [ ] T002 After next tagged release, run `unzip -l risus-macos-arm64.zip` on the downloaded artifact — confirm top-level entry is `risus-macos-arm64/` (not `dist/`); run `codesign --verify --deep --strict risus-macos-arm64/risus-macos-arm64` — exits 0

---

## Dependencies

- T001 has no dependencies — change is isolated to one step
- T002 depends on T001 and a successful tagged release

## Acceptance

SC-001: `unzip -l` shows `risus-macos-arm64/risus-macos-arm64`
SC-002: `codesign --verify` exits 0 after extraction
SC-003: No `dist/` in the zip or after extraction
