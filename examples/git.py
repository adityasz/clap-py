"""
Adapted from https://github.com/clap-rs/clap/blob/master/examples/git-derive.rs
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

import clap
from clap import ColorChoice, arg, long, short


@clap.subcommand
class Clone:
    remote: str


@clap.subcommand
class Diff:
    base: Optional[str] = arg(value_name="COMMIT")
    head: Optional[str] = arg(value_name="COMMIT")
    path: Optional[str]  # what's `argparse`'s equivalent of last=true?
    color: ColorChoice = arg(
        long, value_name="WHEN", nargs="?", default_value=ColorChoice.Auto, const="always"
    )


@clap.subcommand
class Push:
    remote: str


@clap.subcommand
class Add:
    paths: list[Path] = arg(nargs="+")


@clap.subcommand
class Stash:
    @clap.subcommand
    @dataclass
    class Push:
        message: Optional[str]

    @clap.subcommand
    class Pop:
        stash: Optional[str]

    @clap.subcommand
    class Apply:
        stash: Optional[str]

    command: Optional[Union[Push, Pop, Apply]]
    # is there something like args_conflict_with_subcommands in argparse?
    message: Optional[str] = arg(short, long)


@clap.subcommand
class External:
    args: list[str] = arg(nargs="*")


@clap.command(name="git")
class Cli(clap.Parser):
    command: Union[Clone, Diff, Push, Add, Stash, External]


def main():
    args = Cli.parse_args()

    match args.command:
        case Clone(remote=remote):
            print(f"Cloning {remote}")
        case Diff(base=base, head=head, path=path, color=color):
            if path is None:
                path = head
                head = None
                if path is None:
                    path = base
                    base = None
            base = base if base is not None else "stage"
            head = head if head is not None else "worktree"
            path = path if path is not None else ""
            print(f"Diffing {base}..{head} {path} (color={color})")
        case Push(remote=remote):
            print(f"Pushing to {remote}")
        case Add(paths=paths):
            print(f"Adding {" ".join(str(path) for path in paths)}")
        case Stash(command=command, message=message):
            command = command or Stash.Push(message)
            match command:
                case Stash.Push(message=msg):
                    print(f"Pushing {msg}")
                case Stash.Pop(stash=stash):
                    print(f"Popping {stash}")
                case Stash.Apply(stash=stash):
                    print(f"Applying {stash}")
        case External(args=args):
            print(f"Calling out to {args[0]} with {args[1]}")


if __name__ == "__main__":
    main()
