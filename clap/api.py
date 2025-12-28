import os
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Optional, Self, Union, dataclass_transform

from clap.core import (
    Arg,
    ArgAction,
    AutoFlag,
    Command,
    Group,
    NargsType,
    to_kebab_case,
)
from clap.parser import (
    _ATTR_DEFAULTS,
    _COMMAND_DATA,
    _GROUP_DATA,
    _GROUP_MARKER,
    _SUBCOMMAND_MARKER,
    apply_parsed_args,
    create_parser,
    get_help_from_docstring,
)
from clap.styling import ColorChoice, Styles

_PARSER = "__com.github.adityasz.clap-py.parser__"


class Parser:
    """A base class for static type checking.

    Classes decorated with [`@clap.command`][clap.command] will have a
    [`parse`][clap.Parser.parse] method injected at runtime.
    Inheriting from [`Parser`][clap.Parser] provides this method signature to
    static type checkers, avoiding errors and enabling autocompletion in
    editors.

    This class is not strictly required for functionality.

    Example:

    ```python
    import clap


    @clap.command
    class Cli(clap.Parser): ...


    args = Cli.parse()
    ```
    """

    @classmethod
    def parse(cls: type[Self], args: Optional[Sequence[str]] = None) -> Self:
        """Parse from the provided `args` or [`sys.argv`][], exit on error."""
        # - args is passed to the message so that it is no longer unused.
        # - PyCharm does not like it if I make this an abstractmethod.
        #   - Making another superclass where this method is abstract and then
        #     `@override`'ing to suppress the error will only slow down the
        #     runtime.
        msg = (
            f"Did you decorate {cls} with @clap.command: {command}?\n{args or ''}"
        )
        raise NotImplementedError(msg)


@dataclass_transform()
def command[T](
    cls: Optional[type[T]] = None,
    /,
    *,
    name: Optional[str] = None,
    version: Optional[str] = None,
    long_version: Optional[str] = None,
    usage: Optional[str] = None,
    author: Optional[str] = None,
    about: Optional[str] = None,
    long_about: Optional[str] = None,
    before_help: Optional[str] = None,
    before_long_help: Optional[str] = None,
    after_help: Optional[str] = None,
    after_long_help: Optional[str] = None,
    subcommand_help_heading: str = "Commands",
    subcommand_value_name: str = "COMMAND",
    color: Optional[ColorChoice] = None,
    styles: Optional[Styles] = None,
    help_template: Optional[str] = None,
    max_term_width: Optional[int] = None,
    propagate_version: bool = False,
    disable_version_flag: bool = False,
    disable_help_flag: bool = False,
    prefix_chars: str = "-",
    fromfile_prefix_chars: Optional[str] = None,
    conflict_handler: Optional[str] = None,
    allow_abbrev: Optional[bool] = None,
    exit_on_error: Optional[bool] = None,
) -> Union[type[T], Callable[[type[T]], type[T]]]:
    """Configure a class to parse command-line arguments.

    Args:
        cls: The class to be decorated (when used without parentheses).
        name: Overrides the runtime-determined name of the program.
        version: Sets the version for the short version (`-V`) and help messages.
        long_version: Sets the version for the long version (`--version`) and help messages.
        usage: The string describing the program usage. The default is
            generated from arguments added to parser.
        author: Sets the author(s) for the help message. A custom `help_template` is needed for
            author to show up.
        about: The program's description for the short help (`-h`).
        long_about: The program's description for the long help (`--help`).
        after_help: Free-form help text for after auto-generated short help (`-h`).
        after_long_help: Free-form help text for after auto-generated long help (`--help`).
        before_help: Free-form help text for before auto-generated short help (`-h`).
        before_long_help: Free-form help text for before auto-generated long help (`--help`).
        subcommand_help_heading: The help heading used for subcommands when printing help.
        subcommand_value_name: The value name used for subcommands when printing usage and help.
        color: When to color output.
        styles: The styles for help output.
        help_template: The help template to be used, overriding the default format.
        max_term_width: The help output will wrap to
            `min(max_term_width, shutil.get_terminal_size())`.
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
        \"""git - the stupid content tracker.

        Git is a fast, scalable, distributed revision control system with an
        unusually rich command set that provides both high-level operations and
        full access to internals.
        \"""
        ...
    ```
    """

    def wrap(cls: type[T]) -> type[T]:
        nonlocal about, long_about, name
        if cls.__doc__ is not None:
            doc_about, doc_long_about = get_help_from_docstring(cls.__doc__.strip())
            if about is None:
                about = doc_about
            if long_about is None:
                long_about = doc_long_about
        if name is None:
            name = os.path.basename(sys.argv[0])
        command = Command(
            name=name,
            usage=usage,
            author=author,
            version=version,
            long_version=long_version,
            about=about,
            long_about=long_about,
            before_help=before_help,
            before_long_help=before_long_help,
            after_help=after_help,
            after_long_help=after_long_help,
            subcommand_help_heading=subcommand_help_heading,
            subcommand_value_name=subcommand_value_name,
            color=color,
            styles=styles,
            help_template=help_template,
            max_term_width=max_term_width,
            propagate_version=propagate_version,
            disable_version_flag=disable_version_flag,
            disable_help_flag=disable_help_flag,
            prefix_chars=prefix_chars,
            fromfile_prefix_chars=fromfile_prefix_chars,
            conflict_handler=conflict_handler,
            allow_abbrev=allow_abbrev,
            exit_on_error=exit_on_error,
        )

        setattr(cls, _COMMAND_DATA, command)

        # delete default values of fields so that `dataclass` does not complain
        # about mutable defaults (`Arg`)
        attrs = {}
        for name in cls.__annotations__:
            if attr := getattr(cls, name, None):
                attrs[name] = attr
                delattr(cls, name)
        setattr(cls, _ATTR_DEFAULTS, attrs)

        dataclass(cls, slots=True)

        def parse(cls: type[T], args: Optional[list[str]] = None) -> T:
            """Parse command-line arguments and return an instance of the class."""
            if not hasattr(cls, _PARSER):
                # not sure if .parse() would ever have to be called more than
                # once in the real world, but it has to be called multiple times
                # in tests
                setattr(cls, _PARSER, create_parser(cls))
            parser = getattr(cls, _PARSER)
            parsed_args = parser.parse_args(args)
            obj = object.__new__(cls)
            apply_parsed_args(dict(parsed_args._get_kwargs()), obj)
            return obj

        setattr(cls, "parse", classmethod(parse))
        return cls

    if cls is None:
        return wrap
    return wrap(cls)


@dataclass_transform()
def subcommand[T](
    cls: Optional[type[T]] = None,
    /,
    *,
    name: Optional[str] = None,
    version: Optional[str] = None,
    long_version: Optional[str] = None,
    usage: Optional[str] = None,
    aliases: Sequence[str] = (),
    about: Optional[str] = None,
    long_about: Optional[str] = None,
    before_help: Optional[str] = None,
    before_long_help: Optional[str] = None,
    after_help: Optional[str] = None,
    after_long_help: Optional[str] = None,
    subcommand_help_heading: str = "Commands",
    subcommand_value_name: str = "COMMAND",
    color: Optional[ColorChoice] = None,
    styles: Optional[Styles] = None,
    help_template: Optional[str] = None,
    max_term_width: Optional[int] = None,
    propagate_version: bool = False,
    disable_version_flag: bool = False,
    disable_help_flag: bool = False,
    prefix_chars: str = "-",
    fromfile_prefix_chars: Optional[str] = None,
    conflict_handler: Optional[str] = None,
    allow_abbrev: Optional[bool] = None,
    exit_on_error: Optional[bool] = None,
    deprecated: bool = False,
) -> Union[type[T], Callable[[type[T]], type[T]]]:
    """Configure a class as a subcommand parser.

    Args:
        cls: The class to be decorated (when used without parentheses).
        name: Overrides the runtime-determined name of the program.
        version: Sets the version for the short version (`-V`) and help messages.
        long_version: Sets the version for the long version (`--version`) and help messages.
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
        styles: The styles for help output.
        help_template: The help template to be used, overriding the default format.
        max_term_width: The help output will wrap to
            `min(max_term_width, shutil.get_terminal_size())`.
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
        deprecated: Whether this subcommand is deprecated.

    Example:

    ```python
    import clap
    from typing import Union

    @clap.subcommand(aliases=("w", "wat"))
    class Watch:
        \"""Watches an input file and recompiles on changes.\"""
        ...

    @clap.subcommand
    class Init:
        \"""Initializes a new project from a template.\"""
        ...

    @clap.command(name="typst")
    class Cli(clap.Parser):
        command: Union[Watch, Init]
        ...
    ```
    """

    def wrap(cls: type[T]) -> type[T]:
        nonlocal about, long_about, name
        if name is None:
            name = to_kebab_case(cls.__name__)
        if cls.__doc__ is not None:
            doc_about, doc_long_about = get_help_from_docstring(cls.__doc__.strip())
            if about is None:
                about = doc_about
            if long_about is None:
                long_about = doc_long_about
        command = Command(
            name=name,
            aliases=aliases,
            usage=usage,
            version=version,
            long_version=long_version,
            about=about,
            long_about=long_about,
            before_help=before_help,
            before_long_help=before_long_help,
            after_help=after_help,
            after_long_help=after_long_help,
            subcommand_help_heading=subcommand_help_heading,
            subcommand_value_name=subcommand_value_name,
            color=color,
            styles=styles,
            help_template=help_template,
            max_term_width=max_term_width,
            propagate_version=propagate_version,
            disable_version_flag=disable_version_flag,
            disable_help_flag=disable_help_flag,
            prefix_chars=prefix_chars,
            fromfile_prefix_chars=fromfile_prefix_chars,
            conflict_handler=conflict_handler,
            allow_abbrev=allow_abbrev,
            exit_on_error=exit_on_error,
            deprecated=deprecated,
        )

        setattr(cls, _SUBCOMMAND_MARKER, True)
        setattr(cls, _COMMAND_DATA, command)

        # delete default values of fields so that `dataclass` does not complain
        # about mutable defaults (`Arg`)
        attrs = {}
        for name in cls.__annotations__:
            if attr := getattr(cls, name, None):
                attrs[name] = attr
                delattr(cls, name)
        setattr(cls, _ATTR_DEFAULTS, attrs)

        dataclass(cls, slots=True)

        return cls

    if cls is None:
        return wrap
    return wrap(cls)


@dataclass_transform()
def group[T](
    cls: Optional[type[T]] = None,
    /,
    *,
    title: Optional[str] = None,
    about: Optional[str] = None,
    long_about: Optional[str] = None,
    required: bool = False,
    multiple: bool = True,
) -> Union[type[T], Callable[[type[T]], type[T]]]:
    """Configure a class as an argument group.

    Argument groups allow organizing related arguments together, both in
    help output and in code structure. Arguments within a group are accessed
    as nested attributes.

    Args:
        cls: The class to be decorated (when used without parentheses).
        title: The title for the argument group in the help output.
        about: The group's description for the short help (`-h`).
        long_about: The group's description for the long help (`--help`).
        required: Require an argument from the group to be present when parsing.
            Note: Currently, it only works when `multiple = False`.
        multiple: Allows more than one of the Args in this group to be used.

    Example:

    ```python
    import clap
    from clap import arg, long
    from typing import Optional

    @clap.group(title="Input Options")
    class InputOpts:
        input_file: Optional[str] = arg(long)

    @clap.group(title="Output Options")
    class OutputOpts:
        output_file: Optional[str] = arg(long)

    @clap.command
    class Cli(clap.Parser):
        input_opts: InputOpts
        output_opts: OutputOpts

    args = Cli.parse()
    print(args.input_opts.input_file)
    print(args.output_opts.output_dir)
    ```
    """

    def wrap(cls: type[T]) -> type[T]:
        nonlocal title, about, long_about
        if cls.__doc__ is not None:
            doc_about, doc_long_about = get_help_from_docstring(cls.__doc__.strip())
            if about is None:
                about = doc_about
            if long_about is None:
                long_about = doc_long_about

        setattr(cls, _GROUP_MARKER, True)
        setattr(
            cls,
            _GROUP_DATA,
            Group(
                title=title,
                about=about,
                long_about=long_about,
                required=required,
                multiple=multiple,
            ),
        )

        # delete default values of fields so that `dataclass` does not complain
        # about mutable defaults (`Arg`)
        attrs = {}
        for name in cls.__annotations__:
            if attr := getattr(cls, name, None):
                attrs[name] = attr
                delattr(cls, name)
        setattr(cls, _ATTR_DEFAULTS, attrs)

        dataclass(cls, slots=True)

        # This allows hacks like `input_opts: InputOpts = InputOpts()`
        setattr(cls, "__init__", object.__init__)

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
    aliases: Optional[Sequence[str]] = None,
    group: Optional[Group] = None,
    action: Optional[Union[type, ArgAction]] = None,
    num_args: Optional[NargsType] = None,
    default_missing_value: Optional[U] = None,
    default_value: Optional[U] = None,
    choices: Optional[Sequence[str]] = None,
    required: Optional[bool] = None,
    help: Optional[str] = None,
    long_help: Optional[str] = None,
    value_name: Optional[str] = None,
    deprecated: bool = False,
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
    import clap
    from clap import ArgAction, ColorChoice, arg, long, short


    @clap.command
    class Cli:
        verbose: bool = arg(short, long)
        include_hidden: bool = arg(short="H", long="hidden")
        additional_patterns: list[str] = arg(long="and", action=ArgAction.Append)
        color: ColorChoice = arg(
            long,
            value_name="WHEN",
            default_value=ColorChoice.Auto,
            default_missing_value=ColorChoice.Always,
            num_args="?",
        )
    ```
    """
    short_name: Optional[Union[AutoFlag, str]] = None
    long_name: Optional[Union[AutoFlag, str]] = None

    match short_or_long:
        case AutoFlag.Short: short_name = AutoFlag.Short
        case AutoFlag.Long: long_name = AutoFlag.Long
        case _: pass

    match long_or_short:
        case AutoFlag.Short: short_name = AutoFlag.Short
        case AutoFlag.Long: long_name = AutoFlag.Long
        case _: pass

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

    return Arg(
        short=short_name,
        long=long_name,
        help=help,
        long_help=long_help,
        value_name=value_name,
        aliases=aliases or [],
        group=group,
        action=action,
        num_args=num_args,
        default_missing_value=default_missing_value,
        default_value=default_value,
        choices=choices,
        required=required,
        deprecated=deprecated,
    )
