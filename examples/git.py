"""
Adapted from https://github.com/clap-rs/clap/blob/master/examples/git-derive.rs
"""

from pathlib import Path
from typing import Optional

import clap
from clap import ColorChoice, arg, long, short


@clap.subcommand
class Clone:
    remote: str


@clap.subcommand
class Diff:
    base: Optional[str] = arg(value_name="COMMIT")
    head: Optional[str] = arg(value_name="COMMIT")
    path: Optional[str] = arg()  # what's `argparse`'s equivalent of last=true?
    color: ColorChoice = arg(
        long,
        value_name="WHEN",
        num_args="?",
        default_value=ColorChoice.Auto,
        default_missing_value="always",
    )


@clap.subcommand
class Push:
    remote: str


@clap.subcommand
class Add:
    paths: list[Path] = arg(num_args="+")


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

    command: Optional[Push | Pop | Apply]
    message: Optional[str] = arg(short, long)


@clap.subcommand
class External:
    args: list[str] = arg(num_args="*")


@clap.command(name="git")
class Cli(clap.Parser):
    command: Clone | Diff | Push | Add | Stash | External


def main():
    cli = Cli.parse()

    match cli.command:
        case Clone(remote):
            print(f"Cloning {remote}")
        case Diff(base, head, path, color):
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
        case Push(remote):
            print(f"Pushing to {remote}")
        case Add(paths):
            print(f"Adding {' '.join(str(path) for path in paths)}")
        case Stash(command, message):
            command = command or Stash.Push(message)
            match command:
                case Stash.Push(msg):
                    print(f"Pushing {msg}")
                case Stash.Pop(stash):
                    print(f"Popping {stash}")
                case Stash.Apply(stash):
                    print(f"Applying {stash}")
        case External(args):
            print(f"Calling out to {args[0]} with {args[1]}")


if __name__ == "__main__":
    main()
