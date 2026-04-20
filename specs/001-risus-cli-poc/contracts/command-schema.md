# Command Schema Contract: Risus CLI POC

**Feature**: 001-risus-cli-poc  
**Date**: 2026-04-20

This document defines the exact command syntax accepted at the interactive `>` prompt and at the OS shell entry point. It is the authoritative contract between the CLI surface and the implementation.

---

## OS-Level Entry Point

```
cli [--load <save-name>]
```

| Argument | Required | Type | Description |
|----------|----------|------|-------------|
| `--load <save-name>` | No | string | Load named save and enter interactive session |

**Behaviour**:
- No arguments → empty session, enter interactive `>` prompt.
- `--load <name>` → restore named save, enter interactive `>` prompt with session name in header.
- `--load <missing-name>` → print `"Save '<name>' not found"` to stderr, exit with code 1.

---

## Interactive Shell Commands

All commands are typed at the `>` prompt. The `cli` prefix is **not** used inside the shell.

### `player add`

Add a new player to the current battle.

```
player add --name <name> [--cliche <cliche-name>] [--points <n>]
```

| Flag | Required | Type | Default | Description |
|------|----------|------|---------|-------------|
| `--name` | Yes | string | — | Player name (must be unique) |
| `--cliche` | No | string | `""` | Starting active cliché |
| `--points` | No | int ≥ 0 | `0` | Starting dice count |

**Success**: Reprints battle state.  
**Error**: `"Player '<name>' already exists"` — prompt returns, no state change.

---

### `cliche switch`

Set a player's active cliché and dice pool.

```
cliche switch --name <cliche-name> --points <n> --target <player-name>
```

| Flag | Required | Type | Description |
|------|----------|------|-------------|
| `--name` | Yes | string | New cliché name |
| `--points` | Yes | int ≥ 0 | New dice count |
| `--target` | Yes | string | Player name to update |

**Success**: Reprints battle state.  
**Error**: `"Player '<target>' not found"` — prompt returns, no state change.

---

### `cliche reduce-by`

Reduce a player's active dice pool by a specified amount (clamped at 0).

```
cliche reduce-by --amount <n> --target <player-name>
```

| Flag | Required | Type | Description |
|------|----------|------|-------------|
| `--amount` | Yes | int ≥ 1 | Number of dice to remove |
| `--target` | Yes | string | Player name to update |

**Success**: Reprints battle state. If dice reach 0, player is removed from display.  
**Error**: `"Player '<target>' not found"` — prompt returns, no state change.

---

### `save`

Persist the current battle state to a named slot.

```
save --name <save-name>
```

| Flag | Required | Type | Description |
|------|----------|------|-------------|
| `--name` | Yes | string | Save slot name (overwrites if exists) |

**Success**: Reprints battle state with session name in header.  
**Error**: File system write failure → print error, prompt returns.

---

### `help`

Display available commands. Implemented automatically by `cmd.Cmd` via docstrings.

```
help [<command>]
```

---

### `quit` / `exit`

Exit the interactive session cleanly.

```
quit
exit
```

**Behaviour**: Flush stdout, exit with code 0.

---

## Battle State Display Format

Printed after every mutating command and on session start.

```
Battle latest state [(<session-name>)]
======================================
(Name):    (number of dice) (Cliché used in battle)

<player-name>:     <n> dice (<cliche-name>)
...
```

Rules:
- Header shows session name in parentheses only when a session name is set.
- Separator `=` line matches header length.
- Only players with `dice > 0` are listed.
- An empty roster shows no player rows (blank line between header and prompt is acceptable).
- Column widths are not fixed; a single-space separator after the colon is sufficient for POC.

**Example — no session name**:
```
Battle latest state
===================
Hanne:     4 dice (Throw stones)
Zerox:     3 dice (Firearms)
```

**Example — with session name**:
```
Battle latest state (Builders' Shack)
======================================
Hanne:     4 dice (Throw stones)
Zerox:     3 dice (Firearms)
```

---

## Error Output Contract

- All inline errors are printed to **stdout** (within the REPL session flow) before the next `>` prompt.
- Exit-time errors (e.g., `--load` missing save) go to **stderr** with exit code 1.
- Unknown commands at `>` prompt: print `"Unknown command. Type 'help' for available commands."` to stdout, re-display prompt.
