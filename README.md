# clap-py

A declarative, clap-rs like argument parser for Python.

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

## Example

```python
from pathlib import Path
from typing import Optional, Union

import clap
from clap import ColorChoice


HELP_TEMPLATE = """\
{name} {version}

{usage-heading} {usage}

{all-args}{after-help}
"""

AFTER_HELP=""

@clap.arguments
class Cli:
    """A CLI that does stuff."""

    @clap.subcommand
    class Compile:
        """Compiles an input file into a supported output format."""

        input: Path
        """<INPUT>: Path to input file. Use `-` to read input from stdin."""
        output: Path
        """[OUTPUT]: Path to output file. Use `-` to write output to stdout."""
        format: Optional[OutputFormat] = None
        """short, long, <FORMAT>: The format of the output file, inferred from
        the extension by default."""

    @clap.subcommand
    class Init:
        """Initializes a new project from a template."""

        template: Path
        """<TEMPLATE>: The template to use."""
        package_cache_path: Path = Path(os.getenv("XDG_CACHE_HOME", f"{os.getenv("HOME")}/.cache"))
        """-c, long <DIR>: Custom path to package cache."""

    color: ColorChoice = ColorChoice.Auto
    """long: Whether to use color."""
    cert: Optional[Path]
    """Path to a custom CA certificate to use when making network requests."""
    command: Optional[Union[Compile, Watch, Init]]
```

## Limitations

Same as `argparse`.

## TODO

- [ ] Better help output

  Currently, `clap-py` uses `argparse` to output help, and that is very ugly.

## Future work

- Generate shell completions

- Actually parse command line arguments.

  Currently, `clap-py` is just an `argparse` wrapper, and error messages aren't pretty.
