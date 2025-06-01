import argparse
from typing import Any, Callable, Optional, Sequence, TypeVar, Union, overload

from api import Parser, arguments
from core import (
    ColorChoice,
    Group,
    MutexGroup,
    _Action,
    _Long,
    _Nargs,
    _Short,
)

__all__ = [
    "ColorChoice",
    "Group",
    "MutexGroup",
    "Parser",
    "arg",
    "arguments",
    "subcommand",
]


T = TypeVar('T')
U = TypeVar('U')


# TODO: Add overloads based on `nargs` and `required` if `type` is not `None`.
def arg(
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
) -> Any: ...


@overload
def subcommand(cls: type[T], /) -> type[T]: ...


@overload
def subcommand(
    *,
    name: Optional[str],
    deprecated: bool = False,
    help: Optional[str] = ...,
    aliases: Sequence[str] = [],
    prog: Optional[str] = ...,
    usage: Optional[str] = ...,
    description: Optional[str] = ...,
    epilog: Optional[str] = ...,
    parents: Optional[Sequence[argparse.ArgumentParser]] = ...,
    formatter_class: argparse._FormatterClass = ...,
    prefix_chars: str = "-",
    fromfile_prefix_chars: Optional[str] = None,
    argument_default: Any = ...,
    conflict_handler: str = ...,
    add_help: bool = ...,
    allow_abbrev: bool = ...,
    exit_on_error: bool = ...,
) -> Callable[[type[T]], type[T]]: ...


# TODO: Add overloads for `required` being `True` or `False`
def subparser(
    title: Optional[str] = None,
    description: Optional[str] = None,
    prog: Optional[str] = None,
    parser_class: Optional[type] = None,
    action: Optional[_Action] = None,
    required: bool = False,
    help: Optional[str] = None,
    metavar: Optional[str] = None
) -> Any: ...
