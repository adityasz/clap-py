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
    """Watches an input file and recompiles on changes"""

    input: Path
    """Path to input Typst file. Use `-` to read input from stdin"""
    output: Optional[Path]
    """Path to output file (PDF, PNG, SVG, or HTML). Use `-` to write output to stdout"""

    format: Optional[OutputFormat] = arg(short, long)
    """The format of the output file, inferred from the extension by default"""
    ignore_system_fonts: bool = arg(long)
    """Ensures system fonts won't be searched, unless explicitly included via `--font-path`"""
    jobs: Optional[int] = arg(short, long)
    """Number of parallel jobs spawned during compilation. Defaults to number of CPUs"""


@clap.subcommand
class Init:
    """Initializes a new project from a template"""

    template: str
    """The template to use, e.g. `@preview/charged-ieee`"""
    dir: Optional[Path]
    """The project directory, defaults to the template's name"""

    package_path: Optional[Path] = arg(value_name="DIR")
    """Custom path to local packages, defaults to system-dependent location"""


@clap.command(name="typst")
class Cli(clap.Parser):
    input: Path
    """Input."""

    command: Union[Watch, Init]

    cert: Optional[str] = arg(long)
    """Path to a custom CA certificate to use when making network requests"""


def main():
    args = Cli.parse_args()

    if (cert := args.cert):
        print(f"Using {cert} as the CA certificate")

    match args.command:
        case Watch(input=input):
            print(f"Watching {input}...")
        case Init(template=template):
            print(f"{template} is a cool template!")


if __name__ == "__main__":
    main()
