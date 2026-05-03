#!/usr/bin/env python3
"""Risus CLI - multiplayer battle manager."""

import argparse
import atexit
import json
import os
import sys
import urllib.request
from pathlib import Path

import client.config
from client.ws_client import AuthError, WSClient

_client: WSClient | None = None


def _ws() -> WSClient:
    assert _client is not None
    return _client


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def show_state():
    state = _ws().state
    players = state.snapshot_players()
    presence = state.snapshot_presence()
    locks = state.snapshot_locks()

    if presence:
        print(f"Connected: {', '.join(presence)}")
    print("Battle state")
    print("=" * 40)
    if not players:
        print("  (no players)")
    else:
        print(f"  {'NAME':<16} {'DICE':>9}  CLICHE")
        print(f"  {'-'*16} {'-'*9}  {'-'*16}")
        for p in players:
            cliche = p.cliche if p.cliche else "(none)"
            if p.dice is None:
                dice_str = f"? (-{p.lost_dice})" if p.lost_dice else "?"
            else:
                dice_str = str(p.dice)
            lock_indicator = f" [locked by {locks[p.name]}]" if p.name in locks else ""
            print(f"  {p.name:<16} {dice_str:>9}  {cliche}{lock_indicator}")
    print()


def prompt_int(prompt="Number: ") -> int | None:
    val = input(prompt).strip()
    try:
        return int(val)
    except ValueError:
        return None


def _drain_and_wait(msg_types: tuple[str, ...], timeout: float = 5.0) -> dict | None:
    """Drain inbox, return first frame matching one of msg_types."""
    ws = _ws()
    buffered = ws.drain_inbox()
    for f in buffered:
        if f.get("type") in msg_types:
            return f
    return ws.recv(timeout=timeout)


def _request_lock(player_name: str) -> bool:
    """Send lock; wait for lock_acquired or lock_denied. Return True if acquired."""
    ws = _ws()
    ws.send({"type": "lock", "player_name": player_name})
    frame = _drain_and_wait(("lock_acquired", "lock_denied", "error"), timeout=3.0)
    if frame is None:
        return False
    ft = frame.get("type")
    if ft == "lock_acquired" and frame.get("player_name") == player_name:
        return True
    if ft == "lock_denied" and frame.get("player_name") == player_name:
        holder = frame.get("locked_by", "someone")
        print(f"  [{player_name}] is being edited by [{holder}]")
        return False
    return False


def _send_and_wait_state(payload: dict, timeout: float = 5.0) -> bool:
    """Send command; wait for state or error broadcast. Return True on state."""
    ws = _ws()
    ws.send(payload)
    frame = _drain_and_wait(("state", "error"), timeout=timeout)
    if frame is None:
        print("  (no response from server)")
        return False
    if frame.get("type") == "error":
        print(f"  Error: {frame.get('message', 'unknown')}")
        return False
    return True


def _unlock(player_name: str) -> None:
    _ws().send({"type": "unlock", "player_name": player_name})


def _prompt_required(label: str, default: str | None) -> str:
    """Prompt until non-empty input; accept default on empty when default present."""
    while True:
        hint = f" [{default}]" if default else ""
        val = input(f"{label}{hint}: ").strip()
        if val:
            return val
        if default:
            return default


def _prompt_token(saved: str | None) -> str:
    """Prompt for session token; minimum 16 printable non-whitespace chars."""
    while True:
        hint = f" [{saved}]" if saved is not None else ""
        val = input(f"Session token{hint}: ").strip()
        if not val:
            if saved is not None:
                return saved
            continue
        if sum(1 for c in val if c.isprintable() and not c.isspace()) < 16:
            print("  Token must be at least 16 printable non-whitespace characters.")
            continue
        return val


def connect_or_die(server: str, name: str, token: str) -> str:
    global _client
    while True:
        _client = WSClient()
        try:
            _client.start(server, name, token, timeout=10.0)
            _client.drain_inbox()
            return token
        except AuthError:
            print("  Connection rejected: invalid or missing token.")
            token = _prompt_token(None)
        except TimeoutError:
            print(f"Connection to {server} failed — check address, network, and that the server is running.")
            sys.exit(1)
        except Exception as exc:
            print(f"  Connection failed: {exc}")
            sys.exit(1)


def add_player():
    clear()
    show_state()
    print("[ Add Player ]")
    name = input("  Player name: ").strip()
    if not name:
        print("  Cancelled.")
        input("  Press Enter...")
        return
    cliche = input("  Starting cliche (leave blank for none): ").strip()
    dice: int | None = None
    if cliche:
        val = input("  Dice for that cliche (leave blank if unknown): ").strip()
        if val:
            try:
                dice = int(val)
            except ValueError:
                dice = None
    _send_and_wait_state({"type": "add_player", "name": name, "cliche": cliche, "dice": dice})


def switch_cliche():
    clear()
    show_state()
    print("[ Switch Cliche ]")
    players = _ws().state.snapshot_players()
    if not players:
        print("  No players.")
        input("  Press Enter...")
        return
    for i, p in enumerate(players, 1):
        print(f"  {i}. {p.name}")
    choice = prompt_int("  Pick player: ")
    if choice is None or choice < 1 or choice > len(players):
        return
    player = players[choice - 1]
    if not _request_lock(player.name):
        input("  Press Enter...")
        return
    try:
        cliche = input(f"  New cliche for {player.name}: ").strip()
        if not cliche:
            return
        val = input("  Dice (leave blank if unknown): ").strip()
        dice = int(val) if val else None
        _send_and_wait_state({"type": "switch_cliche", "player_name": player.name, "cliche": cliche, "dice": dice})
    finally:
        _unlock(player.name)


def save_battle():
    clear()
    show_state()
    print("[ Save Battle ]")
    name = input("  Save name: ").strip()
    if not name:
        print("  Cancelled.")
        input("  Press Enter...")
        return
    _send_and_wait_state({"type": "save", "save_name": name})
    print(f"  Saved '{name}' on server.")
    input("  Press Enter...")


def _http_base_url(ws_uri: str) -> str:
    return ws_uri.replace("wss://", "https://").replace("ws://", "http://").rsplit("/ws/", 1)[0]


def load_battle():
    clear()
    show_state()
    print("[ Load Battle ]")
    # Fetch save list from REST
    ws = _ws()
    server_base = _http_base_url(ws._uri)
    try:
        with urllib.request.urlopen(f"{server_base}/saves", timeout=5) as resp:
            saves = json.loads(resp.read())
    except Exception as exc:
        print(f"  Could not fetch saves: {exc}")
        input("  Press Enter...")
        return
    if not saves:
        print("  No save files found.")
        input("  Press Enter...")
        return
    for i, s in enumerate(saves, 1):
        print(f"  {i}. {s['save_name']}")
    choice = prompt_int("  Pick save: ")
    if choice is None or choice < 1 or choice > len(saves):
        return
    save_name = saves[choice - 1]["save_name"]
    _send_and_wait_state({"type": "load", "save_name": save_name})
    print(f"  Loaded '{save_name}' from server.")
    input("  Press Enter...")


def reduce_dice():
    clear()
    show_state()
    print("[ Reduce Dice ]")
    players = _ws().state.snapshot_players()
    if not players:
        print("  No players.")
        input("  Press Enter...")
        return
    for i, p in enumerate(players, 1):
        if p.dice is None:
            dice_str = f"? (-{p.lost_dice})" if p.lost_dice else "?"
        else:
            dice_str = str(p.dice)
        print(f"  {i}. {p.name}  ({dice_str} dice)")
    choice = prompt_int("  Pick player: ")
    if choice is None or choice < 1 or choice > len(players):
        return
    player = players[choice - 1]
    if not _request_lock(player.name):
        input("  Press Enter...")
        return
    try:
        is_dead = False
        if player.dice is None:
            amount_str = input("  How many dice lost: ").strip()
            amount = int(amount_str) if amount_str else 0
            dead = input(f"  Is {player.name} dead? [y/n]: ").strip().lower()
            is_dead = dead == "y"
        else:
            amount_str = input(f"  Reduce by how many dice (current: {player.dice}): ").strip()
            if not amount_str:
                return
            amount = int(amount_str)
        _send_and_wait_state({
            "type": "reduce_dice",
            "player_name": player.name,
            "amount": amount,
            "is_dead": is_dead,
        })
    finally:
        _unlock(player.name)


def main():
    if getattr(sys, "frozen", False):
        import certifi
        os.environ.setdefault("SSL_CERT_FILE", certifi.where())

    base_dir = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent

    parser = argparse.ArgumentParser(description="Risus battle manager")
    parser.add_argument("server", nargs="?", default=None, help="Server address (host:port)")
    parser.add_argument("name", nargs="?", default=None, help="Display name")
    parser.add_argument("--token", default=None, help="Session token")
    args = parser.parse_args()

    saved_server, saved_name, saved_token = client.config.read_config(base_dir)

    server = args.server or _prompt_required("Server address", saved_server)
    name = args.name or _prompt_required("Your name", saved_name)

    token = args.token or saved_token or _prompt_token(None)
    token = connect_or_die(server, name, token)
    atexit.register(client.config.write_config, base_dir, server, name, token)

    while True:
        clear()
        show_state()
        print("  1. Add player")
        print("  2. Switch cliche")
        print("  3. Reduce dice")
        print("  4. Save")
        print("  5. Load")
        print("  6. Quit")
        print()
        choice = input("> ").strip()

        if choice == "1":
            add_player()
        elif choice == "2":
            switch_cliche()
        elif choice == "3":
            reduce_dice()
        elif choice == "4":
            save_battle()
        elif choice == "5":
            load_battle()
        elif choice == "6":
            sys.exit(0)

        frames = _ws().drain_inbox()
        for f in frames:
            if f.get("type") == "disconnected":
                print("  Connection lost. Reconnecting...")


if __name__ == "__main__":
    main()
