# clap-py

A declarative, type-safe argument parser for Python inspired by [clap-rs](https://github.com/clap-rs/clap).

## Installation

```python
pip install clap
```

## Example

```python
import clap
from clap import arg, long, short
from pathlib import Path


@clap.arguments
class Cli(clap.Parser):
    """A tiny script."""

    input: Path = arg(metavar="<PATH>")
    """Path to the input file"""
    verbose: bool = arg(short, long)
    """Enable verbose output"""


args = Cli.parse_args()
if args.verbose:
    print(f"Reading {args.input}...")
```

Docstrings are automatically added to help.

`clap` also supports subcommands:

```python
import clap
from clap import arg, long, short
from pathlib import Path
from typing import Union


@clap.subcommand
class Add:
    file: Path


@clap.subcommand
class List:
    directory: Path


@clap.command
class Cli(clap.Parser):
    command: Union[Add, Remove]


args = Cli.parse_args()
match cmd := args.command:
    case Add():
        print(f"Adding {cmd.file}...")
    case List():
        print(f"Listing {cmd.directory}...")
```

See more examples in [/examples](https://github.com/adityasz/clap-py/tree/master/examples).

## Docs

See [/docs](https://github.com/adityasz/clap-py/tree/master/docs).

## Motivation

`argparse` requires procedural declaration and doesn't benefit from linters and
type checkers.

```python
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--type", type=str)
args = parser.parse_args()
print(1 / args.type)
#     ~~^~~~~~~~~~~
#  no static type checking
print(args.typo)
#     ~~~~~^^^^
# no static analysis
```

## TODO

- [ ] Implement `parents` in `@command()`: Maybe use inheritance?

## Future work

- Parse arguments from the command-line.

  Currently, `clap-py` uses `argparse` for parsing, so error messages look bad.

- Generate shell completions
