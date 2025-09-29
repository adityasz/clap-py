from pathlib import Path
from typing import Optional

import clap
from clap import ArgAction, arg, long, short


@clap.subcommand
class Test:
    """Does testing things."""

    list_flag: bool = arg(short, long="list")
    """Lists test values."""


@clap.command(version="1.0")
class Cli(clap.Parser):
    """A simple to use, efficient, and full-featured Command Line Argument Parser."""

    command: Optional[Test]

    name: Optional[str]
    """Optional name to operate on."""
    config: Optional[Path] = arg(short, long, value_name="FILE")
    """Sets a custom config file."""
    debug: int = arg(short, long, action=ArgAction.Count)
    """Turn debugging information on."""


def main():
    cli = Cli.parse()

    # You can check the value provided by positional arguments, or option arguments
    if cli.name:
        print(f"Value for name: {cli.name}")

    if cli.config:
        print(f"Value for config: {cli.config}")

    # You can see how many times a particular flag or argument occurred
    # Note, only flags can have multiple occurrences
    match cli.debug:
        case 0:
            print("Debug mode is off")
        case 1:
            print("Debug mode is kind of on")
        case 2:
            print("Debug mode is on")
        case _:
            print("Don't be crazy")

    # You can check for the existence of subcommands, and if found use their
    # matches just as you would the top level cmd
    match cli.command:
        case Test(list_flag):
            if list_flag:
                print("Printing testing lists...")
            else:
                print("Not printing testing lists...")
        case None: ...

    # Continued program logic goes here...


if __name__ == "__main__":
    main()
