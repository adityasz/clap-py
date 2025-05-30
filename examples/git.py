"""
Adapted from https://github.com/clap-rs/clap/blob/master/examples/git-derive.rs
"""

from pathlib import Path
from typing import Optional, Union

import clap
from clap import arg, ColorChoice


@clap.subcommand
class Clone:
    remote: str


@clap.subcommand
class Diff:
    base: Optional[str] = arg(metavar="COMMIT")
    head: Optional[str] = arg(metavar="COMMIT")
    path: Optional[str]  # what's `argparse`'s equivalent of last=true?
    color: ColorChoice = arg(long=True, metavar="WHEN", nargs='?',
                             default=ColorChoice.Auto, const="always")


@clap.subcommand
class Push:
    remote: str


@clap.subcommand
class Add:
    path: list[Path] = arg(nargs='+')


@clap.subcommand
class Stash:
    @clap.subcommand
    class Push:
        message: Optional[str]

    @clap.subcommand
    class Pop:
        stash: Optional[str]

    @clap.subcommand
    class Apply:
        stash: Optional[str]

    command: Union[Push, Pop, Apply]
    push: Optional[str]


@clap.subcommand
class External:
    args: list[str] = arg(nargs='*')


@clap.arguments(
    name="git",
    description="A fictional versioning CLI"
)
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
        case Add(path=path):
            print(f"Adding {path}")
        case Stash(command=command, push=push):
            if command is None:
                command = push
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
