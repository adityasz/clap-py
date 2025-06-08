from collections.abc import Callable, Sequence
from typing import (
    Optional,
    Self,
    TypeVar,
    Union,
    cast,
)

from .core import (
    _COMMAND_DATA,
    _COMMAND_MARKER,
    _PARSER,
    _SUBCOMMAND_MARKER,
    Arg,
    ArgAction,
    ArgConfig,
    AutoLongFlag,
    AutoShortFlag,
    Command,
    Group,
    MutexGroup,
    NargsType,
    ParserConfig,
    apply_parsed_arguments,
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
    name: Optional[str] = None,
    version: Optional[str] = None,
    usage: Optional[str] = None,
    about: Optional[str] = None,
    long_about: Optional[str] = None,
    after_help: Optional[str] = None,
    subcommand_help_heading: str = "Commands",
    subcommand_value_name: str = "COMMAND",
    disable_version_flag: bool = False,
    disable_help_flag: bool = False,
    disable_help_subcommand: bool = False,
    parents: Optional[list[type]] = None,
    prefix_chars: str = "-",
    fromfile_prefix_chars: Optional[str] = None,
    conflict_handler: str = "error",
    allow_abbrev: bool = True,
    exit_on_error: bool = True,
    heading_ansi_prefix: Optional[str] = None,
    argument_ansi_prefix: Optional[str] = None,
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
        parents: A list of `ArgumentParser` objects whose arguments should
            also be included.
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
            name = to_kebab_case(cls.__name__)
        if cls.__doc__ is not None:
            docstring = cls.__doc__.strip()
            if about is None:
                about = get_about_from_docstring(docstring)
            if long_about is None:
                long_about = docstring
        command = Command(
            ParserConfig(
                prog=name,
                usage=usage,
                prefix_chars=prefix_chars,
                fromfile_prefix_chars=fromfile_prefix_chars,
                conflict_handler=conflict_handler,
                allow_abbrev=allow_abbrev,
                exit_on_error=exit_on_error,
            ),
            name=name,
            version=version,
            about=about,
            long_about=long_about,
            after_help=after_help,
            subcommand_help_heading=subcommand_help_heading,
            subcommand_value_name=subcommand_value_name,
            disable_version_flag=disable_version_flag,
            disable_help_flag=disable_help_flag,
            disable_help_subcommand=disable_help_subcommand,
            heading_ansi_prefix=heading_ansi_prefix,
            argument_ansi_prefix=argument_ansi_prefix
        )
        setattr(cls, _COMMAND_DATA, command)
        setattr(cls, _PARSER, create_parser(cls))

        @classmethod
        def parse_args(cls: type, args: Optional[list[str]] = None) -> T:
            """Parse command-line arguments and return an instance of the class."""
            parser = getattr(cls, _PARSER)
            parsed_args = parser.parse_args(args)
            obj = object.__new__(cls)
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
    *,
    name: Optional[str] = None,
    aliases: Sequence[str] = [],
    usage: Optional[str] = None,
    about: Optional[str] = None,
    long_about: Optional[str] = None,
    after_help: Optional[str] = None,
    subcommand_help_heading: Optional[str] = None,
    subcommand_value_name: Optional[str] = None,
    disable_help_flag: bool = False,
    disable_help_subcommand: bool = False,
    parents: Optional[Sequence[type]] = None,
    prefix_chars: str = "-",
    fromfile_prefix_chars: Optional[str] = None,
    conflict_handler: str = "error",
    allow_abbrev: bool = True,
    exit_on_error: bool = True,
    deprecated: bool = False,
    heading_ansi_prefix: Optional[str] = None,
    argument_ansi_prefix: Optional[str] = None,
) -> Union[type[T], Callable[[type[T]], type[T]]]:
    """Configure a class as a subcommand parser.

    Args:
        cls: The class to decorate. When used without parentheses, this is
            the class being decorated.
        name: The name of the subcommand. If not provided, uses the class name.
        deprecated: Whether this subcommand is deprecated and should not be used.
        help: A brief description of what the subcommand does.
        aliases: A sequence of alternative names for the subcommand.
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
        nonlocal about, long_about, name
        setattr(cls, _SUBCOMMAND_MARKER, True)
        if name is None:
            name = to_kebab_case(cls.__name__)
        if cls.__doc__ is not None:
            docstring = cls.__doc__.strip()
            if about is None:
                about = get_about_from_docstring(docstring)
            if long_about is None:
                long_about = docstring
        command = Command(
            ParserConfig(
                name=name,
                usage=usage,
                aliases=aliases,
                deprecated=deprecated,
                prefix_chars=prefix_chars,
                fromfile_prefix_chars=fromfile_prefix_chars,
                conflict_handler=conflict_handler,
                allow_abbrev=allow_abbrev,
                exit_on_error=exit_on_error,
            ),
            about=about,
            long_about=long_about,
            after_help=after_help,
            subcommand_help_heading=subcommand_help_heading,
            subcommand_value_name=subcommand_value_name,
            disable_help_flag=disable_help_flag,
            disable_help_subcommand=disable_help_subcommand,
            heading_ansi_prefix=heading_ansi_prefix,
            argument_ansi_prefix=argument_ansi_prefix
        )
        setattr(cls, _COMMAND_DATA, command)
        return cls

    if cls is None:
        return wrap
    return wrap(cls)


def arg[U](
    short_or_long: Optional[Union[AutoShortFlag, AutoLongFlag, str]] = None,
    long_: Optional[Union[AutoLongFlag, str]] = None,
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
    required: Optional[bool] = None,
    about: Optional[str] = None,
    long_about: Optional[str] = None,
    value_name: Optional[str] = None,
    deprecated: bool = False
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

    if isinstance(short_or_long, AutoLongFlag):
        short_name = None
        long_name = cast(AutoLongFlag, short_or_long)
    elif (
        isinstance(short_or_long, str) and (
            short_or_long.startswith("--")
            or (not short_or_long.startswith("-") and len(short_or_long) > 1)
        )
    ):
        short_name = None
        long_name = cast(str, short_or_long)
    else:
        short_name = cast(Optional[Union[AutoShortFlag, str]], short_or_long)
        long_name = long_

    if short is not None:
        if isinstance(short, str):
            short_name = short
        elif short is True:
            short_name = AutoShortFlag()

    if long is not None:
        if isinstance(long, str):
            long_name = long
        elif long is True:
            long_name = AutoLongFlag()

    return Arg(
        ArgConfig(
            action=action,
            nargs=num_args,
            const=default_missing_value,
            default=default_value,
            choices=choices,
            required=required,
            deprecated=deprecated
        ),
        short=short_name,
        long=long_name,
        aliases=aliases,
        group=group,
        mutex=mutex,
        about=about,
        long_about=long_about,
        value_name=value_name,
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
