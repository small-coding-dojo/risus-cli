# Implementation Plan: Secure Session

**Branch**: `004-secure-session` | **Date**: 2026-05-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-secure-session/spec.md`

## Summary

Add shared-secret token authentication to the Risus WebSocket layer: the server
validates `RISUS_TOKEN` on every connection, rejects without it, and imposes a
3-second brute-force delay. The client prompts for a token when absent, validates
minimum length, persists it to config, and re-prompts on rejection. TLS is
handled by a Caddy reverse proxy (deployment concern); the client selects
`wss://` vs `ws://` based on whether the server address contains a colon.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: FastAPI (server), websockets (client), configparser
(config), asyncio
**Storage**: PostgreSQL 16 (unchanged); `risus.cfg` extended with `token` key
**Testing**: pytest 8+; unit (no containers), E2E (real container stack)
**Target Platform**: Linux server (Docker/Podman)
**Project Type**: CLI client + FastAPI server
**Performance Goals**: Correct-token connection completes within 3–4 s
(SC-001); 3 s intentional delay
**Constraints**: `input()` MUST remain synchronous; no new auth libraries
**Scale/Scope**: Single shared secret; all players share one token per deployment

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Notes |
| --------- | ----- | ----- |
| I — Server Authority | ✅ PASS | Token validation is server-side only; no local state mutation |
| II — Simplicity | ✅ PASS | Amendment in constitution v1.1.0 explicitly permits `RISUS_TOKEN`. No new auth library. Menu UX (options 1–6) unchanged. `input()` stays synchronous. |
| III — No Duplication | ✅ PASS | Scheme detection in one place (`ws_client.py`). Token validation in one place (`server/ws.py`). URL derivation refactored in `load_battle()`. |
| IV — Testing Discipline | ✅ PASS | Unit tests for token validation (mock `ws.query_params`), scheme detection, config, and startup prompts. E2E tests against real container stack. |
| V — No Local Persistence | ✅ PASS | Token stored in `risus.cfg` is connection config (same category as server/name), not battle state. Constitution v1.1.0 permits this class of config. |

**Complexity Tracking**: No violations. No new patterns beyond what the
constitution already permits.

## Project Structure

### Documentation (this feature)

```text
specs/004-secure-session/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── ws-token-auth.md
└── tasks.md             # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (affected files)

```text
# Modified
client/config.py              # read_config/write_config: add token param
client/ws_client.py           # start(): token + scheme detection; 4401 handling
risus.py                      # --token arg, token prompt, re-prompt on rejection,
                              #   connect_or_die(server, name, token),
                              #   load_battle() URL fix for wss://
server/ws.py                  # handle(): RISUS_TOKEN validation, 3-s delay, logging
docker-compose.yml            # RISUS_TOKEN env; server binds to 127.0.0.1:8765

# New
Caddyfile                     # Caddy reverse proxy (deployment artifact)

# New tests
tests/unit/test_token_auth.py     # server validation + scheme detection
tests/e2e/test_token_auth.py      # E2E: correct/wrong/absent token

# Extended tests (add cases to existing files)
tests/unit/test_config.py         # token read/write cases
tests/unit/test_startup.py        # --token flag and token prompt cases
```

## Implementation Order

1. `client/config.py` — extend API (no external deps change)
2. `client/ws_client.py` — scheme detection + 4401 propagation
3. `server/ws.py` — token gate + delay + logging
4. `risus.py` — wire everything: arg, prompt, re-prompt, URL fix
5. `docker-compose.yml` + `Caddyfile` — deployment changes
6. Tests — unit first, then E2E

Each step is independently testable before the next.
