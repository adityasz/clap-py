from ast import TypeVar
from dataclasses import dataclass
from typing import Optional, Literal, Union, Sequence, get_origin, get_args, cast


T = TypeVar('T')
U = TypeVar('U')


class short:
    """Autogenerate short name"""
    def __init__(self):
        ...

class long:
    """Autogenerate long name"""
    ...


_Action = Literal[
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

_Nargs = Union[Literal['?', '*', '+'], int]


@dataclass
class Argument[T, U]:
    """Represents the parameters of an argument for `argparse.ArgumentParser`."""
    short_: Optional[Union[type[short], str]] = None
    """Short flag for the argument (e.g., '-v')."""
    long_: Optional[Union[type[long], str]] = None
    """Long flag for the argument (e.g., '--version')."""
    action: Optional[_Action] = None
    """Action to be taken when this argument is encountered."""
    nargs: Optional[_Nargs] = None
    """Number of command-line arguments that should be consumed."""
    const: Optional[U] = None
    """Constant value required by some action and nargs selections."""
    default: Optional[U] = None
    """Default value for the argument if not provided."""
    type_: Optional[type[T]] = None
    """Type to which the command-line argument should be converted."""
    choices: Optional[Sequence[str]] = None
    """Sequence of valid choices for the argument."""
    required: bool = False
    """Whether the argument is required or optional."""
    help: Optional[str] = None
    """Brief description of what the argument does."""
    metavar: Optional[str] = None
    """Name for the argument in usage messages."""
    deprecated: bool = False
    """Whether this argument is deprecated and should not be used."""


def arg[T, U](
    type_or_short: Optional[Union[type[T], type[short], str]] = None,
    short_: Optional[Union[type[short], str]] = None,
    *,
    long_: Optional[Union[type[long], str]] = None,
    action: Optional[_Action] = "store",
    nargs: Optional[_Nargs] = None,
    const: Optional[U] = None,
    default: Optional[U] = None,
    choices: Optional[Sequence[str]] = None,
    required: Optional[bool] = False,
    help: Optional[str] = None,
    metavar: Optional[str] = None,
    deprecated: bool = False
) -> Argument:
    short_name = None
    type_ = None

    if (
        isinstance(type_or_short, str)
        or (
            get_origin(type_or_short) is type
            and get_args(type_or_short)[0] is short
            and len(get_args(type_or_short)) == 1
        )
    ):
        short_name = cast(type[short], type_or_short)
    else:
        type_ = type_or_short
        short_name = short_

    return Argument(
        short_=short_name,
        long_=long_,
        action=action,
        nargs=nargs,
        const=const,
        default=default,
        type_=type_,
        choices=choices,
        required=required or False,
        help=help,
        metavar=metavar,
        deprecated=deprecated
    )

def positional[T, U](
    type: Optional[type[T]] = None,
    /,
    *,
    action: Optional[_Action] = "store",
    nargs: Optional[_Nargs] = None,
    default: Optional[U] = None,
    choices: Optional[Sequence[str]] = None,
    metavar: Optional[str] = None,
    deprecated: bool = False
) -> Argument:
    return arg(
        type,
        action=action,
        nargs=nargs,
        default=default,
        choices=choices,
        metavar=metavar,
        deprecated=deprecated
    )


def option[T, U](
    type_or_short: Optional[Union[type[T], str, type[short]]] = None,
    short: Optional[str] = None,
    /,
    *,
    long: Optional[str] = None,
    action: Optional[_Action] = "store",
    nargs: Optional[_Nargs] = None,
    const: Optional[U] = None,
    default: Optional[U] = None,
    choices: Optional[Sequence[str]] = None,
    required: None = None,
    metavar: Optional[str] = None,
    deprecated: bool = False
) -> Argument:
    return arg(
        type_or_short,
        short,
        long_=long,
        action=action,
        nargs=nargs,
        const=const,
        default=default,
        choices=choices,
        required=required,
        metavar=metavar,
        deprecated=deprecated
    )


def flag(
    short: Optional[str] = None,
    /,
    *,
    long: Optional[str] = None,
    count: bool = False
) -> Argument:
    if count:
        return arg(bool, short, long_=long, action="count")
    else:
        return arg(bool, short, long_=long, action="store_true")
