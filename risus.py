#!/usr/bin/env python3
"""Risus CLI - text adventure style battle manager (POC)."""

import json
import os
import sys


class Player:
    def __init__(self, name, cliche="", dice=None):
        self.name = name
        self.cliche = cliche
        self.dice = dice  # None = unknown
        self.lost_dice = 0  # cumulative losses when dice pool is unknown


class Battle:
    def __init__(self):
        self.players: list[Player] = []

    def find(self, name: str) -> Player | None:
        for p in self.players:
            if p.name.lower() == name.lower():
                return p
        return None


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def show_state(battle: Battle):
    print("Battle state")
    print("=" * 40)
    if not battle.players:
        print("  (no players)")
    else:
        print(f"  {'NAME':<16} {'DICE':>9}  CLICHE")
        print(f"  {'-'*16} {'-'*9}  {'-'*16}")
        for p in battle.players:
            cliche = p.cliche if p.cliche else "(none)"
            if p.dice is None:
                dice_str = f"? (-{p.lost_dice})" if p.lost_dice else "?"
            else:
                dice_str = str(p.dice)
            print(f"  {p.name:<16} {dice_str:>9}  {cliche}")
    print()


def prompt_name(prompt="Name: ") -> str:
    val = input(prompt).strip()
    return val


def prompt_int(prompt="Number: ") -> int | None:
    val = input(prompt).strip()
    try:
        return int(val)
    except ValueError:
        return None


def add_player(battle: Battle):
    clear()
    show_state(battle)
    print("[ Add Player ]")
    name = prompt_name("  Player name: ")
    if not name:
        print("  Cancelled.")
        input("  Press Enter...")
        return
    if battle.find(name):
        print(f"  '{name}' already exists.")
        input("  Press Enter...")
        return
    cliche = input("  Starting cliche (leave blank for none): ").strip()
    if cliche:
        dice = prompt_int("  Dice for that cliche (leave blank if unknown): ")
    else:
        dice = None
    battle.players.append(Player(name, cliche, dice))


def switch_cliche(battle: Battle):
    clear()
    show_state(battle)
    print("[ Switch Cliche ]")
    if not battle.players:
        print("  No players.")
        input("  Press Enter...")
        return
    for i, p in enumerate(battle.players, 1):
        print(f"  {i}. {p.name}")
    choice = prompt_int("  Pick player: ")
    if choice is None or choice < 1 or choice > len(battle.players):
        return
    player = battle.players[choice - 1]
    cliche = input(f"  New cliche for {player.name}: ").strip()
    if not cliche:
        return
    dice = prompt_int("  Dice (leave blank if unknown): ")
    player.cliche = cliche
    player.dice = dice


def save_battle(battle: Battle):
    clear()
    show_state(battle)
    print("[ Save Battle ]")
    name = input("  Save name: ").strip()
    if not name:
        print("  Cancelled.")
        input("  Press Enter...")
        return
    filename = f"{name}.json"
    data = {
        "name": name,
        "players": [
            {"name": p.name, "cliche": p.cliche, "dice": p.dice, "lost_dice": p.lost_dice}
            for p in battle.players
        ],
    }
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  Saved to {filename}")
    input("  Press Enter...")


def load_battle(battle: Battle):
    clear()
    show_state(battle)
    print("[ Load Battle ]")
    saves = sorted(f for f in os.listdir(".") if f.endswith(".json"))
    if not saves:
        print("  No save files found.")
        input("  Press Enter...")
        return
    for i, f in enumerate(saves, 1):
        print(f"  {i}. {f[:-5]}")
    choice = prompt_int("  Pick save: ")
    if choice is None or choice < 1 or choice > len(saves):
        return
    filename = saves[choice - 1]
    with open(filename) as f:
        data = json.load(f)
    battle.players = [
        Player(p["name"], p.get("cliche", ""), p.get("dice"), )
        for p in data.get("players", [])
    ]
    for p, pd in zip(battle.players, data.get("players", [])):
        p.lost_dice = pd.get("lost_dice", 0)
    print(f"  Loaded {filename}")
    input("  Press Enter...")


def reduce_dice(battle: Battle):
    clear()
    show_state(battle)
    print("[ Reduce Dice ]")
    if not battle.players:
        print("  No players.")
        input("  Press Enter...")
        return
    for i, p in enumerate(battle.players, 1):
        if p.dice is None:
            dice_str = f"? (-{p.lost_dice})" if p.lost_dice else "?"
        else:
            dice_str = str(p.dice)
        print(f"  {i}. {p.name}  ({dice_str} dice)")
    choice = prompt_int("  Pick player: ")
    if choice is None or choice < 1 or choice > len(battle.players):
        return
    player = battle.players[choice - 1]
    if player.dice is None:
        amount = prompt_int("  How many dice lost: ")
        if amount and amount > 0:
            player.lost_dice += amount
        dead = input(f"  Is {player.name} dead? [y/n]: ").strip().lower()
        if dead == "y":
            battle.players.remove(player)
        return
    amount = prompt_int(f"  Reduce by how many dice (current: {player.dice}): ")
    if amount is None:
        return
    player.dice = max(0, player.dice - amount)
    if player.dice == 0:
        battle.players.remove(player)


def main():
    battle = Battle()

    while True:
        clear()
        show_state(battle)
        print("  1. Add player")
        print("  2. Switch cliche")
        print("  3. Reduce dice")
        print("  4. Save")
        print("  5. Load")
        print("  6. Quit")
        print()
        choice = input("> ").strip()

        if choice == "1":
            add_player(battle)
        elif choice == "2":
            switch_cliche(battle)
        elif choice == "3":
            reduce_dice(battle)
        elif choice == "4":
            save_battle(battle)
        elif choice == "5":
            load_battle(battle)
        elif choice == "6":
            sys.exit(0)


if __name__ == "__main__":
    main()
