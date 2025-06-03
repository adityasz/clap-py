import argparse
from collections.abc import Callable, Sequence
from typing import Any, Optional, TypeVar, Union, overload

from .api import Group, MutexGroup, Parser, group, mutex_group
from .core import ActionType, ColorChoice, NargsType, _LongFlag, _ShortFlag, long, short

__all__ = [
    "ColorChoice",
    "Parser",
    "arg",
    "arguments",
    "group",
    "mutex_group",
    "subcommand",
    "short",
    "long"
]

T = TypeVar('T')
U = TypeVar('U')

# TODO: Add overloads that return `Optional[Any]` based on the `required` and `default` parameters.
def arg(
    short_or_long: Optional[Union[_ShortFlag, _LongFlag, str]] = None,
    long_: Optional[Union[_LongFlag, str]] = None,
    /,
    *,
    short: Optional[Union[str, bool]] = ...,
    long: Optional[Union[str, bool]] = ...,
    group: Optional[Group] = None,
    mutex: Optional[MutexGroup] = None,
    action: Optional[ActionType] = ...,
    nargs: Optional[NargsType] = ...,
    const: Optional[U] = None,
    default: Optional[U] = None,
    choices: Optional[Sequence[str]] = None,
    required: Optional[bool] = ...,
    help: Optional[str] = None,
    metavar: Optional[str] = None,
    deprecated: bool = False
) -> Any: ...

@overload
def arguments[T](cls: type[T], /) -> type[T]: ...

@overload
def arguments(
    *,
    prog: Optional[str] = None,
    usage: Optional[str] = None,
    description: Optional[str] = None,
    epilog: Optional[str] = None,
    parents: Optional[list[type]] = None,
    formatter_class=argparse.HelpFormatter,
    prefix_chars: str = "-",
    fromfile_prefix_chars: Optional[str] = None,
    conflict_handler: str = "error",
    add_help: bool = True,
    allow_abbrev: bool = True,
    exit_on_error: bool = True
) -> Callable[[type[T]], type[T]]: ...

@overload
def subcommand[T](cls: type[T], /) -> type[T]: ...

@overload
def subcommand[T](
    *,
    name: Optional[str] = ...,
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
    conflict_handler: str = ...,
    add_help: bool = ...,
    allow_abbrev: bool = ...,
    exit_on_error: bool = ...,
) -> Callable[[type[T]], type[T]]: ...

# TODO: Add overloads that return `Optional[Any]` based on the `required` and `default` parameters.
def subparser(
    title: Optional[str] = None,
    description: Optional[str] = None,
    prog: Optional[str] = None,
    parser_class: Optional[type] = None,
    action: Optional[ActionType] = None,
    required: bool = False,
    help: Optional[str] = None,
    metavar: Optional[str] = None
) -> Any: ...
