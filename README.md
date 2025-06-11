# clap-py

A declarative and type-safe argument parser for Python, inspired by [clap-rs](https://github.com/clap-rs/clap).

## Installation

```console
$ pip install git+https://github.com/adityasz/clap-py.git
```

## Example

```python
from pathlib import Path

import clap
from clap import arg, long, short


@clap.command
class Cli(clap.Parser):
    """A tiny script."""

    input: Path = arg(value_name="PATH")
    """Path to the input file"""
    verbose: bool = arg(short, long)
    """Enable verbose output"""


args = Cli.parse_args()
if args.verbose:
    print(f"Reading {args.input}...")
```

## Features

### Help generation from docstrings

The same string works for documentation in the IDE and help output.

### Subcommands

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Union

import clap
from clap import arg, long, short


@dataclass
@clap.subcommand
class Add:
    file: Path


@dataclass
@clap.subcommand
class List:
    directory: Path


@clap.command
class Cli(clap.Parser):
    command: Union[Add, List]


args = Cli.parse_args()
match args.command:
    case Add(file):
        print(f"Adding {file}...")
    case List(directory):
        print(f"Listing {directory}...")
```

The `@dataclass` decorator is not required for subcommands to work; it is added
for structural pattern matching in the `match`-`case`.

## Examples

See examples in [/examples](https://github.com/adityasz/clap-py/tree/master/examples).

## Docs

TODO <!-- See [/docs](https://github.com/adityasz/clap-py/tree/master/docs). -->

## Motivation

`argparse` requires procedural declaration, which doesn't work with static
analysis tools. Using subcommands with `argparse` is error-prone because
argparse returns a flat namespace, overwriting global arguments with subcommand
arguments, and hence requires manually setting `dest` for each argument (with no
safety checks!).

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

## Roadmap

- [ ] Support more tags in the help template.
- [ ] Share arguments between (sub)commands using class inheritance.
- [ ] Actually parse arguments intead of relying on `argparse`.
      This will improve error message greatly.
- [ ] Generate shell completions.
