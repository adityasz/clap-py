from pathlib import Path

import clap
from clap import AnsiColor, Style, Styles, arg, long, short


@clap.command
class Cli(clap.Parser):
    input: Path
    """The input file."""

    group = clap.group("Hello")
    """This is a nice group.

    With a long about."""

    verbose: bool = arg(short, long, group=group)
    """Verbose..."""


args = Cli.parse_args()

styles = (Styles().header(Style().bold().underline())
             .literal(Style().fg_color(AnsiColor.Green).bold()))
