# Risus CLI

## Execution requirements


``` bash
. ./.venv/bin/activate
pip install --editable .
python3 -m risus
deactivate
```

## Example Session

```text
$ cli player add --name "Hanne"
Battle latest state
===================
(Name):    (proficiency / skill level / life points) (Skill name used in battle)

Hanne:     0 dice ()

$ cli cliche switch --name "Magic spell" --points 4 --target "Hanne"
Battle latest state
===================
(Name):    (number of dice) (Cliché used in battle)

Hanne:     4 dice (Magic spell)

$ cli player add --name "Zerox" --cliche "Firearms" --points 3
Battle latest state
===================
(Name):    (proficiency / skill level / life points) (Skill name used in battle)

Hanne:     4 dice (Magic spell)
Zerox:     3 dice (Firearms)

$ cli cliche reduce-by --amount 2 --target "Hanne"
Battle latest state
===================
(Name):    (number of dice) (Cliché used in battle)

Hanne:     2 dice (Magic spell)
Zerox:     3 dice (Firearms)

$ cli cliche switch --name "Throw stones" --points 4 --target "Hanne"
Battle latest state
===================
(Name):    (number of dice) (Cliché used in battle)

Hanne:     4 dice (Throw stones)
Zerox:     3 dice (Firearms)

$ cli save --name "Builders' Shack"
Battle latest state (Builders' Shack)
=====================================
(Name):    (number of dice) (Cliché used in battle)

Hanne:     4 dice (Throw stones)
Zerox:     3 dice (Firearms)

$ cli load --name "Builders' Shack"
Battle latest state (Builders' Shack)
=====================================
(Name):    (number of dice) (Cliché used in battle)

Hanne:     4 dice (Throw stones)
Zerox:     3 dice (Firearms)
```

## Design

The design of the CLI commands and parameters is based on how the kubernetes and
docker CLIs work. The idea is to specify the resource first, then the action, then the
arguments or attributes required to satisfy the action.

## Candidate Libraries for CLI parsing

- golang cobra
- rust clap
- python click
- csharp system.commandline / dragonfruit (dragonfruit2)
- node commander

## Future extensions

- Add output format parameter to produce JSON, TOON, or other formats.
