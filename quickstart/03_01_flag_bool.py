import clap
from clap import arg, long, short


@clap.command(version="1.0")
class Cli(clap.Parser):
    verbose: bool = arg(short, long)


def main():
    cli = Cli.parse()
    print(f"verbose: {cli.verbose}")


if __name__ == "__main__":
    main()
