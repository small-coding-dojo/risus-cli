# Data Model: Risus CLI POC

**Feature**: 001-risus-cli-poc  
**Date**: 2026-04-20

---

## Entities

### Player

Represents a single character participating in a battle.

| Field | Type | Constraints | Default |
|-------|------|-------------|---------|
| `name` | `str` | Non-empty, unique within a BattleState | — |
| `cliche_name` | `str` | Can be empty string | `""` |
| `dice` | `int` | Non-negative integer (≥ 0) | `0` |

**Validation rules**:
- `name` must be a non-empty, stripped string.
- `dice` must be ≥ 0. Reductions that would bring it below 0 are clamped to 0.
- When `dice` reaches 0 the player is considered **eliminated** and is excluded from the battle state display (the object is retained in memory to support future undo/re-entry if ever required, but the display layer omits it).

**State transitions**:

```
           player add
Initial ─────────────────► Active (dice ≥ 1 or dice = 0 with cliche)
   Active ──────────────► Active  (cliche switch, reduce-by while dice > 0)
   Active ──────────────► Eliminated  (reduce-by causes dice = 0)
```

---

### BattleState

The aggregate root for an interactive session. Holds all players and optional session metadata.

| Field | Type | Constraints | Default |
|-------|------|-------------|---------|
| `players` | `dict[str, Player]` | Keys are player names (case-sensitive) | `{}` |
| `session_name` | `str \| None` | Optional; set on save or load | `None` |

**Invariants**:
- Player names are unique (enforced on `add`; duplicate → error FR-008).
- `session_name` persists for the lifetime of the interactive session once set (FR-009).

**Operations**:
- `add_player(name, cliche="", dice=0) → Player` — raises `DuplicatePlayerError` if name exists.
- `switch_cliche(player_name, cliche_name, dice) → Player` — raises `PlayerNotFoundError`.
- `reduce_dice(player_name, amount) → Player` — clamps at 0; raises `PlayerNotFoundError`.
- `active_players() → list[Player]` — returns players where `dice > 0`, in insertion order.

---

### SaveSlot

A named snapshot of BattleState persisted to disk.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | The human-readable save name (stored verbatim inside JSON) |
| `filename` | `str` | Derived slug: `re.sub(r'[^a-zA-Z0-9_-]', '_', name).lower() + ".json"` |
| `path` | `Path` | `~/.risus/saves/<filename>` |
| `players` | `list[PlayerRecord]` | Serialised player list |

**Serialisation format** (JSON):

```json
{
  "name": "Builders' Shack",
  "players": [
    { "name": "Hanne", "cliche_name": "Throw stones", "dice": 4 },
    { "name": "Zerox", "cliche_name": "Firearms", "dice": 3 }
  ]
}
```

**Deserialisation rules**:
- Missing `cliche_name` → default `""`.
- Missing `dice` → default `0`.
- `name` field in JSON is the authoritative session name after load.

---

## Relationships

```
BattleState (1) ──── (0..*) Player
BattleState (0..1) ─────── SaveSlot  [transient: save writes it; load reads it]
```

---

## Error Types

| Error Class | Raised By | Message Pattern |
|-------------|-----------|-----------------|
| `DuplicatePlayerError` | `BattleState.add_player` | `"Player '{name}' already exists"` |
| `PlayerNotFoundError` | `switch_cliche`, `reduce_dice` | `"Player '{name}' not found"` |
| `SaveNotFoundError` | `persistence.load` | `"Save '{name}' not found"` |

All errors are caught by the REPL command handlers and printed inline; the interactive session continues.
