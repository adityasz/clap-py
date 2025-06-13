import os
import sys
from collections.abc import Callable, Sequence
from typing import Optional, Self, Union

from clap.styling import Styles

from .help import ColorChoice
from .models import Arg, AutoFlag, Command, Group, MutexGroup
from .parser import (
    _COMMAND_DATA,
    _SUBCOMMAND_DEFAULTS,
    _SUBCOMMAND_MARKER,
    apply_parsed_args,
    create_parser,
    get_help_from_docstring,
    to_kebab_case,
)

_PARSER = "__parser__"


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
    help_styles: Optional[Styles] = None,
    help_template: Optional[str] = None,
    **kwargs,
) -> Union[type[T], Callable[[type[T]], type[T]]]:
    """Configure a class to parse command-line arguments.

    Args:
        cls: The class to be decorated (when used without parentheses).
        name: Overrides the runtime-determined name of the program.
        version: Sets the version for the short version (`-V`) and help messages.
        long_version: Sets the version for the long version (`--version`) and help messages.
        usage: The string describing the program usage. The default is
            generated from arguments added to parser.
        about: The program's description for the short help (`-h`).
        long_about: The program's description for the long help (`--help`).
        after_help: Free-form help text for after auto-generated short help (`-h`).
        after_long_help: Free-form help text for after auto-generated long help (`--help`).
        before_help: Free-form help text for before auto-generated short help (`-h`).
        before_long_help: Free-form help text for before auto-generated long help (`--help`).
        subcommand_help_heading: The help heading used for subcommands when printing help.
        subcommand_value_name: The value name used for subcommands when printing usage and help.
        color: When to color output.
        help_styles: The styles for help output.
        help_template: The help template to be used, overriding the default format.
        propagate_version: Whether to use the version of the current command for all subcommands.
        disable_version_flag: Disable the `-V` and `--version` flags.
        disable_help_flag: Disable the `-h` and `--help` flags.
        prefix_chars: The set of characters that prefix optional arguments.
        fromfile_prefix_chars: The set of characters that prefix files from
            which additional arguments should be read.
        conflict_handler: The strategy for resolving conflicting optionals.
        allow_abbrev: Whether to allow long options to be abbreviated if the
            abbreviation is unambiguous.
        exit_on_error: Whether `ArgumentParser` exits with error info when an error occurs.

    Example:

    ```python
    import clap

    @clap.command(name="git", version="2.49.0")
    class Cli(clap.Parser):
        \"""git - the stupid content tracker\"""
        ...
    ```
    """
    def wrap(cls: type[T]) -> type[T]:
        nonlocal about, long_about, name
        kwargs["name"] = name
        if cls.__doc__ is not None:
            doc_about, doc_long_about = get_help_from_docstring(cls.__doc__.strip())
            if about is None:
                kwargs["about"] = doc_about
            if long_about is None:
                kwargs["long_about"] = doc_long_about
        command = Command(**kwargs)
        setattr(cls, _COMMAND_DATA, command)
        setattr(cls, _PARSER, create_parser(cls, color, help_styles, help_template))

        # delete default values of fields so that `@dataclass` does not complain
        # about mutable defaults (`Arg`)
        for name, _ in cls.__annotations__.items():
            if hasattr(cls, name):
                delattr(cls, name)

        @classmethod
        def parse_args(cls: type[T], args: Optional[list[str]] = None) -> T:
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
        cls: The class to be decorated (when used without parentheses).
        name: Overrides the runtime-determined name of the program.
        usage: The string describing the program usage. The default is
            generated from arguments added to parser.
        aliases: The aliases to this subcommand.
        about: The subcommand's description for the short help (`-h`).
        long_about: The subcommand's description for the long help (`--help`).
        after_help: Free-form help text for after auto-generated short help (`-h`).
        after_long_help: Free-form help text for after auto-generated long help (`--help`).
        before_help: Free-form help text for before auto-generated short help (`-h`).
        before_long_help: Free-form help text for before auto-generated long help (`--help`).
        subcommand_help_heading: The help heading used for subcommands when printing help.
        subcommand_value_name: The value name used for subcommands when printing usage and help.
        color: When to color output.
        help_styles: The styles for help output.
        help_template: The help template to be used, overriding the default format.
        disable_help_flag: Disable the `-h` and `--help` flags.
        prefix_chars: The set of characters that prefix optional arguments.
        fromfile_prefix_chars: The set of characters that prefix files from
            which additional arguments should be read.
        conflict_handler: The strategy for resolving conflicting optionals.
        allow_abbrev: Whether to allow long options to be abbreviated if the
            abbreviation is unambiguous.
        exit_on_error: Whether `ArgumentParser` exits with error info when an error occurs.
    """
    def wrap(cls: type[T]) -> type[T]:
        nonlocal about, long_about, name
        setattr(cls, _SUBCOMMAND_MARKER, True)
        if name is None:
            name = to_kebab_case(cls.__name__)
        kwargs["name"] = name
        if cls.__doc__ is not None:
            doc_about, doc_long_about = get_help_from_docstring(cls.__doc__.strip())
            if about is None:
                kwargs["about"] = doc_about
            if long_about is None:
                kwargs["long_about"] = doc_long_about
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


def arg(
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
        short_or_long: Use `clap.short` or `clap.long` to automatically create
            the short or long version of the argument.
        long_or_short: Use `clap.short` or `clap.long` to automatically create
            the short or long version of the argument.
        short: The short version of the argument without the preceding `-`. Specify
            `True` to automatically create it.
        long: The long version of the argument without the preceding `--`. Specify
            `True` to automatically create it.
        aliases: Additional flags for the argument.
        group: The group to which the argument is added.
        mutex: The mutually exclusive group to which the argument is added.
        action: How to react to an argument when parsing it.
        num_args: The number of arguments parsed per occurrence.
        default_missing_value: The value for the argument when the flag is
            present but no value is specified.
        default_value: The value for the argument when not present.
        choices: A sequence of valid choices for the argument.
        required: Whether the argument must be present.
        help: The description of the argument for short help (`-h`).
        long_help: The description of the argument for long help (`--help`).
        value_name: The placeholder for the argument's value in the help message / usage.
        deprecated: Whether this argument is deprecated and should not be used.

    Examples:

    ```python
    >>> from clap import ArgAction, ColorChoice, arg, long, short
    >>> verbose: bool = arg(short, long)
    >>> include_hidden: bool = arg(short="H", long="hidden")
    >>> additional_patterns: list[str] = arg(long="and", action=ArgAction.Append)
    >>> color: ColorChoice = arg(
        ...     long,
        ...     value_name="WHEN",
        ...     default_value=ColorChoice.Auto,
        ...     default_missing_value=ColorChoice.Always,
        ...     num_args="?"
        ... )
    ```
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


def group(title: str, **kwargs) -> Group:
    """Create an argument group for organizing related arguments in the help output.

    Args:
        title: The title for the argument group in the help output.
        about: The group's description for the short help (`-h`).
        long_about: The group's description for the long help (`--help`).
        conflict_handler: The strategy for resolving conflicting optionals within this group.

    Example:

    ```python
    from pathlib import Path

    import clap
    from clap import group

    @clap.command
    class Cli(clap.Parser):
        output_options = group("Output Options")
        \"""Configure output settings.\"""
        output_dir: Path = arg(long="output", group=output_options, value_name="DIR")
        \"""Path to output directory\"""
    ```
    """
    assert isinstance(title, str)
    return Group(
        title=title,
        **kwargs
    )


def mutex_group(
    parent_group: Optional[Group] = None,
    required: bool = False,
) -> MutexGroup:
    """Create a mutually exclusive group of arguments.

    It will be ensured that only one of the arguments in the mutually
    exclusive group is present on the command line. This is useful for
    options that conflict with each other, such as `--verbose` and `--quiet`.

    Args:
        parent_group: The parent argument group to add this mutually exclusive group to.
            If `None`, the group will be added directly to the parser.
        required: Whether at least one of the mutually exclusive arguments must be present.

    Example:

    ```python
    import clap
    from clap import mutex_group

    @clap.command
    class Cli(clap.Parser):
        loglevel = mutex_group()
        verbose: bool = arg(long, mutex="loglevel")
        quiet: bool = arg(long, mutex="loglevel")
    ```
    """
    return MutexGroup(parent=parent_group, required=required)
