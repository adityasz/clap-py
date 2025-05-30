import argparse
from typing_extensions import dataclass_transform
from typing import Protocol, Optional, Union, Callable, Self, TypeVar, overload

from .core import create_parser
from .stuff import _Action

T = TypeVar('T')

_HELP_TEMPLATE = """\
{before-help}{name} {version}
{about}

{usage-heading} {usage}

{all-args}{after-help}
"""


class ClapArgs(Protocol):
    """Protocol for class types that have a parse_args class method."""
    def __getattr__(self, *args):
        ...
    @classmethod
    def parse_args(cls: type[Self], args: Optional[list[str]] = None) -> Self:
        """Parse command line arguments and return an instance of the class."""
        ...


class Parser:
    @classmethod
    def parse_args(cls: type[Self], args: Optional[list[str]] = None) -> Self:
        ...


@overload
def arguments(cls: type[T], /) -> type[T]:
    ...

@overload
def arguments(
    *,
    name: Optional[str] = None,
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
) -> Callable[[type[T]], type[T]]:
    ...

def arguments(
    cls: Optional[type[T]] = None,
    /,
    *,
    name: Optional[str] = None,
    usage: Optional[str] = None,
    description: Optional[str] = None,
    epilog: Optional[str] = None,
    parents: Optional[list[type[ClapArgs]]] = None,
    formatter_class = argparse.HelpFormatter,
    prefix_chars: str = "-",
    fromfile_prefix_chars: Optional[str] = None,
    conflict_handler: str = "error",
    add_help: bool = True,
    allow_abbrev: bool = True,
    exit_on_error: bool = True
) -> Union[type[T], Callable[[type[T]], type[T]]]:
    def wrap(cls: type[T]) -> type[T]:
        setattr(cls, "_parser", create_parser(cls, conflict_handler, exit_on_error))

        @classmethod
        def parse_args(cls_inner, args: Optional[list[str]] = None):
            """Parse command line arguments and return an instance of the class."""
            parsed = cls_inner._parser.parse_args(args)
            return cls_inner(**vars(parsed))

        setattr(cls, "parse_args", parse_args)
        return cls

    if cls is None:
        return wrap

    return wrap(cls)


# @dataclass_transform()
def subcommand(
    cls: type[T],
    /,
    *,
    title: Optional[str] = "Commands",
    description: Optional[str] = None,
    prog: Optional[str] = None,
    parser_class: Optional[type] = None,
    action: Optional[_Action] = None,
    required: bool = False,
    help: Optional[str] = None,
    metavar: Optional[str] = None
) -> type[T]:
    ...
