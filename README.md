# typed-clap[^1]

![CI](https://github.com/adityasz/typed-clap/actions/workflows/ci.yml/badge.svg)

A declarative and type-safe argument parser for Python, inspired by
[clap-rs](https://github.com/clap-rs/clap).

## Installation [![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

- Using uv: `uv add typed-clap`
- Using pip: `pip install typed-clap`

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

See [/examples](https://github.com/adityasz/typed-clap/tree/master/examples)
for more examples.

## Features

- [**Help generation from docstrings**](https://adityasz.github.io/typed-clap/quickstart/#docstrings)

  Use the same string for the help output as well as documentation in the IDE.

- [**Subcommands**](https://adityasz.github.io/typed-clap/quickstart/#subcommands)

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

- [**Argument groups**](https://adityasz.github.io/typed-clap/quickstart/#argument-relations)

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
  [here](https://adityasz.github.io/typed-clap/quickstart/#help-output).

- **Customize help output** with
  [templates](https://adityasz.github.io/typed-clap/help/#clap.help.HelpTemplate)
  and [styles](https://adityasz.github.io/typed-clap/styling/#clap.styling.Styles).

## Docs

Documentation along with the
[quickstart guide](https://adityasz.github.io/typed-clap/quickstart/)
can be found on the [docs website](https://adityasz.github.io/typed-clap)
built from [`/docs`](https://github.com/adityasz/typed-clap/tree/master/docs).

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

typed-clap is successfully type checked in CI by:

- [mypy](https://mypy-lang.org/)
- [basedpyright](https://docs.basedpyright.com/latest/)

It can also be used with [ty](https://docs.astral.sh/ty/)[^2].

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

[^1]: Because the names clap{,-py,-python} were already taken on PyPI :-(
[^2]: ty is not a part of the CI because it gives some false positives in the
completely standard _internal_ code since ty is not complete and still a WIP.
It does not have any issues with the APIs of this library or their usage,
though.
