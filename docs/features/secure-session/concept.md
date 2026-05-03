# Secure Session — Solution Concept

## Architecture

```
Player → wss://risus.boos.systems/ws/{name}?token=SECRET
              ↓ port 443 (TLS terminated)
           Caddy  (Let's Encrypt, auto-HTTPS)
              ↓ ws://127.0.0.1:8765/ws/{name}?token=SECRET
           FastAPI  (validates RISUS_TOKEN env var)
              ↓
           Postgres

Firewall: open 80 (ACME challenge), 443 (WSS). Block 8765.
```

Token travels encrypted inside TLS. FastAPI validates it as a second layer.
Caddy does not inspect the token — it proxies the full query string through.

## Component Changes

### `client/config.py`
- `read_config(base_dir)` → `tuple[str|None, str|None, str|None]` (server, name, token)
- `write_config(base_dir, server, name, token)` → saves `token` key in `[risus]`

### `risus.py`
- `argparse`: add `--token` optional flag
- `main()`: read token from config; if absent, `_prompt_required("Session token", saved_token)`
- `atexit`: include token in `write_config` call
- `connect_or_die(server, name, token)`: forward token to `WSClient.start()`
- `load_battle()`: replace hardcoded `ws://→http://` with:
  ```python
  server_base = ws._uri.replace("wss://", "https://").replace("ws://", "http://").rsplit("/ws/", 1)[0]
  ```

### `client/ws_client.py`
- `start(server, name, token, timeout=10.0)`:
  ```python
  scheme = "ws://" if ":" in server else "wss://"
  self._uri = f"{scheme}{server}/ws/{name}?token={token}"
  ```

### `server/ws.py`
- In `handle()`, before first `ws.accept()`:
  ```python
  expected = os.environ.get("RISUS_TOKEN", "")
  if not expected or ws.query_params.get("token") != expected:
      await ws.accept()
      await ws.close(code=4401, reason="unauthorized")
      return
  ```

### `docker-compose.yml`
- Server service: add `RISUS_TOKEN: ${RISUS_TOKEN}` to env; bind to `127.0.0.1:8765`
- Add Caddy service:
  ```yaml
  caddy:
    image: caddy:2-alpine
    network_mode: host
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
  ```
  `network_mode: host` lets Caddy reach `127.0.0.1:8765` directly. Ports 80/443 are bound by Caddy itself on the host network.

### `Caddyfile` (new file, project root)
```
risus.boos.systems {
    reverse_proxy ws://127.0.0.1:8765
}
```
Caddy auto-provisions Let's Encrypt cert on first start. Port 80 must be
reachable for the ACME HTTP-01 challenge.

## Test Strategy

**Unit tests** (no containers, mock `ws.query_params`):
- `RISUS_TOKEN` unset → reject all
- Token absent in request → 4401
- Token wrong → 4401
- Token correct → connection proceeds

**Local E2E** (existing compose, no Caddy needed):
- Set `RISUS_TOKEN=testtoken` in compose env
- Correct token → state received
- Wrong token → rejected

**Scheme detection** (unit, no network):
- `"localhost:8765"` → `ws://localhost:8765/ws/...`
- `"risus.boos.systems"` → `wss://risus.boos.systems/ws/...`
