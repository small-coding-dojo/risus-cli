# Contract: Interactive Startup Prompt

**Feature**: 003-standalone-client | **Date**: 2026-05-02

## Purpose

Defines the exact prompt text and behaviour when the client is launched
without command-line arguments (e.g., by double-clicking).

## Trigger Condition

Prompting occurs when a required parameter is absent from CLI arguments:

| Parameter      | CLI arg position | Prompt triggered when |
|----------------|------------------|-----------------------|
| Server address | `sys.argv[1]`    | Not provided          |
| Display name   | `sys.argv[2]`    | Not provided          |

If both are provided, no prompts are shown and the client connects directly.
If only one is provided, only the missing parameter is prompted.

## Prompt Text

### Server Address

When `risus.cfg` provides a default value `v`:

```text
Server address [v]:
```

When no default is available:

```text
Server address:
```

### Display Name

When `risus.cfg` provides a default name `n`:

```text
Your name [n]:
```

When no default is available:

```text
Your name:
```

## Behaviour Rules

1. Prompts use synchronous `input()` — no async input libraries.
2. If the player presses Enter with an empty value, the same prompt is
   displayed again immediately (re-prompt loop until non-empty).
3. For server address with a default: pressing Enter without typing accepts
   the default value shown in brackets.
4. No validation of server address format at prompt time — connection failure
   is reported after the prompt phase.
5. No validation of display name content beyond non-empty — server enforces
   any additional rules.

## Example Session (no CLI args, config has both defaults)

```text
Server address [192.168.1.10:8765]: 
Your name [Conan]: 
```

Player presses Enter twice to accept saved defaults.

## Example Session (no CLI args, config has server only)

```text
Server address [localhost:8765]: 192.168.1.10:8765
Your name: Conan
```

## Example Session (no CLI args, no config)

```text
Server address: 192.168.1.10:8765
Your name: Conan
```

## Example Session (empty input re-prompt)

```text
Server address: 
Server address: 192.168.1.10:8765
Your name: 
Your name: Conan
```
