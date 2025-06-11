import os
import sys
from collections.abc import Callable, Sequence
from typing import (
    Optional,
    Self,
    TypeVar,
    Union,
)

from clap.styling import Styles

from .help import ColorChoice
from .models import Arg, AutoFlag, Command, Group, MutexGroup
from .parser import (
    _COMMAND_DATA,
    _COMMAND_MARKER,
    _PARSER,
    _SUBCOMMAND_DEFAULTS,
    _SUBCOMMAND_MARKER,
    apply_parsed_args,
    create_parser,
    get_about_from_docstring,
    to_kebab_case,
)

U = TypeVar('U')


class Parser:
    @classmethod
    def parse_args(cls: type[Self], args: Optional[Sequence[str]] = None) -> Self:
        ...


def command[T](
    cls: Optional[type[T]] = None,
    /,
    *,
    name: str = os.path.basename(sys.argv[0]),
    about: Optional[str] = None,
    long_about: Optional[str] = None,
    color: ColorChoice = ColorChoice.Auto,
    help_style: Optional[Styles] = None,
    help_template: Optional[str] = None,
    **kwargs,
) -> Union[type[T], Callable[[type[T]], type[T]]]:
    """Configure a class to parse command-line arguments.

    Args:
        cls: The class to decorate. When used without parentheses, this is
            the class being decorated.
        name: The name of the program. Default: `sys.argv[0]`.
        usage: The string describing the program usage. The default is
            generated from arguments added to parser.
        about: Text to display before the argument help.
        after_help: Text to display after the argument help.
        prefix_chars: The set of characters that prefix optional arguments.
        fromfile_prefix_chars: The set of characters that prefix files from
            which additional arguments should be read.
        conflict_handler: The strategy for resolving conflicting optionals.
        allow_abbrev: Whether to allow long options to be abbreviated if the
            abbreviation is unambiguous.
        exit_on_error: Whether `ArgumentParser` exits with error info when
            an error occurs.
    """
    def wrap(cls: type[T]) -> type[T]:
        nonlocal about, long_about, name
        setattr(cls, _COMMAND_MARKER, True)
        if name is None:
            name = os.path.basename(sys.argv[0])
        kwargs["name"] = name
        if cls.__doc__ is not None:
            docstring = cls.__doc__.strip()
            if about is None:
                kwargs["about"] = get_about_from_docstring(docstring)
            if long_about is None:
                kwargs["long_about"] = docstring
        command = Command(**kwargs)
        setattr(cls, _COMMAND_DATA, command)
        setattr(cls, _PARSER, create_parser(cls, color, help_style, help_template))

        # delete default values of fields so that `@dataclass` does not complain
        # about mutable defaults (`Arg`)
        for name, _ in cls.__annotations__.items():
            if hasattr(cls, name):
                delattr(cls, name)

        @classmethod
        def parse_args(cls: type, args: Optional[list[str]] = None) -> T:
            """Parse command-line arguments and return an instance of the class."""
            parser = getattr(cls, _PARSER)
            parsed_args = parser.parse_args(args)
            obj = object.__new__(cls)
            apply_parsed_args(dict(parsed_args._get_kwargs()), obj)
            return obj

        cls.parse_args = parse_args
        return cls

    if cls is None:
        return wrap
    return wrap(cls)


def subcommand[T](
    cls: Optional[type[T]] = None,
    /,
    *,
    name: Optional[str] = None,
    about: Optional[str] = None,
    long_about: Optional[str] = None,
    **kwargs,
) -> Union[type[T], Callable[[type[T]], type[T]]]:
    """Configure a class as a subcommand parser.

    Args:
        cls: The class to decorate. When used without parentheses, this is
            the class being decorated.
        name: The name of the subcommand. If not provided, uses the class name.
        deprecated: Whether this subcommand is deprecated and should not be used.
        about: A brief description of what the subcommand does.
        aliases: A sequence of alternative names for the subcommand.
        usage: The string describing the program usage. The default is
            generated from arguments added to parser.
        prefix_chars: The set of characters that prefix optional arguments.
        fromfile_prefix_chars: The set of characters that prefix files from
            which additional arguments should be read.
        conflict_handler: The strategy for resolving conflicting optionals.
        add_help: Whether to add a `-h/--help` option to the parser.
        allow_abbrev: Whether to allow long options to be abbreviated if the
            abbreviation is unambiguous.
        exit_on_error: Whether `ArgumentParser` exits with error info when
            an error occurs.
    """
    def wrap(cls: type[T]) -> type[T]:
        nonlocal about, long_about, name
        setattr(cls, _SUBCOMMAND_MARKER, True)
        if name is None:
            name = to_kebab_case(cls.__name__)
        kwargs["name"] = name
        if cls.__doc__ is not None:
            docstring = cls.__doc__.strip()
            if about is None:
                kwargs["about"] = get_about_from_docstring(docstring)
            if long_about is None:
                kwargs["long_about"] = docstring
        command = Command(**kwargs)
        setattr(cls, _COMMAND_DATA, command)

        # delete default values of fields so that `@dataclass` does not complain
        # about mutable defaults (`Arg`)
        attrs = {}
        for name, _ in cls.__annotations__.items():
            if attr := getattr(cls, name, None):
                attrs[name] = attr
                delattr(cls, name)
        setattr(cls, _SUBCOMMAND_DEFAULTS, attrs)

        return cls

    if cls is None:
        return wrap
    return wrap(cls)


def arg[U](
    short_or_long: Optional[AutoFlag] = None,
    long_or_short: Optional[AutoFlag] = None,
    /,
    *,
    short: Optional[Union[str, bool]] = None,
    long: Optional[Union[str, bool]] = None,
    **kwargs,
) -> Arg:
    """Create a command-line argument.

    Args:
        short_or_long: The short or long flag for the argument. If a single
            character or starts with `-`, it's treated as a short flag. If it
            starts with `--` or is longer than one character without `-`, it's
            treated as a long flag.
        long_: The long flag for the argument when `short_or_long` is used as
            the short flag.
        short: The short flag for the argument.
        long: The long flag for the argument.
        group: The group for the argument.
        mutex: The mutually exclusive group for the argument.
        action: The action to be taken when this argument is encountered.
        num_args: The number of command-line arguments that should be consumed.
        default_missing_value: The constant value required by some action and num_args selections.
        default_value: The default value for the argument if not provided.
        choices: A sequence of valid choices for the argument.
        required: Whether the argument is required or optional.
        help: A brief description of what the argument does.
        value_name: The name for the argument in usage messages.
        deprecated: Whether this argument is deprecated and should not be used.
    """
    short_name = None
    long_name = None

    match short_or_long:
        case AutoFlag.Short: short_name = AutoFlag.Short
        case AutoFlag.Long: long_name = AutoFlag.Long

    match long_or_short:
        case AutoFlag.Short: short_name = AutoFlag.Short
        case AutoFlag.Long: long_name = AutoFlag.Long

    if short is not None:
        if isinstance(short, str):
            if len(short) == 0:
                raise ValueError
            short_name = short
        elif short is True:
            short_name = AutoFlag.Short

    if long is not None:
        if isinstance(long, str):
            if len(long) == 0:
                raise ValueError
            long_name = long
        elif long is True:
            long_name = AutoFlag.Long

    kwargs["short"] = short_name
    kwargs["long"] = long_name

    return Arg(**kwargs)


def group(
    title: Optional[str] = None,
    description: Optional[str] = None,
    **kwargs,
) -> Group:
    """Create an argument group for organizing related arguments.

    Args:
        title: Title for the argument group in help output. If provided without
            description, this will be used as the group header.
        description: Description for the argument group in help output. This
            appears below the title and provides additional context about the
            group's purpose.
        prefix_chars: The set of characters that prefix optional arguments
            within this group.
        conflict_handler: The strategy for resolving conflicting optionals
            within this group.

    Returns:
        A `Group` object that can be used to organize related arguments.
    """
    assert isinstance(title, str)
    return Group(
        title=title,
        description=description,
        **kwargs
    )


def mutex_group(
    parent_group: Optional[Group] = None,
    required: bool = False,
) -> MutexGroup:
    """Create a mutually exclusive group of arguments.

    `argparse` will ensure that only one of the arguments in the mutually
    exclusive group is present on the command line. This is useful for
    options that conflict with each other, such as `--verbose` and `--quiet`.

    Args:
        parent_group: The parent argument group to add this mutually exclusive
            group to. If `None`, the group will be added directly to the parser.
        required: Whether at least one of the mutually exclusive arguments is
            required.

    Returns:
        A `MutexGroup` object for creating mutually exclusive arguments.
    """
    return MutexGroup(parent=parent_group, required=required)
