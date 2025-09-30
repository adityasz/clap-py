import clap
from clap import arg


@clap.command(version="1.0")
class Cli(clap.Parser):
    port: int = arg(default_value=2020)


def main():
    cli = Cli.parse()
    print(f"port: {cli.port}")


if __name__ == "__main__":
    main()
