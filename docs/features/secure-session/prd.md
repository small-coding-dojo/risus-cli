# Secure Session — PRD

## Problem

Server deployed on a public URL has no access control. Any person who discovers
the address can connect, read state, add players, and mutate dice.
Communication is plaintext (`ws://`), exposing any credential to MITM.

## Goal

Restrict connections to players who possess a shared secret token.
Encrypt all traffic in transit via TLS.

## Scope

**In scope**

- Shared-secret token (one token, all players share it out-of-band)
- TLS via Caddy reverse proxy (Let's Encrypt auto-provisioned)
- Token passed as WS query param: `?token=<secret>`
- Token persisted in `risus.cfg`; `--token` CLI arg; prompt fallback
- Auto-select `ws://` vs `wss://` by server address format
- Server-side token validation (defense in depth, unit-testable)
- Constitution amendment (Principle II currently bans auth)

**Out of scope**

- Per-user credentials or user management
- Token rotation, expiry, or multi-token support
- REST endpoint auth (`/state`, `/saves`, `/healthz`)

## Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-1 | On startup, if `--token` absent and `risus.cfg` has no token, prompt `Session token [<saved>]: `. Non-empty input required. |
| FR-2 | On exit, write token to `risus.cfg` `[risus]` section key `token`. |
| FR-3 | `--token <value>` skips prompt and config read. |
| FR-4 | If server address contains `:` (e.g. `localhost:8765`), use `ws://`. Otherwise `wss://`. |
| FR-5 | WS URI: `{scheme}{server}/ws/{name}?token={token}`. |
| FR-6 | Server reads `RISUS_TOKEN` env var. If request `?token` absent or mismatched, accept WS then close code 4401 reason `"unauthorized"`. If `RISUS_TOKEN` is unset/empty, reject all connections. |
| FR-7 | `load_battle()` must derive HTTP base URL handling both `ws://→http://` and `wss://→https://`. |
| FR-8 | `RISUS_TOKEN` present in server service env in `docker-compose.yml`. |
| FR-9 | Caddy service in `docker-compose.yml`; terminates TLS, proxies to `127.0.0.1:8765`. |
| FR-10 | FastAPI binds to `127.0.0.1:8765` (not `0.0.0.0`) in the compose stack. |

## Acceptance Criteria

| ID | Criterion |
|----|-----------|
| AC-S1 | Client with absent token → rejected (code 4401) |
| AC-S2 | Client with wrong token → rejected (code 4401) |
| AC-S3 | Client with correct token → connects and receives state |
| AC-S4 | Token saved to `risus.cfg`; not prompted again on restart |
| AC-S5 | `--token` bypasses prompt |
| AC-S6 | `localhost:8765` → `ws://`; `risus.boos.systems` → `wss://` |
| AC-S7 | `load_battle()` works on both `ws://` and `wss://` connections |

## Constitution Amendment Required

Principle II ("No authentication — permanently out of scope") must be updated
to permit shared-secret token auth **before** implementation begins.
