import clap
from clap import arg


@clap.command(version="1.0")
class Cli(clap.Parser):
    name: str | None = arg()
    # Alternatively, you can use name: Optional[str] = arg()


def main():
    cli = Cli.parse()
    print(f"name: {cli.name}")


if __name__ == "__main__":
    main()
