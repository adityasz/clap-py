import argparse
import re
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum, StrEnum, auto
from typing import (
    Any,
    Literal,
    Optional,
    Self,
    Union,
    cast,
)

from .styling import ColorChoice, Styles


class AutoFlag(Enum):
    Short = auto()
    """Generate short from the first character in the case-converted field name."""
    Long = auto()
    """Generate long from the case-converted field name."""


class ArgAction(StrEnum):
    Set = "store"
    """When encountered, store the associated value(s).

    Example:

    ```python
    import clap
    from clap import ArgAction, long

    @clap.command
    class Cli(clap.Parser):
        output: str = arg(long, action=ArgAction.Set)

    args = Cli.parse_args(["--output", "file.txt"])
    assert args.output == "file.txt"
    ```
    """
    SetTrue = "store_true"
    """When encountered, act as if [`True`][] was encountered on the command-line.

    Example:

    ```python
    import clap
    from clap import ArgAction, long

    @clap.command
    class Cli(clap.Parser):
        verbose: bool = arg(long, action=ArgAction.SetTrue)

    args = Cli.parse_args(["--verbose"])
    assert args.verbose == True

    args = Cli.parse_args([])
    assert args.verbose == False
    ```
    """
    SetFalse = "store_false"
    """When encountered, act as if [`False`][] was encountered on the command-line.

    Example:

    ```python
    import clap
    from clap import ArgAction, long

    @clap.command
    class Cli(clap.Parser):
        quiet: bool = arg(long, action=ArgAction.SetFalse)

    args = Cli.parse_args(["--quiet"])
    assert args.quiet == False

    args = Cli.parse_args([])
    assert args.quiet == True
    ```
    """
    Append = "append"
    """When encountered, store the associated value(s) in a [`list`][].

    Example:

    ```python
    import clap
    from clap import ArgAction, long

    @clap.command
    class Cli(clap.Parser):
        files: list[str] = arg(long, action=ArgAction.Append)

    args = Cli.parse_args(["--files", "a.txt", "--files", "b.txt"])
    assert args.files == ["a.txt", "b.txt"]

    args = Cli.parse_args([])
    assert args.files == []
    ```
    """
    Extend = "extend"
    """When encountered, extend a [`list`][] with the associated values.

    Example:

    ```python
    import clap
    from clap import ArgAction, long

    @clap.command
    class Cli(clap.Parser):
        items: list[str] = arg(long, action=ArgAction.Extend, num_args='+')

    args = Cli.parse_args(["--items", "a", "b", "--items", "c", "d"])
    assert args.items == ["a", "b", "c", "d"]

    args = Cli.parse_args([])
    assert args.items == []
    ```
    """
    Count = "count"
    """When encountered, increment an [`int`][] counter starting from `0`.

    Example:

    ```python
    import clap
    from clap import ArgAction, short

    @clap.command
    class Cli(clap.Parser):
        verbose: int = arg(short, action=ArgAction.Count)

    args = Cli.parse_args(["-vvv"])
    assert args.verbose == 3

    args = Cli.parse_args([])
    assert args.verbose == 0
    ```
    """

    class Version(argparse.Action):
        """When encountered, display version information.

        Depending on the flag, `long_version` may be shown.
        """

        def __init__(self, option_strings, dest, **kwargs):
            super().__init__(option_strings, dest, nargs=0)

        def __call__(self, parser, namespace, values, option_string=None):
            from .parser import ClapArgParser
            parser = cast(ClapArgParser, parser)
            if isinstance(option_string, str) and len(option_string) == 2:
                parser.print_version(use_long=False)
            else:
                parser.print_version(use_long=True)

    class Help(argparse.Action):
        """When encountered, display help information.

        Depending on the flag, `long_help` may be shown.
        """

        def __init__(self, option_strings, dest, **kwargs):
            super().__init__(option_strings, dest, nargs=0)

        def __call__(self, parser, namespace, values, option_string=None):
            from .parser import ClapArgParser
            parser = cast(ClapArgParser, parser)
            if isinstance(option_string, str) and len(option_string) == 2:
                parser.print_nice_help(use_long=False)
            else:
                parser.print_nice_help(use_long=True)

    class HelpShort(argparse.Action):
        """When encountered, display short help information."""

        def __init__(self, option_strings, dest, **kwargs):
            super().__init__(option_strings, dest, nargs=0)

        def __call__(self, parser, namespace, values, option_string=None):
            from .parser import ClapArgParser
            parser = cast(ClapArgParser, parser)
            parser.print_nice_help(use_long=False)

    class HelpLong(argparse.Action):
        """When encountered, display long help information."""

        def __init__(self, option_strings, dest, **kwargs):
            super().__init__(option_strings, dest, nargs=0)

        def __call__(self, parser, namespace, values, option_string=None):
            from .parser import ClapArgParser
            parser = cast(ClapArgParser, parser)
            parser.print_nice_help(use_long=True)


short = AutoFlag.Short
"""Generate short from the first character in the case-converted field name."""
long = AutoFlag.Long
"""Generate long from the case-converted field name."""

type NargsType = Union[Literal['?', '*', '+'], int]


def to_kebab_case(name: str) -> str:
    name = name.replace('_', '-')  # snake_case, SCREAMING_SNAKE_CASE
    name = re.sub(r'([a-z0-9])([A-Z])', r'\1-\2', name)  # camelCase, PascalCase
    name = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1-\2', name)  # HTTPSConnection -> HTTPS-Connection
    name = name.lower()
    name = re.sub(r'-+', '-', name)
    name = name.strip('-')
    return name


class ArgType:
    @dataclass(slots=True)
    class Base:
        ty: type
        optional: bool

    @dataclass(slots=True)
    class SimpleType(Base): ...

    @dataclass(slots=True)
    class Enum(Base):
        enum: type
        ty: type = field(init=False)
        members: dict = field(init=False)
        choice_to_enum_member: dict[str, Any] = field(init=False)

        def __post_init__(self):
            self.ty = str
            self.members = self.enum.__members__
            choices = list(map(to_kebab_case, self.members.keys()))
            try:
                self.choice_to_enum_member = {
                    c: m for c, m in zip(choices, self.members.values(), strict=True)
                }
            except ValueError:
                raise TypeError("Cannot uniquely extract choices from this Enum.") from None

    @dataclass(slots=True)
    class List(Base): ...

    @dataclass(slots=True)
    class Tuple(Base):
        n: int

    @dataclass(slots=True)
    class SubcommandDest(Base):
        subcommands: list[type]
        ty: type = field(init=False)

        # TODO: this is ugly; figure out a better pattern matching scheme
        def __post_init__(self):
            self.ty = type(None)


@dataclass(slots=True)
class Group:
    """Family of related [arguments][clap.core.Arg]."""
    title: str
    """The title for the argument group in the help output."""
    about: Optional[str] = None
    """The group's description for the short help (`-h`).

    If [`Group.long_about`][clap.Group.long_about] is not specified,
    this message will be displayed for `--help`.
    """
    long_about: Optional[str] = None
    """The group's description for the long help (`--help`).

    If not set, [`Group.about`][clap.Group.about] will be used for long help in
    addition to short help (`-h`).
    """
    conflict_handler: Optional[str] = None
    """The strategy for resolving conflicting optionals within this group.

    This is forwarded to [argparse][].
    """

    def __hash__(self):
        return hash(id(self))

    def get_argparse_kwargs(self):
        kwargs = {}
        kwargs.update({
            k: v
            for k, v in {
                "title": self.title,
                "description": self.long_about,
                "conflict_handler": self.conflict_handler,
            }.items()
            if v is not None
        })
        return kwargs


@dataclass(slots=True)
class MutexGroup:
    parent: Optional[Group] = None
    required: bool = False

    def __hash__(self):
        return hash(id(self))


@dataclass(slots=True)
class Arg:
    short: Optional[Union[AutoFlag, str]] = None
    """The short flag."""
    long: Optional[Union[AutoFlag, str]] = None
    """The long flag."""
    help: Optional[str] = None
    long_help: Optional[str] = None
    value_name: Optional[str] = None
    aliases: Sequence[str] = field(default_factory=list)
    """Flags in addition to `short` and `long`."""
    ty: Optional[ArgType.Base] = None
    """Stores type information for the argument."""
    group: Optional[Group] = None
    """The group containing the argument."""
    mutex: Optional[MutexGroup] = None
    """The mutually exclusive group containing the argument."""

    action: Optional[Union[ArgAction, type]] = None
    num_args: Optional[NargsType] = None
    default_missing_value: Optional[Any] = None
    default_value: Optional[Any] = None
    choices: Optional[Sequence[str]] = None
    required: Optional[bool] = None
    deprecated: Optional[bool] = None
    dest: Optional[str] = None

    def is_positional(self) -> bool:
        return not self.short and not self.long

    def get_argparse_flags(self) -> list[str]:
        if self.is_positional():
            assert self.dest is not None
            return [self.dest]
        flags = []
        if self.short:
            flags.append(self.short)
        if self.long:
            flags.append(self.long)
        flags.extend(self.aliases)
        return flags

    def get_argparse_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}

        kwargs.update({
            k: v
            for k, v in {
                "nargs": self.num_args,
                "const": self.default_missing_value,
                "choices": self.choices if self.choices else None,
                "required": self.required,
                "default": self.default_value,
                "deprecated": self.deprecated,
                "metavar": self.value_name,
                "dest": self.dest,
            }.items()
            if v is not None
        })

        if self.ty is not None:
            kwargs["type"] = self.ty.ty

        if self.is_positional():
            kwargs.pop("dest")

        if self.action in (ArgAction.Count, ArgAction.SetTrue, ArgAction.SetFalse):
            kwargs.pop("type")

        kwargs["action"] = self.action

        if self.num_args == 0 and self.action == ArgAction.Append:
            kwargs["action"] = "append_const"
            kwargs.pop("type")
            kwargs.pop("nargs")

        if self.num_args == 0 and self.action == ArgAction.Set:
            kwargs["action"] = "store_const"
            kwargs.pop("type")
            kwargs.pop("nargs")

        if (action := kwargs["action"]) in ArgAction:
            kwargs["action"] = str(action)

        # argparse does not add an argument to the `Namespace` it returns
        # unless it has a default (which can be `None`)
        kwargs.setdefault("default", None)

        return kwargs


@dataclass(slots=True)
class Command:
    name: str
    aliases: Sequence[str] = field(default_factory=list)
    usage: Optional[str] = None
    version: Optional[str] = None
    long_version: Optional[str] = None
    about: Optional[str] = None
    long_about: Optional[str] = None
    before_help: Optional[str] = None
    before_long_help: Optional[str] = None
    after_help: Optional[str] = None
    after_long_help: Optional[str] = None
    subcommand_help_heading: str = "Commands"
    subcommand_value_name: str = "COMMAND"
    color: Optional[ColorChoice] = None
    styles: Optional[Styles] = None
    help_template: Optional[str] = None
    max_term_width: Optional[int] = None
    propagate_version: bool = False
    disable_version_flag: bool = False
    disable_help_flag: bool = False
    prefix_chars: str = "-"
    fromfile_prefix_chars: Optional[str] = None
    conflict_handler: Optional[str] = None
    allow_abbrev: Optional[bool] = None
    exit_on_error: Optional[bool] = None
    deprecated: Optional[bool] = None

    args: dict[str, Arg] = field(default_factory=dict)
    groups: dict[Group, list[Arg]] = field(default_factory=dict)
    mutexes: defaultdict[MutexGroup, list[Arg]] = field(default_factory=lambda: defaultdict(list))

    subcommand_class: Optional[type] = None
    """Contains the class if it is a subcommand."""

    subcommands: dict[str, Self] = field(default_factory=dict)
    subcommand_dest: Optional[str] = None
    subparser_dest: Optional[str] = None
    subcommand_required: bool = False

    def is_subcommand(self) -> bool:
        return self.subcommand_class is not None

    def contains_subcommands(self) -> bool:
        return self.subcommand_dest is not None

    def get_parser_kwargs(self) -> dict[str, Any]:
        kwargs = {}

        if self.is_subcommand():
            kwargs["name"] = self.name
        else:
            kwargs["prog"] = self.name

        kwargs.update({
            k: v
            for k, v in {
                "usage": self.usage,
                "prefix_chars": self.prefix_chars,
                "fromfile_prefix_chars": self.fromfile_prefix_chars,
                "conflict_handler": self.conflict_handler,
                "allow_abbrev": self.allow_abbrev,
                "exit_on_error": self.exit_on_error,
                "deprecated": self.deprecated,
                "aliases": self.aliases if self.aliases else None,
            }.items()
            if v is not None
        })

        return kwargs
