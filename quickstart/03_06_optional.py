from typing import Optional

import clap


@clap.command(version="1.0")
class Cli(clap.Parser):
    name: Optional[str]


def main():
    cli = Cli.parse_args()
    print(f"name: {cli.name}")


if __name__ == "__main__":
    main()
