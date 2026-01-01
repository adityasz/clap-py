import clap


def smoke_test():
    @clap.command
    class Cli(clap.Parser):
        name: str

    args = Cli.parse(["test"])
    assert args.name == "test"


if __name__ == "__main__":
    smoke_test()
