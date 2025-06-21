# clap-py

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

args = Cli.parse_args()
if args.verbose:
    print(f"Reading {args.input}...")
```

## Features

- **Help generation from docstrings**

  Use the same string for the help output as well as documentation in the IDE.

- **Subcommands**

  ```python
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

- **Separate short and long help** with `-h` and `--help`.

- **Customizable help output** with templates.

## Examples

See examples in [/examples](https://github.com/adityasz/clap-py/tree/master/examples).

## Docs

See [/docs](https://github.com/adityasz/clap-py/tree/master/docs).

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
starting. Thank you!

## TODO (v1.0)

- [ ] Support more tags in the help template.
- [ ] In long help, show description of possible values when the enum has
      docstrings.
- [ ] Share arguments between (sub)commands using class inheritance.

## Future work (beyond v1.0)

- [ ] Find out the python equivalent of `anstyle` and `color_print::cstr!`
      and support styled help strings that wrap properly and are formatted
      depending on output file.
- [ ] Actually parse arguments intead of relying on `argparse`.
      This will improve error message greatly.
- [ ] Add a clap-like builder API to add arguments procedurally (after defining
      some arguments in a class). One use case can be to load arguments and help
      strings from a file (which is useful when arguments/help strings are
      referenced in multiple places).
- [ ] Generate shell completions.

## Acknowledgements

[clap-rs](https://github.com/clap-rs/clap). Most docstrings are lifted verbatim.
