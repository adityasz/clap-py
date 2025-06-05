import sys
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Optional, Union

import clap
from clap import ColorChoice, arg, long, short

GREEN = "\033[32m"
RESET = "\033[0m"


def set_color(choice: ColorChoice):
    global GREEN, RESET
    if choice == ColorChoice.Never:
        GREEN = ""
        RESET = ""
    elif choice == ColorChoice.Auto:
        if not (hasattr(sys.stdout, "isatty") and sys.stdout.isatty()):
            GREEN = ""
            RESET = ""


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

    package_path: Optional[Path] = arg(metavar="DIR")
    """Custom path to local packages, defaults to system-dependent location"""


@clap.arguments(prog="typst")
class Cli(clap.Parser):
    command: Union[Watch, Init]

    color: ColorChoice = arg(long, metavar="COLOR", default=ColorChoice.Auto)
    """Whether to use color. When set to `auto` if the terminal supports it"""
    cert: Optional[str] = arg(long, metavar="CERT")
    """Path to a custom CA certificate to use when making network requests"""


def main():
    args = Cli.parse_args()

    if args.color:
        set_color(args.color)

    if (cert := args.cert):
        print(f"Using {cert} as the CA certificate")

    match args.command:
        case Watch(input=input):
            print(f"{GREEN}Watching{RESET} {input}...")
        case Init(template=template):
            print(f"{template} is a {GREEN}cool{RESET} template!")


if __name__ == "__main__":
    main()
