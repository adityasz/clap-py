import clap


@clap.command(version="1.0")
class Cli(clap.Parser):
    name: str


def main():
    cli = Cli.parse()
    print(f"name: {cli.name}")


if __name__ == "__main__":
    main()
