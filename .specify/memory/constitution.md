<!--
Sync Impact Report
Version change: [CONSTITUTION_VERSION] → 1.0.0
Modified principles: None (initial population — all placeholders replaced)
Added sections: Core Principles (5), Tech Stack & Constraints,
  Development Workflow, Governance
Removed sections: N/A
Templates requiring updates:
  - .specify/templates/plan-template.md ✅
    (Constitution Check gates align with principles below)
  - .specify/templates/spec-template.md ✅
    (no changes required; scope constraints consistent)
  - .specify/templates/tasks-template.md ✅
    (no changes required; testing discipline reflected)
Follow-up TODOs: None — all placeholders resolved
-->

# Risus CLI Constitution

## Core Principles

### I. Server Authority (NON-NEGOTIABLE)

The server is the single source of truth for all battle state. `ClientState`
MUST NOT be mutated locally and assumed correct. All mutations MUST flow
through WebSocket commands to the server. Lock enforcement MUST be
server-side; `LockManager` is the sole arbiter of which client holds a lock.
The `locks` DB table is an audit log only and MUST NOT be used to reconstruct
lock state.

**Rationale**: Concurrency correctness requires one authoritative source.
Local mutations create divergent state that silently corrupts multi-player
sessions.

### II. Simplicity (NON-NEGOTIABLE)

Every change MUST achieve its goal with the minimum viable scope. No
authentication, no multi-battle support — these are permanently out of scope
per the PRD. Menu UX (options 1–6, labels, prompts, ordering) MUST NOT
change. `input()` calls MUST remain synchronous; no `prompt_toolkit` or async
input libraries may be introduced.

**Rationale**: Scope creep breaks the PRD contract and multi-player UX
assumptions. Keep modifications, configuration, and options at the absolute
minimum to achieve the current goal.

### III. No Duplication

Code and documentation MUST NOT duplicate logic or content. When logic appears
in two places, extract it. When docs repeat information, link instead.
Duplication in tests is permitted where it aids clarity and isolation.

**Rationale**: Duplication makes maintenance expensive and creates drift
between sources of truth.

### IV. Testing Discipline

Changes MUST pass unit tests (`pytest tests/unit -q`) and E2E tests
(`CONTAINER_ENGINE=podman pytest tests/e2e -m e2e -q`) on a clean clone
before review. E2E tests MUST target a real container stack — mocking the
container layer in E2E scenarios is prohibited. Both Docker and Podman MUST
remain equal peers in all docs and test instructions.

**Rationale**: The WS protocol and DB interactions require real-stack
verification. Mock-only coverage allows contract drift to reach production
undetected.

### V. No Local Persistence

The CLI MUST NOT perform local JSON or file I/O for battle state. Save/load
are server-side operations only. No feature may introduce local state storage
without an explicit constitution amendment.

**Rationale**: Keeping the CLI a thin renderer preserves server authority and
eliminates a class of local-vs-server state divergence bugs.

## Tech Stack & Constraints

- **Language**: Python 3.12+
- **Server**: FastAPI + asyncpg + Postgres 16; WS at `/ws/{name}`;
  REST at `/state`, `/saves`, `/healthz`
- **Client**: asyncio WS client (`client/ws_client.py`);
  blocking `input()` loop in `risus.py`
- **Testing**: pytest 8+; unit (no containers), E2E (real stack via compose)
- **Container runtimes**: Docker Compose and podman-compose — both MUST work
- **Commits**: Conventional Commits (`feat:`, `fix:`, `test:`, `docs:`,
  `chore:`)
- **Linting**: ruff check; formatting: black (or equivalent)
- **Out of scope**: authentication, multi-battle support, local file
  persistence

## Development Workflow

1. Branch from `main`: `git checkout -b feat/my-change`
2. Make changes; unit tests MUST pass locally before committing
3. E2E tests MUST pass against real stack before opening a PR
4. Commit using Conventional Commits
5. Open PR with the AGENTS.md hand-off checklist completed

**Quality Gate** (required before any PR merges):

```bash
pytest tests/unit -q
CONTAINER_ENGINE=podman pytest tests/e2e -m e2e -q
podman-compose up -d && curl -fsS http://localhost:8765/healthz
```

Changes to the WS protocol MUST update the WS Protocol Reference table in
`AGENTS.md`. Schema changes MUST update `server/schema.sql` and require
`docker compose down -v` on existing volumes.

## Governance

This constitution supersedes all other guidance when conflicts arise.
Amendments require:

1. A description of the change and its rationale.
2. A version bump per semantic versioning:
   - MAJOR: principle removal or redefinition
   - MINOR: new principle or section added
   - PATCH: clarification, wording, or non-semantic refinement
3. A propagation check across `.specify/templates/` and `AGENTS.md`.

All PRs and code reviews MUST verify compliance with Core Principles.
Complexity additions MUST be justified in the plan's Complexity Tracking
table. Refer to `AGENTS.md` for runtime agent guidance and the hand-off
checklist.

**Version**: 1.0.0 | **Ratified**: 2026-05-02 | **Last Amended**: 2026-05-02
