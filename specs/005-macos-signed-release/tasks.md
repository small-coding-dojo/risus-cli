# Tasks: macOS Signed Release

**Input**: Design documents from `/specs/005-macos-signed-release/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Organization**: Tasks grouped by user story. No tests requested in spec — no test tasks generated.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: New build artifact required before any signing step can run.

- [x] T001 Create `build/entitlements.plist` with 4 entitlements required for PyInstaller Python runtime under Hardened Runtime: `com.apple.security.cs.allow-jit`, `com.apple.security.cs.allow-unsigned-executable-memory`, `com.apple.security.cs.allow-dyld-environment-variables`, `com.apple.security.cs.disable-library-validation` (all `true`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Certificate import into CI keychain — MUST complete before any `codesign` call.

**⚠️ CRITICAL**: T002 must be complete before US1 signing steps can run.

- [x] T002 Add `apple-actions/import-codesign-certs@v7` step (`if: runner.os == 'macOS'`) to macOS matrix job in `.github/workflows/release.yml` with `p12-file-base64: ${{ secrets.APPLE_CERTIFICATE }}` and `p12-password: ${{ secrets.APPLE_CERTIFICATE_PASSWORD }}` — action handles keychain creation, import, and cleanup automatically; T003 no longer needed

**Checkpoint**: Keychain lifecycle in place — US1 signing steps can now be added.

---

## Phase 3: User Story 1 - Run CLI Without Security Prompts (Priority: P1) 🎯 MVP

**Goal**: End user downloads and runs the CLI on macOS with zero Gatekeeper dialogs or System Settings steps.

**Independent Test**: Download `risus-macos-arm64.zip` from GitHub Release, extract, run `spctl --assess --type execute --verbose risus-macos-arm64` — output must show `accepted` and `source=Notarized Developer ID`.

### Implementation for User Story 1

- [x] T004 [US1] Add `codesign --force --verbose --timestamp --sign "Developer ID Application: $APPLE_TEAM_ID" --options=runtime --no-strict --entitlements build/entitlements.plist dist/risus-macos-arm64` step (`if: runner.os == 'macOS'`) after binary rename in `.github/workflows/release.yml`
- [x] T005 [US1] Add `ditto -c -k --keepParent dist/risus-macos-arm64 dist/risus-macos-arm64.zip` step (`if: runner.os == 'macOS'`) after signing in `.github/workflows/release.yml`
- [x] T006 [US1] Add `xcrun notarytool submit dist/risus-macos-arm64.zip --wait --key /tmp/apple_api_key.p8 --key-id $APPLE_API_KEY_ID --issuer $APPLE_API_ISSUER_ID` step (`if: runner.os == 'macOS'`, `timeout-minutes: 15`) in `.github/workflows/release.yml` — decode `APPLE_API_KEY_CONTENT` to `/tmp/apple_api_key.p8` before calling notarytool, delete the file after
- [x] T007 [US1] Update the "Compute checksum (Unix)" step in `.github/workflows/release.yml` to hash `risus-macos-arm64.zip` on macOS (not the bare binary) — use `if: runner.os == 'macOS'` for the new step and `if: runner.os == 'Linux'` for the existing Linux step
- [x] T008 [US1] Update the macOS artifact upload step in `.github/workflows/release.yml` — change `path` to upload `dist/risus-macos-arm64.zip` and `dist/risus-macos-arm64.zip.sha256` instead of the bare binary

**Checkpoint**: Tag a release and confirm the macOS artifact in GitHub Releases is `risus-macos-arm64.zip`, passes `spctl --assess`, and requires no System Settings exception.

---

## Phase 4: User Story 2 - Developer Produces Notarized Artifact (Priority: P2)

**Goal**: Developer can verify the artifact is correctly signed and notarized using standard macOS tooling.

**Independent Test**: Run `codesign --verify --deep --strict --verbose=2 risus-macos-arm64` and `spctl --assess --type execute --verbose risus-macos-arm64` against the downloaded artifact — both commands exit 0.

### Implementation for User Story 2

- [x] T009 [US2] Add post-notarization verification step (`if: runner.os == 'macOS'`) in `.github/workflows/release.yml` — run `codesign --verify --deep --strict --verbose=2 dist/risus-macos-arm64` and `spctl --assess --type execute --verbose dist/risus-macos-arm64`; job fails if either command exits non-zero
- [x] T010 [P] [US2] Add "Signing Setup" subsection to the Release Checklist in `AGENTS.md` documenting the 6 required GitHub Actions secrets (`APPLE_CERTIFICATE`, `APPLE_CERTIFICATE_PASSWORD`, `APPLE_TEAM_ID`, `APPLE_API_KEY_ID`, `APPLE_API_ISSUER_ID`, `APPLE_API_KEY_CONTENT`) and how to obtain each (reference `specs/005-macos-signed-release/quickstart.md` for full setup steps)

**Checkpoint**: CI run produces a verifiable artifact; developer can confirm signing with `codesign` and `spctl` without any manual steps.

---

## Phase 5: User Story 3 - CI/CD Consistent Notarized Artifacts (Priority: P3)

**Goal**: Every tagged release automatically produces a notarized macOS artifact via GitHub Actions without developer intervention.

**Independent Test**: Push a tag to a branch with secrets configured — GitHub Actions macOS job completes without manual steps and the release asset is `risus-macos-arm64.zip` with `source=Notarized Developer ID`.

### Implementation for User Story 3

- [x] T011 [US3] Update `on.push.branches` in `.github/workflows/build.yml` to add `005-macos-signed-release` so CI runs on this feature branch during development
- [x] T012 [P] [US3] Add a pre-tag check to the Release Checklist in `AGENTS.md`: verify all 6 Apple signing secrets are configured in repository Settings → Secrets before pushing a release tag

**Checkpoint**: Tagged release with secrets configured completes notarization automatically; secrets missing causes clear CI failure before any artifact is uploaded.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Documentation and release checklist hygiene.

- [x] T013 [P] Update the macOS entry in the release workflow job name in `.github/workflows/release.yml` from `Build (macos-latest)` to `Build & Sign (macos-latest)` for clarity in the GitHub Actions UI
- [ ] T014 Run manual end-to-end verification per `specs/005-macos-signed-release/quickstart.md` against the first notarized release artifact

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on T001 (entitlements must exist before signing) — **blocks all US phases**
- **US1 (Phase 3)**: Depends on T001, T002, T003 — core delivery
- **US2 (Phase 4)**: T009 depends on T006 (notarization must exist before verify step); T010 is independent [P]
- **US3 (Phase 5)**: T011 and T012 are independent [P] of US1/US2 implementation
- **Polish (Phase N)**: Depends on all US phases complete

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational (T001–T003) — no dependency on US2/US3
- **US2 (P2)**: T009 depends on US1 workflow steps existing; T010 is independent
- **US3 (P3)**: Independent of US1/US2 — parallel with either

### Within US1

- T004 (sign) → T005 (zip) → T006 (notarize) → T007 (checksum) → T008 (upload): strictly sequential

---

## Parallel Opportunities

```bash
# Phase 1+2 can start in parallel with US3 tasks:
Task: T001 "Create build/entitlements.plist"
Task: T011 "Update build.yml branches list"
Task: T012 "Add pre-tag secrets check to AGENTS.md"

# After Foundational complete, T010 runs in parallel with T004-T008:
Task: T010 "Add signing setup subsection to AGENTS.md"
Task: T004-T008 "US1 workflow signing steps (sequential)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete T001 (entitlements file)
2. Complete T002–T003 (keychain lifecycle)
3. Complete T004–T008 (sign, zip, notarize, checksum, upload)
4. **STOP and VALIDATE**: push a test tag, confirm `spctl --assess` returns `accepted`
5. Add T009 (verification step) and T010 (docs)

### Incremental Delivery

1. T001 → T002–T003 → T004–T008 → validate (US1 complete, users unblocked)
2. T009 → T010 → validate (US2 complete, repeatable workflow documented)
3. T011 → T012 → validate (US3 complete, CI automation confirmed)
4. T013–T014 (polish)

---

## Notes

- All signing steps require `if: runner.os == 'macOS'` guards — Linux/Windows matrix jobs are unchanged
- `APPLE_TEAM_ID` is used in the signing identity string: `"Developer ID Application: $(APPLE_TEAM_ID)"` — confirm the exact identity string from `security find-identity -v -p codesigning` on the developer machine
- `xcrun notarytool submit --wait` typically takes 1–5 minutes; the 15-minute SC-004 limit is well within GitHub Actions job timeout defaults
- Keychain cleanup step uses `if: always()` so it runs even if signing or notarization fails
- The bare-binary artifact (`risus-macos-arm64`) is no longer uploaded; only the zip is distributed
