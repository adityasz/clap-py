from typing import Any, Literal, Optional, Sequence, TypeVar, Union, overload

from .decorator import ClapArgs, arguments, Parser
from .help import ColorChoice

__all__ = [
    "arguments",
    "ClapArgs",
    "Parser",
    "ColorChoice",
    "flag",
    "option",
    "positional",
]

T = TypeVar('T')
U = TypeVar('U')


@overload
def flag(
    short: Optional[str] = None,
    /,
    *,
    long: Optional[str] = None,
    count: None = None
) -> bool:
    """Create a command-line flag."""
    ...


@overload
def flag(
    short: Optional[str] = None,
    /,
    *,
    long: Optional[str] = None,
    count: bool
) -> int:
    """Create a command-line flag.

    Arguments:
        count: Whether to count the number of occurrences of this flag.
    """


@overload
def option(
    type: type[T],
    short: Optional[str] = None,
    /,
    *,
    long: Optional[str] = None,
    action: Optional[
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
            "version",
        ]
    ] = "store",
    nargs: Optional[Union[Literal["?", "+", "*"], int]] = ...,
    const: Optional[U] = None,
    default: Optional[U] = None,
    choices: Optional[Sequence[str]] = None,
    required: None = None,
    metavar: Optional[str] = None,
    deprecated: bool = False
) -> Optional[T]: ...


@overload
def option(
    short: Optional[str] = None,
    /,
    *,
    long: Optional[str] = None,
    action: Optional[
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
            "version",
        ]
    ] = "store",
    nargs: Optional[Union[Literal["?", "+", "*"], int]] = ...,
    const: None = None,
    default: U,
    choices: Optional[Sequence[str]] = None,
    required: None = None,
    metavar: Optional[str] = None,
    deprecated: bool = False
) -> Optional[U]: ...


@overload
def option(
    short: Optional[str] = None,
    /,
    *,
    long: Optional[str] = None,
    action: Optional[
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
            "version",
        ]
    ] = "store",
    nargs: Optional[Union[Literal["?", "+", "*"], int]] = ...,
    const: U,
    default: None = None,
    choices: Optional[Sequence[str]] = None,
    required: None = None,
    metavar: Optional[str] = None,
    deprecated: bool = False
) -> Optional[U]: ...

@overload
def option(
    type: type[T],
    short: Optional[str] = None,
    /,
    *,
    long: Optional[str] = None,
    action: Optional[
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
            "version",
        ]
    ] = "store",
    nargs: Optional[Union[Literal["?", "+", "*"], int]] = ...,
    const: Optional[U] = None,
    default: Optional[U] = None,
    choices: Optional[Sequence[str]] = None,
    required: bool = ...,
    metavar: Optional[str] = None,
    deprecated: bool = False
) -> T: ...


@overload
def option(
    short: Optional[str] = None,
    /,
    *,
    long: Optional[str] = None,
    action: Optional[
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
            "version",
        ]
    ] = "store",
    nargs: Optional[Union[Literal["?", "+", "*"], int]] = ...,
    const: None = None,
    default: U,
    choices: Optional[Sequence[str]] = None,
    required: bool = ...,
    metavar: Optional[str] = None,
    deprecated: bool = False
) -> U: ...


@overload
def option(
    short: Optional[str] = None,
    /,
    *,
    long: Optional[str] = None,
    action: Optional[
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
            "version",
        ]
    ] = "store",
    nargs: Optional[Union[Literal["?", "+", "*"], int]] = ...,
    const: U,
    default: None = None,
    choices: Optional[Sequence[str]] = None,
    required: bool = ...,
    metavar: Optional[str] = None,
    deprecated: bool = False
) -> U: ...

@overload
def option(
    short: Optional[str] = None,
    /,
    *,
    long: Optional[str] = None,
    action: Optional[
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
            "version",
        ]
    ] = "store",
    nargs: Optional[Union[Literal["?", "+", "*"], int]] = ...,
    const: None = None,
    default: None = None,
    choices: Optional[Sequence[str]] = None,
    required: Literal[True],
    metavar: Optional[str] = None,
    deprecated: bool = False
) -> Any: ...
    # """
    # This overload lets you do this:
    # ```python
    # foo: int = option(required=True)
    # ```
    # But the type checker wouldn't warn you if you do this:
    # ```python
    # foo: int = option("-f")  # should be Optional[int]
    # ```
    # """
    # ...
