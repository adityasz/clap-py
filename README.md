# clap-py

[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
![CI](https://github.com/adityasz/clap-py/actions/workflows/ci.yml/badge.svg)

A declarative and type-safe argument parser for Python, inspired by
[clap-rs](https://github.com/clap-rs/clap).

## Installation

- Using [uv](https://docs.astral.sh/uv):
  ```console
  $ uv add git+https://github.com/adityasz/clap-py.git
  ```

- Using pip:
  ```console
  $ pip install git+https://github.com/adityasz/clap-py.git
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

- [**Help generation from docstrings**](https://adityasz.github.io/clap-py/quickstart/#docstrings)

  Use the same string for the help output as well as documentation in the IDE.

- [**Subcommands**](https://adityasz.github.io/clap-py/quickstart/#subcommands)

  ```python
  @clap.subcommand
  class Add:
      file: Path

  @clap.subcommand
  class List:
      directory: Path

  @clap.command
  class Cli(clap.Parser):
      command: Add | List

  args = Cli.parse()
  match args.command:
      case Add(file):
          print(f"Adding {file}...")
      case List(directory):
          print(f"Listing {directory}...")
  ```

- [**Argument groups**](https://adityasz.github.io/clap-py/quickstart/#argument-relations)

  ```python
  @clap.group(required=True, multiple=False)
  class InputOptions:
      """Only one of these can be provided.

      This can be shared between multiple parsers in different scripts!"""
      dpi: Optional[int] = arg(long)
      resolution: Optional[tuple[int, int]] = arg(long, value_name="PX")
  
  @clap.command
  class Cli(clap.Parser):
      input_options: InputOptions

  args = Cli.parse()
  print(args.input_options.dpi or args.input_options.resolution)
  ```

- **Separate short and long help** with `-h` and `--help`. See example output
  [here](https://adityasz.github.io/clap-py/quickstart/#help-output).

- **Customize help output** with
  [templates](https://adityasz.github.io/clap-py/help/#clap.help.HelpTemplate)
  and [styles](https://adityasz.github.io/clap-py/styling/#clap.styling.Styles).

## Docs

Documentation along with the
[quickstart guide](https://adityasz.github.io/clap-py/quickstart/)
can be found on the [docs website](https://adityasz.github.io/clap-py)
built from [`/docs`](https://github.com/adityasz/clap-py/tree/master/docs).

## Motivation

`argparse` doesn't work with static analysis tools.

Static analysis is important to prevent errors like these:

```python
import argparse
from pathlib import Path

import torch

parser = argparse.ArgumentParser()
# 50 lines of other arguments...
parser.add_argument("--data", type=Path)
parser.add_argument("--some-number", type=Path)  # copy-paste error in type
# 30 lines of other arguments...
args = parser.parse_args()

# 500 lines of code...

c = 1 / args.some_number   # some_number was accidentally set to be Path
#   ~~^~~~~~~~~~~~~~~~~~
```

Once that error is fixed and the script is re-run:

```python
# 1500 lines of code...
 
torch.save(agi, args.data_dir / "agi.pt")  # this attribute does not exist
#               ~~~~~~~~~^^^^
```

These errors are detected right when you typed them if you use this library and
a type checker like pyright. _(A dry run is obviously still recommended before
starting long training runs. E.g., this library will not see if `args.data_dir`
exists on disk.)_

Also, using subcommands with `argparse` is error-prone because argparse returns
a flat namespace, overwriting global arguments with subcommand arguments. This
should be written in bold all over the argparse docs but it isn't. The
workaround is to manually set `dest` for each argument, which is a tedious and
error-prone process.

## Supported type checkers

clap-py is successfully type checked in CI by:

- mypy
- basedpyright

ty is in development and gives too many false positive errors. I will not add
any type ignore comments or redundant casts in my code. Hence, ty will not be a
part of the CI until the issues are fixed. However, I do run `ty check`
occasionally and make sure there are no true positives.

## Contributing

PRs that fix bugs, add features from clap-rs, or complete the following TODOs
are welcome. For adding other features, please create a discussion before
creating a PR. Thank you!

## TODO (v1.0)

- [ ] Better diagnostics (source range highlighting etc.) for incorrect parsers.
- [ ] Parse arguments manually instead of using `argparse`. This will improve
  error messages for invalid arguments.

## Future work (beyond v1.0)

- [ ] Add support for custom value parsers, validation, `conflicts_with`, etc.
- [ ] Generate shell completions.
- [ ] Add a clap-like builder API to add arguments procedurally (after
  defining some arguments in a class), which can be used together with the
  declarative API.
- [ ] Find or build out the python equivalent of `color_print::cstr!` and
  support styled help strings that wrap properly and are formatted depending on
  output file.

## Acknowledgements

[clap-rs](https://github.com/clap-rs/clap). Most docstrings are lifted verbatim.
