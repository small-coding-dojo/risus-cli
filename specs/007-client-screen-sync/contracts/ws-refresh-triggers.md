# WS Contract: Messages That Trigger Client Screen Refresh

**Feature**: 007-client-screen-sync  
**Date**: 2026-05-04

## Overview

The client sets `ClientState.update_event` when it receives any of the following server-sent WebSocket frames. The main loop uses this event to decide when to redraw the battle display.

## Refresh-Triggering Frames (Server → Client)

| Frame type | Key fields | Triggers refresh | Reason |
|------------|------------|------------------|--------|
| `state` | `players: [{name, cliche, dice, lost_dice}]` | YES | Full game state changed |
| `presence` | `clients: [names]` | YES | Connected player list changed |
| `lock_acquired` | `player_name, locked_by` | YES | Lock indicator must update |
| `lock_released` | `player_name` | YES | Lock indicator must clear |

## Non-Refresh Frames (Server → Client)

| Frame type | Key fields | Triggers refresh | Reason |
|------------|------------|------------------|--------|
| `lock_denied` | `player_name, locked_by` | NO | Caller-only; handled inline by submenu |
| `error` | `message` | NO | Caller-only; displayed inline by submenu |

## Contract Invariants

- The refresh mechanism is display-only — no server protocol changes in this feature.
- `update_event` is set AFTER `ClientState.apply()` updates internal state, ensuring the main thread always reads fresh data when it calls `show_state()`.
- `lock_denied` and `error` frames are already handled inline within submenu functions and do not need to interrupt the top-level display loop.

## Protocol Reference

Full WS protocol reference is in `AGENTS.md` under "WS Protocol Reference". This document covers only the refresh-trigger subset relevant to this feature.
