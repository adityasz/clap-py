import sys
from enum import Enum, auto
from pathlib import Path
from typing import Optional, Union

import clap
from clap import AnsiColor, ColorChoice, Style, arg, long, short


class OutputFormat(Enum):
    PDF = auto()
    PNG = auto()
    SVG = auto()
    HTML = auto()


@clap.subcommand(aliases=("w"))
class Watch:
    """Watches an input file and recompiles on changes."""

    input: Path
    """Path to input Typst file. Use `-` to read input from stdin."""
    output: Optional[Path]
    """Path to output file (PDF, PNG, SVG, or HTML). Use `-` to write output to stdout.

    For output formats emitting one file per page (PNG & SVG), a page number template
    must be present if the source document renders to multiple pages. Use `{p}` for
    page numbers, `{0p}` for zero padded page numbers and `{t}` for page count. For
    example, `page-{0p}-of-{t}.png` creates `page-01-of-10.png`, `page-02-of-10.png`,
    and so on.
    """

    format: Optional[OutputFormat] = arg(short, long)
    """The format of the output file, inferred from the extension by default."""
    ignore_system_fonts: bool = arg(long)
    """Ensures system fonts won't be searched, unless explicitly included via `--font-path`."""
    jobs: Optional[int] = arg(short, long)
    """Number of parallel jobs spawned during compilation. Defaults to number of CPUs."""


@clap.subcommand
class Init:
    """Initializes a new project from a template."""

    template: str
    """The template to use, e.g. `@preview/charged-ieee`."""
    dir: Optional[Path]
    """The project directory, defaults to the template's name."""

    package_path: Optional[Path] = arg(long, value_name="DIR")
    """Custom path to local packages, defaults to system-dependent location."""


@clap.command(name="typst")
class Cli(clap.Parser):
    command: Union[Watch, Init]

    cert: Optional[str] = arg(long)
    """Path to a custom CA certificate to use when making network requests."""
    color: ColorChoice = arg(long, default_value=ColorChoice.Auto)
    """Whether to use color. When set to `auto` if the terminal to supports it."""


def main():
    args = Cli.parse_args()

    if args.color == ColorChoice.Always or (
        args.color == ColorChoice.Auto and sys.stdout.isatty()
    ):
        verb = Style().fg_color(AnsiColor.Green).bold()
        info = Style().fg_color(AnsiColor.Blue).bold()
    else:
        verb = info = Style()

    if cert := args.cert:
        print(f"Using {info}'{cert}'{info:#} as the CA certificate\n")

    match args.command:
        case Watch(input):
            print(
                f"{verb}watching{verb:#} {input}\n"
                f"{verb}writing to{verb:#} {input.with_suffix(".pdf")}\n\n"
                f"[01:45:47] compiled successfully in 1 picosecond (because typst is way too fast)"
            )
        case Init(template):
            print(
                f"{info}'{template}'{info:#} "
                f"is a cool template!"
            )


if __name__ == "__main__":
    main()
