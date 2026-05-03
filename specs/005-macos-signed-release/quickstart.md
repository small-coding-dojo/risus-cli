# Quickstart: macOS Signed Release

**Date**: 2026-05-03

## What changes

- `build/entitlements.plist` — new file; minimal entitlements for the signed binary
- `.github/workflows/release.yml` — macOS job gains certificate import, codesign, notarization, and zip steps

Linux and Windows jobs are unchanged.

## Prerequisites (one-time developer setup)

1. **Export Developer ID Application certificate** from Keychain Access as `.p12` with a strong passphrase.
2. **Base64-encode the certificate**:
   ```bash
   base64 -i DeveloperIDApplication.p12 | pbcopy
   ```
3. **Create an App Store Connect API key** at [appstoreconnect.apple.com](https://appstoreconnect.apple.com) → Users and Access → Integrations → App Store Connect API. Download the `.p8` file (downloadable once only).
4. **Base64-encode the API key**:
   ```bash
   base64 -i AuthKey_KEYID.p8 | pbcopy
   ```
5. **Add GitHub Actions secrets** (repository Settings → Secrets and variables → Actions):
   - `APPLE_CERTIFICATE` — base64 certificate
   - `APPLE_CERTIFICATE_PASSWORD` — certificate passphrase
   - `APPLE_TEAM_ID` — your 10-character team ID (visible in developer.apple.com membership)
   - `APPLE_API_KEY_ID` — key ID from App Store Connect
   - `APPLE_API_ISSUER_ID` — issuer ID from App Store Connect
   - `APPLE_API_KEY_CONTENT` — base64 API key

## Triggering a release

```bash
git tag v1.0.5
git push origin v1.0.5
```

The release workflow runs. The macOS job:
1. Builds the binary with PyInstaller
2. Imports the certificate into a temporary keychain
3. Signs the binary with `codesign`
4. Zips the binary
5. Submits the zip to Apple notarization (`xcrun notarytool submit --wait`)
6. Uploads `risus-macos-arm64.zip` to the GitHub Release

## Verifying the artifact locally

```bash
unzip risus-macos-arm64.zip
codesign --verify --deep --strict --verbose=2 risus-macos-arm64
spctl --assess --type execute --verbose risus-macos-arm64
# Expected: risus-macos-arm64: accepted
#           source=Notarized Developer ID
```
