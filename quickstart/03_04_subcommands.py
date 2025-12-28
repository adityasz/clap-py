import clap
from clap import arg


@clap.subcommand
class Add:
    """Adds files to myapp."""

    name: str = arg()


@clap.subcommand
class Remove:
    """Remove files from myapp."""

    name: str = arg()


@clap.command(version="1.0", propagate_version=True)
class Cli(clap.Parser):
    command: Add | Remove
    # Alternatively, you can write command: Union[Add, Remove]

    quiet: bool = arg(short=True, long=True)


def main():
    args = Cli.parse()

    # You can check for the existence of subcommands, and if found use their
    # matches just as you would the top level cmd
    match args.command:
        case Add(name):
            if not args.quiet:
                print(f"'myapp add' was used, name is: {name}")
        case Remove(name):
            if not args.quiet:
                print(f"'myapp remove' was used, name is: {name}")


if __name__ == "__main__":
    main()
