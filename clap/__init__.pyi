import argparse
from collections.abc import Callable, Sequence
from typing import Any, Optional, TypeVar, Union, overload

from .api import Parser, group, mutex_group
from .models import (
    ArgAction,
    AutoFlag,
    Group,
    MutexGroup,
    NargsType,
    long,
    short,
)
from .styling import AnsiColor, ColorChoice, Styles

__all__ = [
    "AnsiColor",
    "ArgAction",
    "ColorChoice",
    "Styles",
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

# TODO: Add overloads that return `Optional[Any]` based on the `required`,
# `default`, and `num_args`.
def arg(
    short_or_long: Optional[AutoFlag] = None,
    long_or_short: Optional[AutoFlag] = None,
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
    name: str = ...,
    usage: Optional[str] = ...,
    about: Optional[str] = None,
    long_about: Optional[str] = None,
    before_help: Optional[str] = None,
    after_help: Optional[str] = None,
    subcommand_help_heading: str = ...,
    subcommand_value_name: str = ...,
    disable_version_flag: bool = False,
    disable_help_flag: bool = False,
    disable_help_subcommand: bool = False,
    prefix_chars: str = "-",
    fromfile_prefix_chars: Optional[str] = None,
    conflict_handler: str = ...,
    allow_abbrev: bool = True,
    exit_on_error: bool = True,
    heading_ansi_prefix: Optional[str] = ...,
    argument_ansi_prefix: Optional[str] = ...,
) -> Callable[[type[T]], type[T]]: ...

@overload
def subcommand[T](cls: type[T], /) -> type[T]: ...

@overload
def subcommand[T](
    *,
    name: str = ...,
    aliases: Sequence[str] = ...,
    usage: Optional[str] = ...,
    about: Optional[str] = ...,
    long_about: Optional[str] = ...,
    after_help: Optional[str] = ...,
    subcommand_help_heading: Optional[str] = ...,
    subcommand_value_name: Optional[str] = ...,
    disable_help_flag: bool = False,
    disable_help_subcommand: bool = False,
    prefix_chars: str = "-",
    fromfile_prefix_chars: Optional[str] = None,
    conflict_handler: str = ...,
    allow_abbrev: bool = ...,
    exit_on_error: bool = ...,
    deprecated: bool = False,
    heading_ansi_prefix: Optional[str] = ...,
    argument_ansi_prefix: Optional[str] = ...,
) -> Callable[[type[T]], type[T]]: ...
