import clap
from clap import arg, long


@clap.command(name="MyApp", version="1.0")
class Cli(clap.Parser):
    """Does awesome things."""

    two: str = arg(long)
    one: str = arg(long)


def main():
    cli = Cli.parse()

    print(f"two: {cli.two}")
    print(f"one: {cli.one}")


if __name__ == "__main__":
    main()
