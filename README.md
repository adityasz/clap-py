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


@clap.arguments
class Cli(clap.Parser):
    command: Union[Add, Remove]


args = Cli.parse_args()
match args.command:
    case Add(file=file):
        print(f"Adding {file}...")
    case List(directory=directory):
        print(f"Listing {directory}...")
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

- [ ] Better help output

  Currently, `clap-py` uses `argparse` to output help, and that is very ugly.

## Future work

- Generate shell completions

- Actually parse command line arguments.

  Currently, `clap-py` is just an `argparse` wrapper, and error messages aren't pretty.
