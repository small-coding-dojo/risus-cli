# Research: macOS Signed Release

**Phase**: 0 | **Date**: 2026-05-03

## Decision 1: PyInstaller Binary Signing

- **Decision**: Sign the PyInstaller single-file binary directly with `codesign --force --verbose --timestamp --sign "Developer ID Application: TEAM_NAME (TEAM_ID)" --options=runtime --no-strict --entitlements build/entitlements.plist`.
- **Rationale**: PyInstaller produces a single Mach-O executable. `--options runtime` enables Hardened Runtime (prerequisite for notarization). `--timestamp` embeds Apple's secure timestamp so the signature remains valid after certificate expiry. `--no-strict` avoids false validation errors on PyInstaller's internal structure. `--deep` is omitted — it is unnecessary for a single-file binary and can cause signing errors.
- **Alternatives considered**: Signing a `.app` bundle — unnecessary overhead for a CLI tool with no GUI.

## Decision 2: Entitlements

- **Decision**: Provide `build/entitlements.plist` with 4 entitlements: `com.apple.security.cs.allow-jit`, `com.apple.security.cs.allow-unsigned-executable-memory`, `com.apple.security.cs.allow-dyld-environment-variables`, `com.apple.security.cs.disable-library-validation` (all `true`).
- **Rationale**: PyInstaller embeds a Python runtime. Under Hardened Runtime, macOS enforces strict memory and library constraints that the Python interpreter requires relaxing: JIT for bytecode execution, unsigned executable memory for Python's allocator, DYLD variables for Python path resolution, and disabled library validation because embedded libraries are not individually Apple-signed. This set is confirmed by the malimo project (same signing approach for a .NET self-contained binary, analogous constraints).
- **Alternatives considered**: Using only `disable-library-validation` — insufficient; Python runtime also needs the JIT and memory entitlements. Signing all embedded libraries individually — impractical with PyInstaller's bundle structure.

## Decision 3: Notarization Authentication

- **Decision**: Use App Store Connect API key (`.p8` file) with `xcrun notarytool submit --key-id ... --issuer-id ... --key ...`.
- **Rationale**: API key authentication is stateless, requires no 2FA, and is the recommended approach for CI/CD. Apple ID + app-specific password requires storing an Apple ID email as a secret and can be blocked by Apple's security systems.
- **Alternatives considered**: Apple ID + app-specific password — works but requires more secrets and is more fragile in automated environments. Both approaches produce identical notarization results.
- **Secrets required**:
  - `APPLE_API_KEY_ID` — 10-character key ID from App Store Connect
  - `APPLE_API_ISSUER_ID` — UUID issuer ID from App Store Connect
  - `APPLE_API_KEY_CONTENT` — base64-encoded `.p8` key file content

## Decision 4: Notarization Submission Format

- **Decision**: Zip the signed binary (`ditto -c -k --keepParent`) and submit the zip to `xcrun notarytool submit --wait`.
- **Rationale**: `notarytool` requires a zip, `.dmg`, or `.pkg` — not a bare binary. A zip is the simplest wrapper. `--wait` blocks until Apple completes the scan (typically 1–5 minutes), simplifying the CI step.
- **Alternatives considered**: `.pkg` wrapper — enables stapling (ticket embedded in artifact for offline Gatekeeper checks), but adds packaging complexity. Since the spec requires no privacy exceptions on download (not offline use), a zip with online Gatekeeper verification satisfies all requirements.

## Decision 5: Stapling

- **Decision**: Do not staple. Distribute the notarized zip as-is.
- **Rationale**: `xcrun stapler` cannot staple a notarization ticket to a bare binary or a zip archive — only to `.app`, `.dmg`, and `.pkg` files. On first run, macOS Gatekeeper performs an online check against Apple's notarization database and passes the binary. This satisfies FR-003 (`spctl --assess` accepted) without any user privacy exception.
- **Alternatives considered**: Wrapping in `.dmg` or `.pkg` to enable stapling — provides offline Gatekeeper verification but adds significant packaging steps. Out of scope per Simplicity principle; the spec does not require offline use.

## Decision 6: Certificate Import in CI

- **Decision**: Use `apple-actions/import-codesign-certs@v7` GitHub Action to import the `.p12` certificate.
- **Rationale**: The action handles temporary keychain creation, certificate import, partition list configuration, and cleanup automatically. Eliminates ~15 lines of fragile bash. Confirmed working in malimo project with identical secrets layout.
- **Secrets required**:
  - `APPLE_CERTIFICATE` — base64-encoded `.p12` Developer ID Application certificate
  - `APPLE_CERTIFICATE_PASSWORD` — passphrase for the `.p12` file
  - `APPLE_TEAM_ID` — 10-character team identifier (used in the signing identity string)

## Resolved Clarifications

All NEEDS CLARIFICATION items from the spec have been resolved:
- Notarization service unavailability: `xcrun notarytool submit --wait` exits non-zero on Apple service errors; GitHub Actions will mark the job failed and no artifact is uploaded (satisfies FR-005).
- Certificate expiry: `codesign` fails fast with a non-zero exit code if the certificate is invalid or expired.
- Artifact portability: The notarization record is tied to the binary's hash in Apple's database; copying to another machine preserves the signature and Gatekeeper performs the same online check.
