# Quickstart: macOS Signed Release

**Date**: 2026-05-03

## What changes

- `build/entitlements.plist` — new file; minimal entitlements for the signed binary
- `.github/workflows/release.yml` — macOS job gains certificate import, codesign, notarization, and zip steps

Linux and Windows jobs are unchanged.

## Prerequisites (one-time developer setup)

### 1. Export the Developer ID Application certificate

Use Xcode — not Keychain Access (the cert has no private key there).

1. Open **Xcode → Settings → Accounts** → select your Apple ID → **Manage Certificates**
2. Right-click **Developer ID Application** (it looks like a static label but is clickable) → **Export Certificate**
3. Choose a save location and set a strong password
4. macOS prompts for your **login keychain password — twice**. Enter it both times.
5. You now have a `.p12` file. Keep it secret.

Base64-encode for GitHub:

```bash
base64 -i YourCert.p12 | pbcopy
```

**Delete the `.p12` file immediately after adding it to GitHub.** It is not encrypted at rest and contains the private key.

### 2. Find your signing identity string

```bash
security find-identity -v -p codesigning
```

Copy the full string from the output, e.g.:

```
Developer ID Application: Stefan Boos (M9YN683HBZ)
```

This is your `APPLE_SIGNING_IDENTITY` value.

### 3. Create an App Store Connect API key

1. Go to [appstoreconnect.apple.com](https://appstoreconnect.apple.com) → **Users and Access → Integrations → App Store Connect API**
2. Click **Request Access** if you have not done so before — the **+** button is not available until access is granted
3. Click **+** → name the key (e.g. `risus-notarization`) → Access: **Developer** → **Generate**
4. Note the **Key ID** and **Issuer ID** shown on the page
5. Click **Download API Key** — saves `AuthKey_KEYID.p8` — **downloadable once only**

Base64-encode for GitHub:

```bash
base64 -i AuthKey_KEYID.p8 | pbcopy
```

### 4. Add GitHub Actions secrets

Go to repository **Settings → Secrets and variables → Actions → New repository secret**:

| Secret | Value |
|--------|-------|
| `APPLE_CERTIFICATE` | Base64-encoded `.p12` file |
| `APPLE_CERTIFICATE_PASSWORD` | Password set during `.p12` export |
| `APPLE_SIGNING_IDENTITY` | Full identity string, e.g. `Developer ID Application: Name (TEAMID)` |
| `APPLE_API_KEY_ID` | Key ID from App Store Connect |
| `APPLE_API_ISSUER_ID` | Issuer ID from App Store Connect |
| `APPLE_API_KEY_CONTENT` | Base64-encoded `.p8` file |

### 5. Bump the version

Before tagging, update `pyproject.toml`:

```toml
version = "1.x.y"
```

The tag must match the version (e.g. `version = "1.0.5"` → tag `v1.0.5`).

## Conditional signing

Signing steps only run when `APPLE_CERTIFICATE` is configured as a repository secret. On branches and PRs where secrets are absent, the macOS job builds an unsigned binary — useful for verifying the build without Apple credentials.

On **tagged releases**, the pipeline asserts that secrets are present and fails loudly if they are missing. This prevents accidentally publishing an unsigned artifact.

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
# Expected: risus-macos-arm64: valid on disk
#           risus-macos-arm64: satisfies its Designated Requirement
```

Note: `spctl --assess --type execute` does not work for plain Mach-O CLI binaries and will report "does not seem to be an app" even when the binary is correctly signed and notarized. Use `codesign --verify` instead.
