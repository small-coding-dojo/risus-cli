# Risus Client — Player Quickstart

No Python required. Download the binary for your platform and play.

## 1. Download

Go to the [Releases page](../../releases) and download the file for your
operating system:

| Your OS               | File to download                |
|-----------------------|---------------------------------|
| Windows               | `risus-windows-x86_64.exe`      |
| macOS (Apple Silicon) | `risus-macos-arm64`             |
| macOS (Intel)         | `risus-macos-x86_64`            |
| Linux                 | `risus-linux-x86_64`            |

## 2. Make it executable (macOS / Linux only)

```bash
chmod +x risus-linux-x86_64   # replace with your filename
```

**macOS note**: On first run macOS may block the app because it is not
notarized. To allow it:

1. Try to run it once — macOS shows a security warning and blocks it.
2. Open **System Settings → Privacy & Security**.
3. Scroll down to the blocked app and click **Allow Anyway**.
4. Run the binary again — it will launch.

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

A template file `risus.cfg.example` is included — copy it to `risus.cfg`
to set initial defaults before your first session.

## Troubleshooting

| Symptom | Fix |
| ------- | --- |
| `No response from server` | Check that the server is running and the address/port is correct |
| Permission denied (Unix) | Run `chmod +x <filename>` first |
| macOS blocks the app | Follow Step 2 above |
| Windows SmartScreen warning | Click **More info → Run anyway** |
