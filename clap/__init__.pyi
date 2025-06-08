import argparse
from collections.abc import Callable, Sequence
from typing import Any, Optional, TypeVar, Union, overload

from .api import Group, MutexGroup, Parser, group, mutex_group
from .core import (
    ArgAction,
    AutoLongFlag,
    AutoShortFlag,
    ColorChoice,
    NargsType,
    long,
    short,
)

__all__ = [
    "ArgAction",
    "ColorChoice",
    "Parser",
    "arg",
    "command",
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
    short_or_long: Optional[Union[AutoShortFlag, AutoLongFlag, str]] = None,
    long_: Optional[Union[AutoLongFlag, str]] = None,
    /,
    *,
    short: Optional[Union[str, bool]] = None,
    long: Optional[Union[str, bool]] = None,
    aliases: Optional[Sequence[str]] = None,
    group: Optional[Group] = None,
    mutex: Optional[MutexGroup] = None,
    action: Optional[Union[argparse.Action, ArgAction]] = None,
    num_args: Optional[NargsType] = None,
    default_missing_value: Optional[U] = None,
    default_value: Optional[U] = None,
    choices: Optional[Sequence[str]] = None,
    required: Optional[bool] = None,
    about: Optional[str] = None,
    long_about: Optional[str] = None,
    value_name: Optional[str] = None,
    deprecated: bool = False
) -> Any: ...

@overload
def command[T](cls: type[T], /) -> type[T]: ...

@overload
def command(
    *,
    name: Optional[str] = None,
    usage: Optional[str] = None,
    about: Optional[str] = None,
    long_about: Optional[str] = None,
    after_help: Optional[str] = None,
    subcommand_help_heading: str = "Commands",
    subcommand_value_name: str = "COMMAND",
    disable_version_flag: bool = False,
    disable_help_flag: bool = False,
    disable_help_subcommand: bool = False,
    parents: Optional[Sequence[type]] = None,
    prefix_chars: str = "-",
    fromfile_prefix_chars: Optional[str] = None,
    conflict_handler: str = "error",
    allow_abbrev: bool = True,
    exit_on_error: bool = True,
    heading_ansi_prefix: Optional[str] = None,
    argument_ansi_prefix: Optional[str] = None,
) -> Callable[[type[T]], type[T]]: ...

@overload
def subcommand[T](cls: type[T], /) -> type[T]: ...

@overload
def subcommand[T](
    *,
    name: Optional[str] = ...,
    aliases: Sequence[str] = ...,
    usage: Optional[str] = ...,
    about: Optional[str] = ...,
    long_about: Optional[str] = ...,
    after_help: Optional[str] = ...,
    subcommand_help_heading: Optional[str] = ...,
    subcommand_value_name: Optional[str] = ...,
    disable_help_flag: bool = False,
    disable_help_subcommand: bool = False,
    parents: Optional[Sequence[type]] = ...,
    prefix_chars: str = "-",
    fromfile_prefix_chars: Optional[str] = None,
    conflict_handler: str = ...,
    allow_abbrev: bool = ...,
    exit_on_error: bool = ...,
    deprecated: bool = False,
    heading_ansi_prefix: Optional[str] = ...,
    argument_ansi_prefix: Optional[str] = ...,
) -> Callable[[type[T]], type[T]]: ...
