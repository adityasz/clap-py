import sys
from typing_extensions import dataclass_transform
from packaging.version import Version
from typing import Protocol, Optional, Union, Callable, Self, TypeVar, overload

from .core import create_parser

T = TypeVar('T')

_HELP_TEMPLATE = """\
{before-help}{name} {version}
{about}

{usage-heading} {usage}

{all-args}{after-help}
"""


# does not help since dataclass_transform adds its own return type :-(
class ClapArgs(Protocol):
    """Protocol for class types that have a parse_args class method."""
    @classmethod
    def parse_args(cls: type[Self], args: Optional[list[str]] = None) -> Self:
        """Parse command line arguments and return an instance of the class."""
        ...


class Parser:
    @classmethod
    def parse_args(cls: type[Self], args: Optional[list[str]] = None) -> Self:
        ...


@overload
def arguments(cls: type, /) -> type[ClapArgs]:
    ...

@overload
def arguments(
    *,
    name: Optional[str] = None,
    version: Optional[Version] = None,
    parent: Optional[type[ClapArgs]] = None,
    help_template: str = _HELP_TEMPLATE,
    after_help: str = "",
    max_term_width: int = 80,
    conflict_handler: str = "error",
    exit_on_error: bool = True
) -> Callable[[type], type[ClapArgs]]:
    ...

@dataclass_transform()
def arguments(
    cls: Optional[type] = None,
    /,
    *,
    name: Optional[str] = None,
    version: Optional[Version] = None,
    parent: Optional[type[ClapArgs]] = None,
    help_template: str = _HELP_TEMPLATE,
    after_help: str = "",
    max_term_width: int = 80,
    conflict_handler: str = "error",
    exit_on_error: bool = True
) -> Union[type[ClapArgs], Callable[[type], type[ClapArgs]]]:
    def wrap(cls: type) -> type[ClapArgs]:
        cls._help = ...  # figure out which subcommand's help to show
        cls._parser = create_parser(cls, conflict_handler, exit_on_error)

        @classmethod
        def parse_args(cls_inner, args: Optional[list[str]] = None):
            """Parse command line arguments and return an instance of the class."""
            if True:
                print("Parsed")
                return
            if "-h" in sys.argv or "--help" in sys.argv:
                cls_inner._help()
            parsed = cls_inner._parser.parse_args(args)
            return cls_inner(**vars(parsed))

        cls.parse_args = parse_args
        return cls

    if cls is None:
        return wrap

    return wrap(cls)


@dataclass_transform()
def subcommand(cls: type[T]) -> type[T]:
    ...

@dataclass_transform()
def group(cls: type[T]) -> type[T]:
    ...

@dataclass_transform()
def mutually_exclusive_group(cls: type[T]) -> type[T]:
    ...
