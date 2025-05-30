import argparse
from ast import TypeVar
from dataclasses import asdict, dataclass
from typing import Any, Literal, Optional, Sequence, Union, cast


class _Short:
    ...


class _Long:
    ...


class Subcommand:
    ...


@dataclass
class Group:
    name: str


@dataclass
class MutexGroup:
    parent: Optional[Group] = None


short = _Short()
"""Generate short from the first character in the case-converted field name."""

long = _Long()
"""Generate long from the case-converted field name."""

_Action = Union[
    argparse.Action,
    Literal[
        "store",
        "store_const",
        "store_true",
        "store_false",
        "append",
        "append_const",
        "extend",
        "count",
        "help",
        "version"
    ]
]

_Nargs = Union[Literal['?', '*', '+'], int]

T = TypeVar('T')
U = TypeVar('U')


@dataclass
class ArgumentInfo[T, U]:
    """The properties of a command-line argument."""

    short: Optional[Union[_Short, str]] = None
    """The short flag for the argument."""
    long: Optional[Union[_Long, str]] = None
    """The long flag for the argument."""
    group: Optional[Group] = None
    """The group for the argument."""
    mutex: Optional[MutexGroup] = None
    """The mutually exclusive group for the argument."""
    action: Optional[_Action] = None
    """The action to be taken when this argument is encountered."""
    nargs: Optional[_Nargs] = None
    """The number of command-line arguments that should be consumed."""
    const: Optional[U] = None
    """The constant value required by some action and nargs selections."""
    default: Optional[U] = None
    """The default value for the argument if not provided."""
    type_: Optional[type[T]] = None
    """The type to which the command-line argument should be converted."""
    choices: Optional[Sequence[str]] = None
    """A sequence of valid choices for the argument."""
    required: bool = True
    """Whether the argument is required or optional."""
    help: Optional[str] = None
    """A brief description of what the argument does."""
    metavar: Optional[str] = None
    """The name for the argument in usage messages."""
    deprecated: bool = False
    """Whether this argument is deprecated and should not be used."""
    commands: Optional[list[type]] = None
    """..."""

    def get_kwargs(self) -> dict[str, Any]:
        kwargs = asdict(self)
        for k, v in kwargs.items():
            if v is None:
                kwargs.pop(k)
        return kwargs


@dataclass
class SubcommandInfo:
    subparser_info: "ParserInfo"
    title: Optional[str] = "Commands"
    description: Optional[str] = None
    prog: Optional[str] = None
    parser_class: Optional[type] = None
    action: Optional[_Action] = None
    required: bool = False
    help: Optional[str] = None
    metavar: Optional[str] = None

    def get_kwargs(self) -> dict[str, Any]:
        kwargs = asdict(self)
        for k, v in kwargs.items():
            if v is None:
                kwargs.pop(k)
        return kwargs


@dataclass
class ParserInfo:
    arguments: dict[str, ArgumentInfo]
    subcommands: dict[str, SubcommandInfo]
    groups: dict[Group, ArgumentInfo]
    mutexes: dict[MutexGroup, ArgumentInfo]


def arg[T, U](
    short_or_long: Optional[Union[_Short, _Long, str]] = None,
    long_: Optional[Union[_Long, str]] = None,
    /,
    *,
    short: Optional[Union[str, bool]] = None,
    long: Optional[Union[str, bool]] = None,
    group: Optional[Group] = None,
    mutex: Optional[MutexGroup] = None,
    type: Optional[type[T]] = None,
    action: Optional[_Action] = "store",
    nargs: Optional[_Nargs] = None,
    const: Optional[U] = None,
    default: Optional[U] = None,
    choices: Optional[Sequence[str]] = None,
    required: Optional[bool] = True,
    help: Optional[str] = None,
    metavar: Optional[str] = None,
    deprecated: bool = False
) -> ArgumentInfo:
    """Create a command-line argument."""
    short_name = None
    long_name = None

    if isinstance(short_or_long, _Long):
        short_name = None
        long_name = cast(_Long, short_or_long)
    elif (
        isinstance(short_or_long, str) and (
            short_or_long.startswith("--")
            or (not short_or_long.startswith("-") and len(short_or_long) > 1)
        )
    ):
        short_name = None
        long_name = cast(str, short_or_long)
    else:
        short_name = cast(Optional[Union[_Short, str]], short_or_long)
        long_name = long_

    if short is not None:
        if isinstance(short, str):
            short_name = short
        elif short is True:
                short_name = _Short()

    if long is not None:
        if isinstance(long, str):
            long_name = long
        elif long is True:
                long_name = _Long()

    return ArgumentInfo(
        short=short_name,
        long=long_name,
        action=action,
        nargs=nargs,
        const=const,
        default=default,
        type_=type,
        choices=choices,
        required=required or False,
        help=help,
        metavar=metavar,
        deprecated=deprecated
    )


def subcommand():
    """Declare a field as containing subcommand arguments."""
    return Subcommand()
