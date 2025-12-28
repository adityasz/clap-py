from enum import Enum, auto

import clap
from clap import arg


class Mode(Enum):
    """TODO: Help strings are not yet printed for enum values in the long help output.

    See TODOs in README.md.
    """

    Fast = auto()
    """Run swiftly."""
    Slow = auto()
    """Crawl slowly but steadily.

    This paragraph is ignored because there is no long help text for possible values.
    """


@clap.command(version="1.0")
class Cli(clap.Parser):
    mode: Mode = arg()
    """What mode to run the program in."""


def main():
    cli = Cli.parse()

    match cli.mode:
        case Mode.Fast:
            print("Hare")
        case Mode.Slow:
            print("Tortoise")


if __name__ == "__main__":
    main()
