# clap-py

[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
![CI](https://github.com/adityasz/clap-py/actions/workflows/ci.yml/badge.svg)

A declarative and type-safe argument parser for Python, inspired by
[clap-rs](https://github.com/clap-rs/clap).

## Installation

- Using pip:
  ```console
  $ pip install git+https://github.com/adityasz/clap-py.git
  ```

- Using [uv](https://docs.astral.sh/uv):
  ```console
  $ uv add git+https://github.com/adityasz/clap-py.git
  ```

## Example

```python
import clap
from clap import arg, long, short
from pathlib import Path

@clap.command
class Cli(clap.Parser):
    """A tiny script."""

    input: Path = arg(value_name="PATH")
    """Path to the input file."""
    verbose: bool = arg(short, long)
    """Enable verbose output."""

args = Cli.parse()
if args.verbose:
    print(f"Reading {args.input}...")
```

See [/examples](https://github.com/adityasz/clap-py/tree/master/examples)
for more examples.

## Features

- **Help generation from docstrings**

  Use the same string for the help output as well as documentation in the IDE.

- **Subcommands**

  ```python
  @clap.subcommand
  class Add:
      file: Path

  @clap.subcommand
  class List:
      directory: Path

  @clap.command
  class Cli(clap.Parser):
      command: Union[Add, List]

  args = Cli.parse()
  match args.command:
      case Add(file):
          print(f"Adding {file}...")
      case List(directory):
          print(f"Listing {directory}...")
  ```

- **Separate short and long help** with `-h` and `--help`. See example output
  [here](https://adityasz.github.io/clap-py/quickstart/#help).

- **Customize help output** with
  [templates](https://adityasz.github.io/clap-py/help/#clap.help.HelpTemplate)
  and [styles](https://adityasz.github.io/clap-py/styling/#clap.styling.Styles).

## Docs

Documentation along with the
[quickstart guide](https://adityasz.github.io/clap-py/quickstart/)
can be found on the [docs website](https://adityasz.github.io/clap-py)
built from [`/docs`](https://github.com/adityasz/clap-py/tree/master/docs).

## Motivation

`argparse` requires procedural declaration, which doesn't work with static
analysis tools. Using subcommands with `argparse` is error-prone because
argparse returns a flat namespace, overwriting global arguments with subcommand
arguments, and hence requires manually setting `dest` for each argument, which
is a tedious and error-prone process.

```python
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--type")
args = parser.parse_args()
print(1 / args.type)
#     ~~^~~~~~~~~~~
#  no static type checking
print(args.typo)
#     ~~~~~^^^^
# no static analysis
```

## Contributing

PRs that fix bugs, add features from clap-rs, or complete the following TODOs
are welcome. For adding other features, please create a discussion before
creating a PR. Thank you!

## TODO (v1.0)

- [ ] Actually parse arguments instead of using `argparse`. This will help
      improve error messages and enable features like `requires_all`,
      `conflicts_with`, etc.

## Future work (beyond v1.0)

- [ ] Create argument groups using classes.
- [ ] Generate shell completions.
- [ ] Add a clap-like builder API to add arguments procedurally (after
      defining some arguments in a class). One use case can be to load
      arguments and help strings from a file (which is useful when
      arguments/help strings are referenced in multiple places).
- [ ] Find or build out the python equivalent of `color_print::cstr!` and
      support styled help strings that wrap properly and are formatted depending
      on output file.

## Acknowledgements

[clap-rs](https://github.com/clap-rs/clap). Most docstrings are lifted verbatim.
