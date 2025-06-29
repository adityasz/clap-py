from typing import Optional

import clap


@clap.subcommand
class Add:
    """Adds files to myapp."""

    name: Optional[str]


@clap.command(version="1.0", propagate_version=True)
class Cli(clap.Parser):
    command: Add


def main():
    cli = Cli.parse_args()

    # You can check for the existence of subcommands, and if found use their
    # matches just as you would the top level cmd
    match cli.command:
        case Add(name):
            print(f"'myapp add' was used, name is: {name}")


if __name__ == "__main__":
    main()
