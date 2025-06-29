import clap
from clap import ArgAction, arg, long, short


@clap.command(version="1.0")
class Cli(clap.Parser):
    verbose: int = arg(short, long, action=ArgAction.Count)


def main():
    cli = Cli.parse_args()
    print(f"verbose: {cli.verbose}")


if __name__ == "__main__":
    main()
