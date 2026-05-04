# Data Model: Automatic Client Screen Refresh

**Feature**: 007-client-screen-sync  
**Date**: 2026-05-04

## Existing Entities (unchanged)

### PlayerSnapshot (`client/state.py`)

Immutable snapshot of a single player's current battle state. No changes in this feature.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Player identifier |
| `cliche` | `str` | Active cliché description |
| `dice` | `Optional[int]` | Current dice count; `None` until set |
| `lost_dice` | `int` | Accumulated lost dice |

### ClientState (`client/state.py`)

Thread-safe container for the current game snapshot. **Modified by this feature.**

| Field | Type | Description |
|-------|------|-------------|
| `players` | `list[PlayerSnapshot]` | All players in current battle |
| `presence` | `list[str]` | Names of connected clients |
| `locks` | `dict[str, str]` | `player_name → lock_holder_display_name` |
| `_lock` | `threading.Lock` | Guards reads/writes (existing) |
| **`update_event`** | **`threading.Event`** | **NEW: set by `apply()` on every state change; cleared by main thread after redraw** |

**State transitions for `update_event`**:

```
Initial state: Event cleared (not set)
                    │
                    ▼
apply() called ─────► update_event.set()
  (any frame type)
                    │
                    ▼
                Main thread detects event set
                    │
                    ▼
              show_state() called
                    │
                    ▼
              update_event.clear()
                    │
                    └──► back to initial state
```

## New Behavior: `apply()` method

After applying any frame type (`state`, `presence`, `lock_acquired`, `lock_released`), `apply()` calls `self.update_event.set()`. This is the only change to `apply()`.

```
Frame arrives in _reader() background thread
        │
        ▼
state.apply(frame)
        │
        ├─ update players / presence / locks (existing)
        │
        └─ self.update_event.set()   ← NEW
```

## New Behavior: Main Loop Input (`risus.py`)

The top-level menu loop acquires user input via `_input_with_refresh(prompt)` instead of `input(prompt)`.

```
_input_with_refresh("> "):
    print prompt, flush
    loop:
        ready = select.select([stdin], [], [], 1.0)
        if ready:
            return stdin.readline().rstrip()
        if update_event.is_set():
            update_event.clear()
            print newline
            show_state()
            print prompt, flush
```

**Invariants**:
- `update_event` is ONLY cleared by the main thread inside `_input_with_refresh`
- `update_event` is ONLY set by the background thread inside `ClientState.apply()`
- Submenu `input()` calls are unaffected — no dirty-flag check there
- `show_state()` logic is UNCHANGED — still calls `snapshot_players()`, `snapshot_presence()`, `snapshot_locks()`

## Data Flow Diagram

```
Background async thread                  Main CLI thread
(ws_client._reader)                      (risus.main)
        │                                       │
[WS frame arrives]                      [loop top: show_state()]
        │                                       │
state.apply(frame)                      [print menu options]
  updates players/                              │
  presence/locks       ──────────────►  [_input_with_refresh("> ")]
  sets update_event                             │
        │                               [select.select, 1s timeout]
        │                                       │
        │                               [timeout: update_event set?]
        │                               ├─ YES: clear → show_state() → reprint prompt
        │                               └─ NO: continue waiting
        │                                       │
        │                               [input ready: return choice]
        │                                       │
        │                               [handle menu choice]
        │                                       │
        └───────────────────────────────[loop back to top]
```
