from enum import Enum, auto
from pathlib import Path
from typing import Optional, Union

import clap
from clap import arg, long, short


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


@clap.command(name="typst", color=clap.ColorChoice.Always)
class Cli(clap.Parser):
    command: Union[Watch, Init]

    cert: Optional[str] = arg(long)
    """Path to a custom CA certificate to use when making network requests."""


def main():
    args = Cli.parse_args()

    if cert := args.cert:
        print(f"Using {cert} as the CA certificate")

    match args.command:
        case Watch(input):
            print(f"Watching {input}...")
        case Init(template):
            print(f"{template} is a cool template!")


if __name__ == "__main__":
    main()
