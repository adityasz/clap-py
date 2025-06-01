import argparse
from typing import Callable, Optional, Self, Sequence, TypeVar, Union, cast, overload

from core import (
    COMMAND_ATTR,
    COMMAND_KWARGS,
    PARSER_ATTR,
    SUBCOMMAND_ATTR,
    SUBCOMMAND_KWARGS,
    SUBCOMMAND_TITLE,
    ArgparseArgumentInfo,
    Argument,
    Group,
    MutexGroup,
    SubparserInfo,
    _Action,
    _Long,
    _Nargs,
    _Short,
    create_parser,
)

T = TypeVar('T')
U = TypeVar('U')


class Parser:
    @classmethod
    def parse_args(cls: type[Self], args: Optional[list[str]] = None) -> Self:
        ...


@overload
def arguments(cls: type[T], /) -> type[T]: ...


@overload
def arguments(
    *,
    prog: Optional[str] = None,
    usage: Optional[str] = None,
    description: Optional[str] = None,
    epilog: Optional[str] = None,
    parents: Optional[list[type]] = None,
    formatter_class = argparse.HelpFormatter,
    prefix_chars: str = "-",
    fromfile_prefix_chars: Optional[str] = None,
    conflict_handler: str = "error",
    add_help: bool = True,
    allow_abbrev: bool = True,
    exit_on_error: bool = True
) -> Callable[[type[T]], type[T]]: ...


def arguments(
    cls: Optional[type[T]] = None,
    /,
    **kwargs
) -> Union[type[T], Callable[[type[T]], type[T]]]:
    def wrap(cls: type[T]) -> type[T]:
        setattr(cls, COMMAND_ATTR, True)
        setattr(cls, COMMAND_KWARGS, kwargs)
        setattr(cls, PARSER_ATTR, create_parser(cls, **kwargs))

        @classmethod
        def parse_args(cls: type, args: Optional[list[str]] = None):
            """Parse command-line arguments and return an instance of the class."""
            parser = getattr(cls, PARSER_ATTR)
            parsed = parser.parse_args(args)
            print("TODO: setattr...")
            return cls

        setattr(cls, "parse_args", parse_args)
        return cls

    if cls is None:
        return wrap
    return wrap(cls)


def subcommand(
    cls: Optional[type[T]] = None,
    /,
    **kwargs
) -> Union[type[T], Callable[[type[T]], type[T]]]:
    def wrap(cls: type[T]) -> type[T]:
        setattr(cls, SUBCOMMAND_ATTR, True)
        kwargs.setdefault("title", SUBCOMMAND_TITLE)
        setattr(cls, SUBCOMMAND_KWARGS, kwargs)
        return cls

    if cls is None:
        return wrap
    return wrap(cls)


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
) -> Argument:
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

    return Argument(
        ArgparseArgumentInfo(
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
        ),
        group=group,
        mutex=mutex
    )


def subparser(
    title: Optional[str] = None,
    description: Optional[str] = None,
    prog: Optional[str] = None,
    parser_class: Optional[type] = None,
    action: Optional[_Action] = None,
    required: bool = False,
    help: Optional[str] = None,
    metavar: Optional[str] = None
) -> SubparserInfo:
    return SubparserInfo(
        title=title,
        description=description,
        prog=prog,
        parser_class=parser_class,
        action=action,
        required=required,
        help=help,
        metavar=metavar
    )
