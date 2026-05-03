# Contract: Release Artifact

**Phase**: 1 | **Date**: 2026-05-03

Defines the contract for the macOS release artifact produced by the GitHub Actions release workflow.

## Artifact Naming

| Platform | Artifact filename | Checksum filename |
|----------|------------------|------------------|
| macOS arm64 | `risus-macos-arm64.zip` | `risus-macos-arm64.zip.sha256` |

The zip contains: `risus-macos-arm64` (signed binary).

## Verification Commands

After downloading `risus-macos-arm64.zip` and extracting `risus-macos-arm64`:

```bash
# Verify code signature
codesign --verify --deep --strict --verbose=2 risus-macos-arm64

# Verify Gatekeeper acceptance (no privacy exceptions required)
spctl --assess --type execute --verbose risus-macos-arm64

# Expected output from spctl:
# risus-macos-arm64: accepted
# source=Notarized Developer ID
```

## Signing Identity

```
Developer ID Application: <DEVELOPER_NAME> (<TEAM_ID>)
```

## Required GitHub Actions Secrets

| Secret name | Description |
|-------------|-------------|
| `APPLE_CERTIFICATE` | Base64-encoded `.p12` Developer ID Application certificate |
| `APPLE_CERTIFICATE_PASSWORD` | Passphrase for the `.p12` file |
| `APPLE_TEAM_ID` | 10-character Apple Developer team identifier |
| `APPLE_API_KEY_ID` | App Store Connect API key ID (10 chars) |
| `APPLE_API_ISSUER_ID` | App Store Connect issuer UUID |
| `APPLE_API_KEY_CONTENT` | Base64-encoded `.p8` API key file content |

## Failure Modes

| Failure | CI behaviour |
|---------|-------------|
| `codesign` exits non-zero | Job fails; no artifact uploaded |
| `notarytool` returns non-zero (Apple rejects or service error) | Job fails; no artifact uploaded |
| Certificate expired or revoked | `codesign` fails fast with non-zero exit |
