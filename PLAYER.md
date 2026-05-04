# Risus Client — Player Guide

No Python required. Download the binary for your platform and play.

## 1. Download

Go to the [Releases page](../../releases) and download the file for your
operating system:

| Your OS               | File to download                |
|-----------------------|---------------------------------|
| Windows               | `risus-windows-x86_64.exe`      |
| macOS                 | `risus-macos-arm64`             |
| Linux                 | `risus-linux-x86_64`            |

## 2. Make it executable (macOS / Linux only)

```bash
chmod +x risus-linux-x86_64   # replace with your filename
```

**macOS note**: The binary is notarized. Gatekeeper allows it on first run without any manual steps.

## 3. Run

### Option A: Double-click (easiest)

Double-click the executable. The client asks for the server address and your
name:

```text
Server address: 192.168.1.10:8765
Your name: Conan
```

### Option B: Command line

```bash
./risus-linux-x86_64 <server-address> <your-name>
```

Example:

```bash
./risus-linux-x86_64 192.168.1.10:8765 Conan
```

On Windows:

```cmd
risus-windows-x86_64.exe 192.168.1.10:8765 Conan
```

## 4. Connection details are saved automatically

After your first session the client saves your server address and name to
`risus.cfg` in the same folder. Next time you launch, both are pre-filled —
just press Enter to accept them.

You can also edit `risus.cfg` directly:

```ini
[risus]
server = 192.168.1.10:8765
name = Conan
```

A template file `risus.cfg.example` is included in the release — copy it to
`risus.cfg` to set initial defaults before your first session.

## Troubleshooting

| Symptom | Fix |
| ------- | --- |
| `Connection to … failed` | Check that the server is running and the address is correct |
| Menu appears instantly, no players listed, no delay | Client did not connect. Check `risus.cfg` exists in the same folder as the binary. If the server uses TLS (e.g. `risus.example.com`), the address must have **no port** — a `host:port` address forces an unencrypted connection |
| Permission denied (Unix) | Run `chmod +x <filename>` first |
| macOS blocks the app | Binary is notarized — if blocked, open System Settings → Privacy & Security and click Allow Anyway |
| Windows SmartScreen warning | Click **More info → Run anyway** |
| Slow startup (~2–4 s) | Normal — binary self-extracts on first launch |
