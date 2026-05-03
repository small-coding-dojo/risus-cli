# Quickstart: Running with Secure Session

## Server

```bash
# Set token in environment (min 16 printable chars)
export RISUS_TOKEN=my-super-secret-game-token

# Start stack
docker compose up -d

# Or with podman
PATH=$PWD/.venv/bin:$PATH CONTAINER_ENGINE=podman podman-compose up -d
```

The server will reject all connections if `RISUS_TOKEN` is unset.

## Client — interactive

```bash
python risus.py
# Server address [saved]: risus.example.com
# Your name [saved]: Conan
# Session token: <type token, min 16 chars>
```

Token is saved to `risus.cfg` on exit. Subsequent launches skip the prompt.

## Client — CLI flags

```bash
python risus.py risus.example.com Conan --token my-super-secret-game-token
```

`--token` takes precedence over any stored value and suppresses the prompt.

## Wrong token

If the server rejects the token (4401), the client re-prompts:

```text
  Token rejected by server. Enter new token.
  Session token:
```

The rejected token is not stored. The new token is stored on the next
successful exit.

## Local development (no TLS)

```bash
# Start server with token
RISUS_TOKEN=dev-token-for-testing docker compose up -d

# Connect to localhost:8765 → uses ws:// (not wss://)
python risus.py localhost:8765 Conan --token dev-token-for-testing
```

Any server address containing `:` uses `ws://`; bare hostnames use `wss://`.

## Running tests

```bash
# Unit tests (no containers)
pytest tests/unit -q

# E2E tests (requires running container stack with RISUS_TOKEN set)
RISUS_TOKEN=test-token-for-e2e docker compose up -d
CONTAINER_ENGINE=podman PATH=$PWD/.venv/bin:$PATH RISUS_TOKEN=test-token-for-e2e pytest tests/e2e -m e2e -q
```
