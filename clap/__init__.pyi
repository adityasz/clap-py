from typing import Any, Optional, Sequence, TypeVar, Union

from .decorator import Parser, arguments, subcommand
from .help import ColorChoice
from .stuff import Group, MutexGroup, _Action, _Long, _Nargs, _Short

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
