from collections.abc import Callable, Sequence
from typing import Any, Optional, TypeVar, Union, dataclass_transform, overload

from .api import Parser, mutex_group
from .core import (
    ArgAction,
    AutoFlag,
    Group,
    MutexGroup,
    NargsType,
    long,
    short,
)
from .help import HelpTemplate
from .styling import AnsiColor, ColorChoice, Style, Styles

__all__ = [
    "AnsiColor",
    "ArgAction",
    "ColorChoice",
    "Group",
    "MutexGroup",
    "HelpTemplate",
    "Style",
    "Styles",
    "Parser",
    "arg",
    "command",
    "mutex_group",
    "subcommand",
    "short",
    "long"
]

T = TypeVar('T')
U = TypeVar('U')

# TODO: Add overloads that return `Optional[Any]` based on the `required`,
# `default`, and `num_args`.
def arg[U](
    short_or_long: Optional[AutoFlag] = None,
    long_or_short: Optional[AutoFlag] = None,
    /,
    *,
    short: Optional[Union[str, bool]] = None,
    long: Optional[Union[str, bool]] = None,
    aliases: Optional[Sequence[str]] = None,
    group: Optional[Group] = None,
    mutex: Optional[MutexGroup] = None,
    action: Optional[Union[type, ArgAction]] = None,
    num_args: Optional[NargsType] = None,
    default_missing_value: Optional[U] = None,
    default_value: Optional[U] = None,
    choices: Optional[Sequence[str]] = None,
    required: Optional[bool] = ...,
    help: Optional[str] = ...,
    long_help: Optional[str] = ...,
    value_name: Optional[str] = None,
    deprecated: bool = False
) -> Any: ...

@overload
@dataclass_transform()
def command[T](cls: type[T], /) -> type[T]: ...

@overload
@dataclass_transform()
def command(
    *,
    name: str = ...,
    version: Optional[str] = None,
    long_version: Optional[str] = None,
    usage: Optional[str] = ...,
    about: Optional[str] = ...,
    long_about: Optional[str] = ...,
    after_help: Optional[str] = None,
    after_long_help: Optional[str] = ...,
    before_help: Optional[str] = None,
    before_long_help: Optional[str] = ...,
    subcommand_help_heading: str = ...,
    subcommand_value_name: str = ...,
    color: ColorChoice = ColorChoice.Auto,
    help_styles: Optional[Styles] = ...,
    help_template: Optional[str] = ...,
    max_term_width: Optional[int] = ...,
    propagate_version: bool = False,
    disable_version_flag: bool = False,
    disable_help_flag: bool = False,
    prefix_chars: str = "-",
    fromfile_prefix_chars: Optional[str] = None,
    conflict_handler: str = ...,
    allow_abbrev: bool = True,
    exit_on_error: bool = True,
) -> Callable[[type[T]], type[T]]: ...

@overload
@dataclass_transform()
def subcommand[T](cls: type[T], /) -> type[T]: ...

@overload
@dataclass_transform()
def subcommand[T](
    *,
    name: str = ...,
    version: Optional[str] = None,
    long_version: Optional[str] = None,
    aliases: Sequence[str] = ...,
    usage: Optional[str] = ...,
    about: Optional[str] = ...,
    long_about: Optional[str] = ...,
    before_help: Optional[str] = None,
    before_long_help: Optional[str] = ...,
    after_help: Optional[str] = None,
    after_long_help: Optional[str] = ...,
    subcommand_help_heading: Optional[str] = ...,
    subcommand_value_name: Optional[str] = ...,
    color: Optional[ColorChoice] = ...,
    help_styles: Optional[Styles] = ...,
    help_template: Optional[str] = ...,
    max_term_width: Optional[int] = ...,
    propagate_version: bool = False,
    disable_version_flag: bool = False,
    disable_help_flag: bool = False,
    prefix_chars: str = "-",
    fromfile_prefix_chars: Optional[str] = None,
    conflict_handler: str = ...,
    allow_abbrev: bool = ...,
    exit_on_error: bool = ...,
    deprecated: bool = False,
) -> Callable[[type[T]], type[T]]: ...

def group(
    title: str,
    about: Optional[str] = ...,
    long_about: Optional[str] = ...,
    conflict_handler: Optional[str] = ...
) -> Group: ...
