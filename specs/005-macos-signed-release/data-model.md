# Data Model: macOS Signed Release

**Phase**: 1 | **Date**: 2026-05-03

This feature has no runtime data model changes. The entities below describe the build-time and distribution artifacts.

## Entities

### Release Artifact

The distributable file produced by the macOS release job.

| Attribute | Value |
|-----------|-------|
| Name | `risus-macos-arm64.zip` |
| Contents | Signed, notarized `risus-macos-arm64` binary |
| Signing identity | Developer ID Application certificate (Developer ID Application: NAME (TEAM_ID)) |
| Hardened runtime | Enabled (`--options runtime`) |
| Entitlements | `com.apple.security.cs.disable-library-validation: true` |
| Notarization | Submitted and approved by Apple's notarization service |
| Gatekeeper result | `accepted` via online check on first run |

### Developer ID Certificate

| Attribute | Value |
|-----------|-------|
| Type | Developer ID Application (not Distribution, not App Store) |
| Format | `.p12` PKCS#12 archive |
| Storage | GitHub Actions secret `APPLE_CERTIFICATE` (base64-encoded) |
| Passphrase secret | `APPLE_CERTIFICATE_PASSWORD` |
| Keychain | Temporary per-job keychain, deleted after job |

### App Store Connect API Key

Used exclusively for `xcrun notarytool` authentication.

| Attribute | Value |
|-----------|-------|
| Format | `.p8` private key file |
| Key ID | GitHub Actions secret `APPLE_API_KEY_ID` |
| Issuer ID | GitHub Actions secret `APPLE_API_ISSUER_ID` |
| Content | GitHub Actions secret `APPLE_API_KEY_CONTENT` (base64-encoded) |

### Entitlements File

| Attribute | Value |
|-----------|-------|
| Path | `build/entitlements.plist` |
| Format | Apple property list (XML) |
| Entitlements | `allow-jit`, `allow-unsigned-executable-memory`, `allow-dyld-environment-variables`, `disable-library-validation` (all `true`) |
| Rationale | Python runtime under Hardened Runtime requires all four; see research.md Decision 2 |

## State Transitions

```
Binary built (unsigned)
  → codesign applied (signed, hardened runtime)
    → zipped
      → notarytool submitted
        → Apple scan: pass
          → notarization approved (ticket in Apple DB)
            → zip uploaded to GitHub Release
              → user downloads → Gatekeeper online check → accepted → binary runs
```
