# Research: Automatic Client Screen Refresh

**Feature**: 007-client-screen-sync  
**Date**: 2026-05-04

## Unknown 1: How to refresh display without breaking `input()` constraint

**Decision**: Use `select.select([sys.stdin], [], [], 1.0)` with a 1-second timeout to implement a non-blocking input loop in `risus.py`'s main menu. This replaces only the single top-level `input("> ")` call; all submenu `input()` calls remain unchanged.

**Rationale**:
- `select` is Python stdlib — no new dependencies
- `select.select` on a list containing `sys.stdin` returns immediately when the user presses Enter; if 1 second passes with no input, it returns an empty ready-list
- The call is still synchronous from the caller's perspective (blocks until input or timeout)
- Does not add `prompt_toolkit`, `aioconsole`, or any async input library — the constitution's explicit prohibitions
- One-second polling interval guarantees state changes are visible within 2 seconds (worst case: missed one 1s window, picked up in the next)

**Alternatives considered**:

| Alternative | Why rejected |
|-------------|--------------|
| Dedicated refresh thread printing to stdout | Corrupts terminal display while user types; complex ANSI cursor management required |
| Async rewrite of main loop | Major scope creep; violates "minimum viable scope" principle (II) |
| `signal.SIGALRM` timer | Platform-specific (Unix only, not available on Windows Python); complicates exception handling |
| Refresh only on next loop iteration (no timeout) | Does not satisfy SC-001 (2 second SLA); state visible only after user presses Enter |
| `prompt_toolkit` | Explicitly prohibited by constitution |

**Platform note**: `select.select` on stdin is supported on Linux and macOS. Windows is not a stated target (project runs in Docker/Podman containers on Linux; CLI clients run on macOS/Linux). If Windows support is ever added, this can be switched to `msvcrt.kbhit()` polling.

**Partial-input safety**: Terminals default to canonical (cooked) mode — keystrokes are buffered in the terminal's line buffer and not flushed to the program's stdin fd until the operator presses Enter. Therefore `select.select` on stdin will not return ready for partial input; the 1-second timeout fires cleanly, `show_state()` redraws the screen, and any characters already typed remain in the terminal's line buffer. When the operator presses Enter, the full line is delivered. This satisfies FR-007 (no data loss; visual redraw is acceptable per spec).

---

## Unknown 2: Where to place the dirty-flag

**Decision**: Add `update_event: threading.Event` directly to `ClientState` in `client/state.py`.

**Rationale**:
- `ClientState.apply()` is the single point where all incoming frames are applied — the right place to signal
- Placing the event on `ClientState` keeps the WS client layer (`ws_client.py`) unchanged
- Main thread accesses `ClientState` through `_ws().state` — already established access pattern
- `threading.Event` is thread-safe, lightweight, and already in stdlib

**Alternatives considered**:

| Alternative | Why rejected |
|-------------|--------------|
| Callback registered on `WSClient` | Adds indirection; `risus.py` would need to register during `connect_or_die()` — more coupling |
| Queue-based notification | Over-engineered; `threading.Event` already is a boolean flag with wait semantics |
| Polling `_inbox` queue from main thread | `recv()` with timeout already available, but would require restructuring main loop around it |

---

## Unknown 3: Scope of auto-refresh — top-level menu only or all prompts?

**Decision**: Auto-refresh applies ONLY to the top-level menu prompt (`choice = input("> ")` in `main()`). All submenu prompts (`add_player`, `switch_cliche`, `reduce_dice`, `save_game`, `load_game`) retain plain `input()`.

**Rationale**:
- Submenu flows are short interactive sequences; the user is mid-action and a screen redraw would be disruptive and confusing
- Spec edge case explicitly states "displayed at the next natural opportunity without interrupting the user's current input"
- The top-level menu is the natural idle resting point; refreshing there satisfies SC-001 in the common case (users spend most idle time at top menu)
- Minimal scope per Principle II

---

## Resolved Clarifications

All NEEDS CLARIFICATION items from Phase 0 resolved above. No open questions remain.
