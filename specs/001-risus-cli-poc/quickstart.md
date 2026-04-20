# Quickstart: Risus CLI POC

**Feature**: 001-risus-cli-poc

---

## Prerequisites

- Python 3.11+
- pip

---

## Install (development)

```bash
# from repo root
pip install -e .
```

This makes the `cli` command available on your PATH.

---

## Run without installing

```bash
python -m risus
```

---

## Basic session

```bash
# Start fresh
cli

# Or load a saved session
cli --load "Builders' Shack"
```

Once inside the `>` prompt:

```
> player add --name "Hanne"
Battle latest state
===================
Hanne:     0 dice ()

> player add --name "Zerox" --cliche "Firearms" --points 3
Battle latest state
===================
Hanne:     0 dice ()
Zerox:     3 dice (Firearms)

> cliche switch --name "Magic spell" --points 4 --target "Hanne"
Battle latest state
===================
Hanne:     4 dice (Magic spell)
Zerox:     3 dice (Firearms)

> cliche reduce-by --amount 2 --target "Hanne"
Battle latest state
===================
Hanne:     2 dice (Magic spell)
Zerox:     3 dice (Firearms)

> save --name "Builders' Shack"
Battle latest state (Builders' Shack)
======================================
Hanne:     2 dice (Magic spell)
Zerox:     3 dice (Firearms)

> quit
```

---

## Run tests

```bash
pytest
```

---

## Save files location

Saves are stored in `~/.risus/saves/` as JSON files. You can inspect or delete them manually.

---

## Project layout

```
risus/
├── __main__.py       # Entry point: parses --load, launches REPL
├── repl.py           # Interactive REPL (cmd.Cmd subclass)
├── models.py         # Player, BattleState dataclasses + errors
├── persistence.py    # save/load JSON to ~/.risus/saves/
└── display.py        # Battle state table renderer

tests/
├── test_models.py
├── test_persistence.py
├── test_repl.py
└── test_display.py

pyproject.toml
```
