# clap-py

A declarative, clap-rs like argument parser for Python.

## Motivation

`argparse` has verbose syntax and doesn't work with static analysis tools.

```python
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--type", type=str)
args = parser.parse_args()
print(1 / args.type)
#     ~~^~~~~~~~~~~
#  no static type checking
print(args.typo)
#     ^~~~~~~~~
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

@clap.args(
    name = "myapp",
    version = "0.1.0",
    help_template = HELP_TEMPLATE,
    after_help = AFTER_HELP,
    max_term_width = 80
)
class CliArguments:
    """A CLI that does stuff."""
    class Compile:
        """Compiles an input file into a supported output format."""
        input: Path
        """<INPUT>: Path to input file. Use `-` to read input from stdin."""
        output: Path
        """[OUTPUT]: Path to output file. Use `-` to write output to stdout."""
        format: Optional[OutputFormat] = None
        """short, long, <FORMAT>: The format of the output file, inferred from
        the extension by default."""

    class Init:
        """Initializes a new project from a template."""
        template: Path
        """<TEMPLATE>: The template to use."""
        package_cache_path: Path = Path(os.getenv("XDG_CACHE_HOME", f"{os.getenv("HOME")}/.cache"))
        """-c, long <DIR>: Custom path to package cache."""

    color: ColorChoice = ColorChoice.Auto
    """long: Whether to use color."""
    cert: Optional[Path] = None
    """Path to a custom CA certificate to use when making network requests."""
    command: Optional[Union[Compile, Watch, Init]] = None
```

`-h, --help`, `-V, --version` are available by default.

## Limitations:

- For type checkers to recognize annotations as fields (i.e., `x: int`), I have
  to decorate `clap.arguments` with `@dataclass_transform()`. This leads to
  weird issues:
  * The protocol I defined for `parse_args()` to be recognized as a classmethod
    for the command-line arguments class (i.e., the class decorated with
    `@clap.arguments`) does not work with `@dataclass_transform()` for reasons I don't know
    and hence the command-line arguments class has to inherit from `clap.Parser`
    for type checkers to not complain when `parse_args()` is called.
  * While I handle annotation -> field conversion automatically, I have to use
    `@dataclass_transform()` for type checkers to recognize annotations as fields.
    But this introduces a limitation: fields with default values can't come before
    fields without them (i.e., `y: int` can't come after `x: int = 3`). I don't
    know if how to get both things to work.

## Future work

- Parse command line arguments.

  Currently, `clap-py` is just an `argparse` wrapper: It generates Python code
  at runtime that uses `argparse` to parse the arguments.

- Support imperatively creating a parser, just like `clap-rs`.
