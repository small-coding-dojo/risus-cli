# Developer Build Instructions

Produces a self-contained `risus` binary for the current platform using
PyInstaller. No Python installation is required on the target machine.

## Prerequisites

- Python 3.12+ installed
- Project checked out (`git clone …`)
- Dev dependencies installed:

```bash
pip install -e ".[dev,client]"
```

Or install PyInstaller directly:

```bash
pip install pyinstaller>=6
```

## Build command

Run from the **project root**:

```bash
python -m PyInstaller build/risus.spec
```

## Expected output

| Platform | Output path       |
|----------|-------------------|
| Linux    | `dist/risus`      |
| macOS    | `dist/risus`      |
| Windows  | `dist/risus.exe`  |

The binary is self-contained and can be copied to any machine without Python.

## Clean build

Remove stale PyInstaller artifacts before rebuilding:

```bash
rm -rf dist/ build/risus/
```

Then rerun the build command above.

## CI

GitHub Actions runs the same command in a matrix across four runners
(`ubuntu-latest`, `macos-13`, `macos-latest`, `windows-latest`). See
`.github/workflows/build.yml` (CI smoke test) and
`.github/workflows/release.yml` (tag-triggered release). The spec file is
platform-agnostic; PyInstaller writes platform-appropriate output automatically.

Artifacts are renamed to the canonical form (`risus-{os}-{arch}[.exe]`) and
uploaded to the GitHub Release along with `.sha256` checksum files and
`risus.cfg.example`.
