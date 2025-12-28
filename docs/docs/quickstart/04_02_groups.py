from typing import Optional

import clap
from clap import arg, long


@clap.group(required=True, multiple=False)
class Vers:
    set_ver: Optional[str] = arg(long, value_name="VER")
    """Set version manually."""
    major: bool = arg(long)
    """Auto inc major."""
    minor: bool = arg(long)
    """Auto inc minor."""
    patch: bool = arg(long)
    """Auto inc patch."""


@clap.command
class Cli(clap.Parser):
    vers: Vers


def main():
    args = Cli.parse()

    # Let's assume the old version 1.2.3
    major = 1
    minor = 2
    patch = 3

    vers = args.vers
    version: str

    # See if --set_ver was used to set the version manually
    if vers.set_ver:
        version = vers.set_ver
    else:
        # Increment the one requested (in a real program, we'd reset the lower numbers)
        maj, min, pat = vers.major, vers.minor, vers.patch
        match maj, min, pat:
            case True, _, _: major += 1
            case _, True, _: minor += 1
            case _, _, True: patch += 1
            case _: raise RuntimeError()
        version = f"{major}.{minor}.{patch}"

    print(f"Version: {version}")


if __name__ == "__main__":
    main()
