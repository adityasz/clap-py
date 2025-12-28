import sys
from typing import Optional

import clap
from clap import arg, long, short


@clap.command(version="1.0")
class Cli(clap.Parser):
    input_file: Optional[str] = arg()
    """Some regular input."""

    set_ver: Optional[str] = arg(long, value_name="VER")
    """Set version manually."""

    major: bool = arg(long)
    """Auto inc major."""

    minor: bool = arg(long)
    """Auto inc minor."""

    patch: bool = arg(long)
    """Auto inc patch."""

    spec_in: Optional[str] = arg(long)
    """Some special input argument."""

    config: Optional[str] = arg(short)


def main():
    cli = Cli.parse()

    # Let's assume the old version 1.2.3
    major = 1
    minor = 2
    patch = 3

    # See if --set-ver was used to set the version manually
    if cli.set_ver is not None:
        if cli.major or cli.minor or cli.patch:
            print("error: Can't do relative and absolute version change", file=sys.stderr)
            sys.exit(1)
        version = cli.set_ver
    else:
        # Increment the one requested (in a real program, we'd reset the lower numbers)
        flags_set = [cli.major, cli.minor, cli.patch]
        if sum(flags_set) != 1:
            print("error: Can only modify one version field", file=sys.stderr)
            sys.exit(1)

        if cli.major:
            major += 1
        elif cli.minor:
            minor += 1
        elif cli.patch:
            patch += 1
        else:
            print(
                "error: Must specify one of --set-ver, --major, --minor, or --patch",
                file=sys.stderr,
            )
            sys.exit(1)

        version = f"{major}.{minor}.{patch}"

    print(f"Version: {version}")

    # Check for usage of -c
    if cli.config is not None:
        input_file = cli.input_file or cli.spec_in
        if input_file is None:
            print(
                "error: INPUT_FILE or --spec-in is required when using --config", file=sys.stderr
            )
            sys.exit(1)
        print(f"Doing work using input {input_file} and config {cli.config}")


if __name__ == "__main__":
    main()
