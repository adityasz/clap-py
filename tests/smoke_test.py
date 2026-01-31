import clap


def smoke_test():
    @clap.command
    class Cli(clap.Parser):
        name: str

    cli = Cli.parse(["test"])
    assert cli.name == "test"


if __name__ == "__main__":
    smoke_test()
