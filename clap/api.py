from collections.abc import Callable, Sequence
from typing import (
    Optional,
    Self,
    TypeVar,
    Union,
    cast,
)

from .core import (
    _COMMAND_MARKER,
    _PARSER,
    _PARSER_CONFIG,
    _SUBCOMMAND_MARKER,
    ActionType,
    ArgparseConfig,
    Argument,
    Group,
    MutexGroup,
    NargsType,
    SubparserInfo,
    _LongFlag,
    _ShortFlag,
    apply_parsed_arguments,
    create_parser,
    to_kebab_case,
)

T = TypeVar('T')
U = TypeVar('U')


class Parser:
    @classmethod
    def parse_args(cls: type[Self], args: Optional[Sequence[str]] = None) -> Self:
        ...


def arguments[T](
    cls: Optional[type[T]] = None,
    /,
    **kwargs
) -> Union[type[T], Callable[[type[T]], type[T]]]:
    """Configure a class to parse command-line arguments.

    Args:
        cls: The class to decorate. When used without parentheses, this is
            the class being decorated.
        prog: The name of the program. By default, `ArgumentParser` calculates
            the name of the program from `sys.argv[0]`.
        usage: The string describing the program usage. The default is
            generated from arguments added to parser.
        description: Text to display before the argument help.
        epilog: Text to display after the argument help.
        parents: A list of `ArgumentParser` objects whose arguments should
            also be included.
        formatter_class: A class for customizing the help output.
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
        setattr(cls, _COMMAND_MARKER, True)
        kwargs.setdefault("description", cls.__doc__)
        setattr(cls, _PARSER_CONFIG, kwargs)
        setattr(cls, _PARSER, create_parser(cls, **kwargs))

        @classmethod
        def parse_args(cls: type, args: Optional[list[str]] = None) -> T:
            """Parse command-line arguments and return an instance of the class."""
            parser = getattr(cls, _PARSER)
            parsed_args = parser.parse_args(args)
            obj = cls()
            apply_parsed_arguments(dict(parsed_args._get_kwargs()), obj)
            return obj

        cls.parse_args = parse_args
        return cls

    if cls is None:
        return wrap
    return wrap(cls)


def subcommand[T](
    cls: Optional[type[T]] = None,
    /,
    **kwargs
) -> Union[type[T], Callable[[type[T]], type[T]]]:
    """Configure a class as a subcommand parser.

    Args:
        cls: The class to decorate. When used without parentheses, this is
            the class being decorated.
        name: The name of the subcommand. If not provided, uses the class name.
        deprecated: Whether this subcommand is deprecated and should not be used.
        help: A brief description of what the subcommand does.
        aliases: A sequence of alternative names for the subcommand.
        prog: The name of the program. By default, `ArgumentParser` calculates
            the name of the program from `sys.argv[0]`.
        usage: The string describing the program usage. The default is
            generated from arguments added to parser.
        description: Text to display before the argument help.
        epilog: Text to display after the argument help.
        parents: A sequence of `ArgumentParser` objects whose arguments should
            also be included.
        formatter_class: A class for customizing the help output.
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
        setattr(cls, _SUBCOMMAND_MARKER, True)
        kwargs.setdefault("name", to_kebab_case(cls.__name__))
        kwargs.setdefault("help", cls.__doc__)
        setattr(cls, _PARSER_CONFIG, kwargs)
        return cls

    if cls is None:
        return wrap
    return wrap(cls)


def arg[T, U](
    short_or_long: Optional[Union[_ShortFlag, _LongFlag, str]] = None,
    long_: Optional[Union[_LongFlag, str]] = None,
    /,
    *,
    short: Optional[Union[str, bool]] = None,
    long: Optional[Union[str, bool]] = None,
    group: Optional[Group] = None,
    mutex: Optional[MutexGroup] = None,
    action: Optional[ActionType] = None,
    nargs: Optional[NargsType] = None,
    const: Optional[U] = None,
    default: Optional[U] = None,
    choices: Optional[Sequence[str]] = None,
    required: Optional[bool] = None,
    help: Optional[str] = None,
    metavar: Optional[str] = None,
    deprecated: bool = False
) -> Argument:
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
        nargs: The number of command-line arguments that should be consumed.
        const: The constant value required by some action and nargs selections.
        default: The default value for the argument if not provided.
        choices: A sequence of valid choices for the argument.
        required: Whether the argument is required or optional.
        help: A brief description of what the argument does.
        metavar: The name for the argument in usage messages.
        deprecated: Whether this argument is deprecated and should not be used.
    """
    short_name = None
    long_name = None

    if isinstance(short_or_long, _LongFlag):
        short_name = None
        long_name = cast(_LongFlag, short_or_long)
    elif (
        isinstance(short_or_long, str) and (
            short_or_long.startswith("--")
            or (not short_or_long.startswith("-") and len(short_or_long) > 1)
        )
    ):
        short_name = None
        long_name = cast(str, short_or_long)
    else:
        short_name = cast(Optional[Union[_ShortFlag, str]], short_or_long)
        long_name = long_

    if short is not None:
        if isinstance(short, str):
            short_name = short
        elif short is True:
            short_name = _ShortFlag()

    if long is not None:
        if isinstance(long, str):
            long_name = long
        elif long is True:
            long_name = _LongFlag()

    return Argument(
        ArgparseConfig(
            action=action,
            nargs=nargs,
            const=const,
            default=default,
            choices=choices,
            required=required,
            help=help,
            metavar=metavar,
            deprecated=deprecated
        ),
        short=short_name,
        long=long_name,
        group=group,
        mutex=mutex
    )


def subparser(
    title: Optional[str] = None,
    description: Optional[str] = None,
    prog: Optional[str] = None,
    parser_class: Optional[type] = None,
    action: Optional[ActionType] = None,
    required: bool = False,
    help: Optional[str] = None,
    metavar: Optional[str] = None
) -> SubparserInfo:
    """Create subparser configuration for command-line sub-commands.

    Args:
        title: Title for the sub-parser group in help output. By default
            "subcommands" if description is provided, otherwise uses title
            for positional arguments.
        description: Description for the sub-parser group in help output.
        prog: Usage information that will be displayed with sub-command help.
            By default the name of the program and any positional arguments
            before the subparser argument.
        parser_class: Class which will be used to create sub-parser instances.
            By default the class of the current parser.
        action: The basic type of action to be taken when this argument is
            encountered at the command line.
        required: Whether a subcommand must be provided.
        help: Help for sub-parser group in help output.
        metavar: String presenting available subcommands in help. By default
            it presents subcommands in form `{cmd1, cmd2, ...}`.
    """
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


def group(
    title: Optional[str] = None,
    description: Optional[str] = None,
    *,
    prefix_chars: str = "-",
    conflict_handler: str = "error"
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
        prefix_chars=prefix_chars,
        conflict_handler=conflict_handler
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
