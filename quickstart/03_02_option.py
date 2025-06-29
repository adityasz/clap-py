import clap
from clap import arg, long, short


@clap.command(version="1.0")
class Cli(clap.Parser):
    name: str = arg(short, long)


def main():
    cli = Cli.parse_args()
    print(f"name: {cli.name}")


if __name__ == "__main__":
    main()
