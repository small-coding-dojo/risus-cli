# Feature Specification: macOS Signed Release

**Feature Branch**: `005-macos-signed-release`
**Created**: 2026-05-03
**Status**: Draft
**Input**: User description: "The macOS release shall not require the user to configure privacy exceptions. The developer is enrolled in the apple developer program."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run CLI Without Security Prompts (Priority: P1)

A macOS user downloads the Risus CLI release artifact and runs it immediately without needing to visit System Settings or approve any security exception.

**Why this priority**: Any security prompt is a blocker — users who do not know how to bypass Gatekeeper cannot use the tool at all. This is the primary acceptance gate.

**Independent Test**: Download the release artifact on a clean macOS machine, double-click or execute it in Terminal, and verify it runs without any "unidentified developer" dialog, Gatekeeper block, or privacy exception prompt. Delivers a fully usable CLI out of the box.

**Acceptance Scenarios**:

1. **Given** a macOS user downloads the release artifact, **When** they run it from Terminal for the first time, **Then** the CLI launches without any Gatekeeper warning or security exception dialog.
2. **Given** a macOS user is on macOS 13 (Ventura) or later, **When** they execute the artifact, **Then** macOS does not quarantine or block execution.
3. **Given** the artifact is downloaded via a browser, **When** the user runs it immediately, **Then** no "open anyway" step in System Settings is required.

---

### User Story 2 - Developer Produces a Notarized Release Artifact (Priority: P2)

A developer with an Apple Developer Program account runs the release process and produces an artifact that is code-signed and notarized, ready for distribution.

**Why this priority**: Without a repeatable notarization workflow the P1 user story cannot be fulfilled on each release.

**Independent Test**: Run the release build process in a macOS environment with valid Apple Developer credentials. Verify the produced artifact passes `spctl` assessment and carries a valid code signature. Delivers a distributable binary independent of any end-user steps.

**Acceptance Scenarios**:

1. **Given** a developer has valid Apple Developer Program credentials configured, **When** the release build process runs, **Then** it produces a signed and notarized artifact without manual intervention.
2. **Given** the produced artifact, **When** `spctl --assess` is run against it, **Then** the assessment passes with `accepted` status.
3. **Given** the produced artifact, **When** `codesign --verify` is run against it, **Then** the signature is valid and the signing identity is a trusted Apple Developer ID.

---

### User Story 3 - CI/CD Produces Consistent Notarized Artifacts (Priority: P3)

The CI/CD pipeline produces a notarized macOS artifact on each tagged release without developer manual steps beyond providing credentials as secrets.

**Why this priority**: Automates the notarization workflow so releases are repeatable and not gated on a specific developer's machine.

**Independent Test**: Trigger a tagged release in CI. Confirm the produced macOS artifact in the release assets is notarized. Delivers automation independent of local developer environment.

**Acceptance Scenarios**:

1. **Given** a tagged release is pushed, **When** the CI pipeline runs, **Then** the macOS artifact in release assets is signed and notarized.
2. **Given** Apple Developer credentials are stored as CI secrets, **When** the pipeline runs, **Then** signing and notarization succeed without interactive input.

---

### Edge Cases

- What happens if the Apple notarization service is temporarily unavailable during CI?
- How does the artifact behave on macOS versions older than the minimum supported version?
- What if the Developer ID certificate is expired or revoked — does the build fail fast with a clear error?
- What happens if the user copies the artifact to another macOS machine — does the signature remain valid?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The macOS release artifact MUST be code-signed with a valid Apple Developer ID Application certificate.
- **FR-002**: The macOS release artifact MUST be submitted to Apple for notarization and approved; Gatekeeper verifies the notarization record online on first run.
- **FR-003**: The artifact MUST pass `spctl --assess` on a clean macOS system without any user-configured security exceptions.
- **FR-004**: The release build process MUST accept Apple Developer credentials (Team ID, certificate, App-specific password or API key) via environment variables or secrets — no hard-coded credentials.
- **FR-005**: The release process MUST fail with a clear error if code-signing or notarization fails, preventing distribution of an unsigned artifact.
- **FR-006**: The CI/CD pipeline MUST produce the notarized macOS artifact automatically on each tagged release.
- **FR-007**: The artifact MUST run on the latest macOS release without additional configuration by the user.

### Key Entities

- **Release Artifact**: The distributable macOS binary or archive of the Risus CLI, packaged for end-user download.
- **Developer ID Certificate**: The Apple-issued code-signing certificate associated with the enrolled Apple Developer Program account.
- **Notarization Ticket**: Apple's cryptographic attestation stapled to the artifact confirming it passed security checks.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A fresh macOS user can download and run the CLI in under 60 seconds with zero security dialogs or System Settings steps.
- **SC-002**: 100% of tagged releases produce a notarized macOS artifact via the automated pipeline.
- **SC-003**: `spctl --assess` returns `accepted` on every distributed artifact.
- **SC-004**: The release build process completes notarization in under 15 minutes per release.
- **SC-005**: Zero support requests related to macOS Gatekeeper or "unidentified developer" blocks after the feature ships.

## Assumptions

- Developer is enrolled in the Apple Developer Program and has access to a valid Developer ID Application certificate.
- Credentials (Team ID, certificate, signing password) will be provided as CI secrets — not stored in the repository.
- The CLI is distributed as a standalone binary or archive (e.g., via GitHub Releases), not through the Mac App Store, so Developer ID signing applies rather than App Store signing.
- Only the latest macOS release is supported; older versions are out of scope.
- The existing CI/CD platform (GitHub Actions or equivalent) supports macOS runners capable of running the signing and notarization tools.
- No entitlements beyond what is required for a command-line tool are needed (no camera, microphone, or other privacy-sensitive access).
