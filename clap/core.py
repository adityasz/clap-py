# TODO: short/long validation
# TODO: help actions with _ = ...

import argparse
import ast
import builtins
import re
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field, fields
from enum import Enum, EnumType, StrEnum, auto
from inspect import getsource
from textwrap import dedent
from typing import (
    Any,
    Literal,
    Optional,
    Self,
    Union,
    cast,
    get_args,
    get_origin,
    get_type_hints,
)

_COMMAND_MARKER = "__com.github.adityasz.clap_py.command_marker__"
_SUBCOMMAND_MARKER = "__com.github.adityasz.clap_py.subcommand_marker__"
_PARSER = "__parser__"
_COMMAND_DATA = "__command_data__"
_SUBCOMMAND_DEST = "__subcommand_dest__"
_HELP_DEST = "0h"
_HELP_SHORT_DEST = "0s"
_HELP_LONG_DEST = "0l"
_VERSION_DEST = "0v"


class ColorChoice(Enum):
    Auto = auto()
    Always = auto()
    Never = auto()


class AutoShortFlag:
    ...


class AutoLongFlag:
    ...


class ArgAction(StrEnum):
    Set = "store"
    SetTrue = "store_true"
    SetFalse = "store_false"
    Append = "append"
    Extend = "extend"
    Count = "count"
    Help = auto()
    HelpShort = auto()
    HelpLong = auto()
    Version = auto()


short = AutoShortFlag()
"""Generate short from the first character in the case-converted field name."""

long = AutoLongFlag()
"""Generate long from the case-converted field name."""

type ArgparseAction = Union[
    type,
    Literal[
        "store",
        "store_const",
        "store_true",
        "store_false",
        "append",
        "append_const",
        "extend",
        "count",
    ],
]

type NargsType = Union[Literal['?', '*', '+'], int]


class ArgType:
    class Base:
        optional: bool

    @dataclass
    class SimpleType(Base):
        ty: type
        optional: bool

    class Enum(Base):
        def __init__(self, enum: type, optional: bool):
            self.enum = enum
            self.members = enum.__members__
            choices = list(map(to_kebab_case, self.members.keys()))
            try:
                self.choice_to_enum_member: dict[str, Any] = {
                    c: m for c, m in zip(choices, self.members.values(), strict=True)
                }
            except ValueError:
                raise TypeError("Cannot uniquely extract choices from this Enum.") from None
            self.optional = optional

    @dataclass
    class List(Base):
        ty: type
        optional: bool

    @dataclass
    class Tuple(Base):
        ty: type
        n: int
        optional: bool

    @dataclass
    class SubcommandDest(Base):
        subcommands: list[type]
        optional: bool


@dataclass
class ConfigBase:
    def get_kwargs(self) -> dict[str, Any]:
        """Only returns non-None fields.

        Let argparse handle default configuration.
        """
        fields = asdict(self)
        kwargs = {}
        for k, v in fields.items():
            if v is not None:
                kwargs[k] = v
        return kwargs


@dataclass
class Group(ConfigBase):
    title: str
    description: Optional[str] = None
    prefix_chars: Optional[str] = None
    conflict_handler: Optional[str] = None

    def __hash__(self):
        return hash(self.title)


@dataclass
class MutexGroup:
    parent: Optional[Group] = None
    required: bool = False

    def __hash__(self):
        return hash(id(self))


@dataclass
class ArgConfig(ConfigBase):
    action: Optional[ArgparseAction | ArgAction] = None
    nargs: Optional[NargsType] = None
    const: Optional[Any] = None
    default: Optional[Any] = None
    type: Optional[builtins.type] = None
    choices: Optional[Sequence[str]] = None
    required: Optional[bool] = None
    deprecated: Optional[bool] = None
    metavar: Optional[str] = None  # for argparse error messages
    dest: Optional[str] = None


@dataclass
class Arg:
    arg_config: ArgConfig = field(default_factory=ArgConfig)
    """The kwargs for `parser.add_argument()`."""

    about: Optional[str] = None
    """..."""
    long_about: Optional[str] = None
    """..."""
    value_name: Optional[str] = None
    """..."""
    short: Optional[Union[AutoShortFlag, str]] = None
    """The short flag."""
    long: Optional[Union[AutoLongFlag, str]] = None
    """The long flag."""
    aliases: Optional[Sequence[str]] = None
    """Flags in addition to `short` and `long`."""
    ty: Optional[ArgType.Base] = None
    """Stores type information for the argument."""
    group: Optional[Group] = None
    """The group containing the argument."""
    mutex: Optional[MutexGroup] = None
    """The mutually exclusive group containing the argument."""

    def __repr__(self):
        attrs = []
        if self.short is not None:
            attrs.append(f'"{self.short}"' if isinstance(self.short, str) else "short")
        if self.long is not None:
            attrs.append(f'"{self.long}"' if isinstance(self.long, str) else "long")
        for attr, val in self.arg_config.get_kwargs().items():
            attrs.append(f"{attr}={val}")
        for f in fields(self):
            if (
                f.name not in ("arg_kwargs", "short", "long", "ty")
                and (value := getattr(self, f.name)) is not None
            ):
                attrs.append(f"{f.name}={value}")
        return f"{self.__class__.__name__}({", ".join(attrs)})"

    def is_positional(self) -> bool:
        return not self.short and not self.long

    def get_flags(self) -> list[str]:
        flags = []
        if self.short:
            flags.append(self.short)
        if self.long:
            flags.append(self.long)
        if self.aliases:
            flags.extend(self.aliases)
        return flags

    def get_kwargs(self) -> dict[str, Any]:
        kwargs = self.arg_config.get_kwargs()
        # argparse does not add an argument to the `argparse.Namespace` that
        # `argparse.ArgumentParser.parser_args()` returns unless it has a value.
        # So, to get everything, set default value to None if not already set.
        if not isinstance(self.arg_config.action, type):
            kwargs.setdefault("default", None)
        return kwargs


@dataclass
class SubparsersConfig(ConfigBase):
    required: Optional[bool] = None
    dest: Optional[str] = None


@dataclass
class ParserConfig(ConfigBase):
    prog: Optional[str] = None
    usage: Optional[str] = None
    prefix_chars: str = "-"
    fromfile_prefix_chars: Optional[str] = None
    conflict_handler: Optional[str] = None
    allow_abbrev: Optional[bool] = None
    exit_on_error: Optional[bool] = None
    # The following are used by subcommands (subparsers.add_parser()):
    name: Optional[str] = None
    deprecated: Optional[bool] = None
    aliases: Optional[Sequence[str]] = None


@dataclass
class Command:
    parser_config: ParserConfig
    """Contains kwargs for argparse.ArgumentParser() and subparsers.add_parser()."""
    subparsers_config: Optional[SubparsersConfig] = None
    """Contains kwargs for parser.add_subparsers() if the command has subcommands."""
    subcommand_class: Optional[type] = None
    """Contains the class if the command is a subcommand."""

    name: Optional[str] = None
    version: Optional[str] = None
    about: Optional[str] = None
    long_about: Optional[str] = None
    after_help: Optional[str] = None
    subcommand_help_heading: Optional[str] = None
    subcommand_value_name: Optional[str] = None
    disable_version_flag: bool = False
    disable_help_flag: bool = False
    disable_help_subcommand: bool = False
    heading_ansi_prefix: Optional[str] = None
    argument_ansi_prefix: Optional[str] = None

    arguments: dict[str, Arg] = field(default_factory=dict)
    options: dict[str, Arg] = field(default_factory=dict)
    groups: dict[Group, list[Arg]] = field(default_factory=dict)
    mutexes: defaultdict[MutexGroup, list[Arg]] = field(default_factory=lambda: defaultdict(list))
    subcommands: dict[str, Self] = field(default_factory=dict)
    subcommand_aliases: dict[str, str] = field(default_factory=dict)
    subcommand_dest: Optional[str] = None


def get_about_from_docstring(docstring: str) -> str:
    return docstring[:docstring.find("\n")]


def is_subcommand(cls: type) -> bool:
    return getattr(cls, _SUBCOMMAND_MARKER, False)


def contains_subcommands(types: list[type]) -> bool:
    error_msg = "Field contains a mixture of subcommands and other types."
    flag = None
    for ty in types:
        if is_subcommand(ty):
            if flag is False:
                raise TypeError(error_msg)
            flag = True
        else:
            if flag is True:
                raise TypeError(error_msg)
            flag = False
    return bool(flag)


def to_kebab_case(name: str) -> str:
    name = name.replace('_', '-')  # snake_case, SCREAMING_SNAKE_CASE
    name = re.sub(r'([a-z0-9])([A-Z])', r'\1-\2', name)  # camelCase, PascalCase
    name = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1-\2', name)  # HTTPSConnection -> HTTPS-Connection
    name = name.lower()
    name = re.sub(r'-+', '-', name)
    name = name.strip('-')
    return name


class DocstringExtractor(ast.NodeVisitor):
    def __init__(self):
        self.docstrings: dict[str, str] = {}

    def visit_ClassDef(self, node):
        for stmt_1, stmt_2 in zip(node.body[:-1], node.body[1:], strict=False):
            if (
                isinstance(stmt_1, ast.AnnAssign)
                and isinstance(stmt_1.target, ast.Name)
                and isinstance(stmt_2, ast.Expr)
                and isinstance(stmt_2.value, ast.Constant)
                and isinstance(stmt_2.value.value, str)
            ):
                self.docstrings[stmt_1.target.id] = stmt_2.value.value.strip()
                # Class attributes do not have __doc__, but the interpreter does
                # not strip away the docstrings either. So we can get them from
                # the AST.
                #
                # >>> file: Path
                # >>> """Path to the input file"""


def extract_docstrings(cls: type) -> dict[str, str]:
    extractor = DocstringExtractor()
    try:
        source = dedent(getsource(cls))
    except OSError:
        # can't get source in an ipykernel for example
        return {}
    tree = ast.parse(source)
    extractor.visit(tree)
    return extractor.docstrings


def parse_type_hint(type_hint: Any, optional: bool = False) -> ArgType.Base:
    if type(type_hint) is type:
        if is_subcommand(type_hint):
            return ArgType.SubcommandDest([type_hint], optional)
        return ArgType.SimpleType(type_hint, optional)
    if type(type_hint) is EnumType:
        return ArgType.Enum(type_hint, optional)
    origin = get_origin(type_hint)
    types = get_args(type_hint)
    if origin is Union:
        subcommands = []
        for ty in types:
            if ty is type(None):
                optional = True
            else:
                subcommands.append(ty)
        if contains_subcommands(subcommands):
            return ArgType.SubcommandDest(subcommands, optional)
        if len(types) != 2 or not optional:
            raise TypeError(f"{type_hint}: Unions can only contain subcommands.")
        if type(None) is types[0]:
            return parse_type_hint(types[1], True)
        elif type(None) is types[1]:
            return parse_type_hint(types[0], True)
    if origin is list:
        return ArgType.List(types[0], optional)
    if origin is tuple:
        for ty in types:
            if ty != (types[0]):
                raise TypeError("Heterogenous tuples are not supported.")
        return ArgType.Tuple(types[0], len(types), optional)
    raise TypeError(f"Could not parse {type_hint}.")


def set_flags(arg: Arg, field_name: str, prefix_chars: str):
    """Sets short and long flags of the argument."""
    if isinstance(arg.short, AutoShortFlag):
        arg.short = "-" + field_name[0].lower()
    elif isinstance(arg.short, str) and not arg.short.startswith("-"):
        arg.short = "-" + arg.short

    if isinstance(arg.long, AutoLongFlag):
        arg.long = "--" + to_kebab_case(field_name)
    elif isinstance(arg.long, str) and not arg.long.startswith("--"):
        arg.long = "--" + arg.long


def set_type_dependent_kwargs(arg: Arg):
    kwargs = arg.arg_config

    match arg.ty:
        case ArgType.SimpleType(t):
            if t is bool:
                if kwargs.action is None:
                    kwargs.action = ArgAction.SetTrue
            else:
                if kwargs.action is None:
                    kwargs.action = ArgAction.Set
                kwargs.type = t
        case ArgType.Enum(enum=enum, choice_to_enum_member=choice_to_enum_member):
            if kwargs.action is None:
                kwargs.action = ArgAction.Set
            kwargs.type = str
            kwargs.choices = list(choice_to_enum_member.keys())
            if isinstance(kwargs.default, enum):
                for choice, member in choice_to_enum_member.items():
                    if member == kwargs.default:
                        kwargs.default = choice  # set default to a string for help message
        case ArgType.List(t):
            if kwargs.action is None:
                kwargs.action = ArgAction.Set
            if kwargs.nargs is None and kwargs.action in (ArgAction.Set, ArgAction.Extend):
                kwargs.nargs = "*"
            kwargs.type = t
        case ArgType.Tuple(t, n):
            if kwargs.action is None:
                kwargs.action = ArgAction.Set
            kwargs.type = t
            if (nargs := kwargs.nargs) is not None:
                if nargs != n:
                    raise TypeError(f"The tuple has {n} values but 'num_args' is set to {nargs}.")
            else:
                kwargs.nargs = n
        case _:
            raise TypeError("An unknown error occurred.")


def set_action_dependent_kwargs(arg: Arg):
    kwargs = arg.arg_config
    assert arg.ty is not None
    optional_type_hint = arg.ty.optional

    match kwargs.action:
        case ArgAction.Append:
            if not optional_type_hint and not kwargs.default:
                kwargs.default = []
            if kwargs.required is None:
                kwargs.required = False
            if kwargs.nargs == 0:
                kwargs.nargs = None
                kwargs.action = "append_const"
                kwargs.type = None
        case ArgAction.Extend:
            if not optional_type_hint and not kwargs.default:
                kwargs.default = []
            if kwargs.required is None:
                kwargs.required = False
        case ArgAction.Count:
            if kwargs.default is None:
                kwargs.default = 0
            if kwargs.required is None:
                kwargs.required = False
            if optional_type_hint:
                raise TypeError(
                    "An argument with the 'count' action cannot be None. If no default is "
                    "provided, it is set to 0."
                )
            arg.value_name = None
        case ArgAction.Set:
            if kwargs.required is not None:
                if kwargs.required and optional_type_hint:
                    raise TypeError("An argument with 'required=True' can never be None.")
                return
            if kwargs.default is not None and optional_type_hint:
                raise TypeError("An argument with a default value can never be None.")
            if kwargs.default is None:
                kwargs.required = not optional_type_hint
            if kwargs.nargs == 0:
                kwargs.nargs = None
                kwargs.action = "store_const"
                kwargs.type = None
        case ArgAction.SetFalse:
            if optional_type_hint:
                raise TypeError("An argument with the 'store_false' action can never be None.")
            if kwargs.default is None:
                kwargs.default = True
            if kwargs.required is None:
                kwargs.required = False
            arg.value_name = None
        case ArgAction.SetTrue:
            if optional_type_hint:
                raise TypeError("An argument with the 'store_true' action can never be None.")
            if kwargs.default is None:
                kwargs.default = False
            if kwargs.required is None:
                kwargs.required = False
            arg.value_name = None

    if arg.is_positional():
        if optional_type_hint:
            if (nargs := kwargs.nargs) is not None and nargs != '?':
                raise TypeError(
                    "A positional argument with 'num_args != ?' can never be None; an empty list "
                    "is returned when no argument is provided with 'num_args' is 0 or *."
                )
            kwargs.nargs = '?'
        kwargs.required = None

    if kwargs.action in (ArgAction.Count, ArgAction.SetTrue, ArgAction.SetFalse):
        kwargs.type = None

    if kwargs.const is not None:
        if kwargs.action == ArgAction.SetTrue:
            raise TypeError(
                "'default_missing_value' has no purpose when action is 'SetTrue'."
            )
        if kwargs.action not in ("append_const", "store_const"):
            if kwargs.nargs is None:
                kwargs.nargs = "?"
            elif kwargs.nargs not in ("?", "*", 0):
                raise TypeError(
                    "'num_args' must be '?', '*', or 0 if 'default_missing_value' is not None"
                )


def set_value_name(arg: Arg, field_name: str):
    kwargs = arg.arg_config
    arg.value_name = field_name.upper()

    match kwargs.nargs:
        case '?':
            arg.value_name = f"[{arg.value_name}]"
        case '*':
            arg.value_name = f"[<{arg.value_name}>...]"
        case '+':
            arg.value_name = f"<{arg.value_name}>..."
        case int(n):
            arg.value_name = " ".join(f"<{arg.value_name}>" for _ in range(n))
        case None:
            match kwargs.action:
                case ArgAction.Set | ArgAction.Append | ArgAction.Extend:
                    arg.value_name = f"<{arg.value_name}>"
                case _:
                    arg.value_name = None

    kwargs.metavar = arg.value_name


def add_argument(
    arg: Arg,
    ty: ArgType.Base,
    command: Command,
    field_name: str,
    command_path: str,
    docstrings: dict[str, str],
):
    arg.ty = ty
    arg.arg_config.dest = command_path + field_name
    docstring = docstrings.get(field_name)
    if docstring is not None:
        if arg.about is None:
            arg.about = get_about_from_docstring(docstring)
        if arg.long_about is None:
            arg.long_about = docstring

    set_flags(arg, field_name, command.parser_config.prefix_chars)

    set_type_dependent_kwargs(arg)

    set_action_dependent_kwargs(arg)

    set_value_name(arg, field_name)

    if isinstance(arg.arg_config.action, ArgAction):
        arg.arg_config.action = cast(ArgparseAction, str(arg.arg_config.action))

    command.arguments[field_name] = arg

    if (mutex := arg.mutex) is not None:
        if (group := arg.group) is not None and mutex.parent != group:
            raise ValueError(
                "The mutex group's parent group ('{}') is different from this "
                "argument's group ('{}'). It is not necessary to provide the "
                "group when the mutex group is already provided because the "
                "mutex group's parent must be the given group."
            )
        command.mutexes[mutex].append(arg)
    elif (group := arg.group) is not None:
        command.groups[group].append(arg)


def configure_subcommands(
    ty: ArgType.SubcommandDest,
    command: Command,
    value: Any,
    field_name: str,
    command_path: str,
):
    if command.subcommand_dest is not None:
        raise TypeError(
            f"'{command.subcommand_dest}' is already the subcommand destination."
        )
    command.subcommand_dest = field_name
    if value is not None:
        raise TypeError(
            f"{field_name} is a subcommand destination based on the annotation; "
            f"cannot assign {type(value)} to it."
        )
    # if dest is not provided to add_subparsers(), argparse does not give the
    # command name, and if a subcommand shares a flag name with the command and
    # the flag is provided for both of them, argparse simply overwrites it in
    # the output (argparse.Namespace)
    command.subparsers_config = SubparsersConfig(
        required=not ty.optional, dest=command_path + command.subcommand_dest
    )
    for cmd in ty.subcommands:
        subcommand = create_command(cmd, command_path)
        name = subcommand.parser_config.name
        assert name is not None
        command.subcommands[name] = subcommand
        if subcommand.parser_config.aliases:
            for alias in subcommand.parser_config.aliases:
                command.subcommand_aliases[alias] = name


class ClapArgumentParser(argparse.ArgumentParser):
    def __init__(
        self,
        command: Command,
        prog: Optional[str] = None,
        prefix_chars="-",
        fromfile_prefix_chars=None,
        conflict_handler="error",
        allow_abbrev=True,
        exit_on_error=True,
        **kwargs,
    ):
        self.command = command
        super().__init__(
            prog=prog,
            prefix_chars=prefix_chars,
            fromfile_prefix_chars=fromfile_prefix_chars,
            conflict_handler=conflict_handler,
            allow_abbrev=allow_abbrev,
            exit_on_error=exit_on_error,
            add_help=False,
            **kwargs
        )

    def print_version(self):
        print("version")

    def print_short_help(self):
        print("short_help")

    def print_long_help(self):
        print("long_help")


class VersionAction(argparse.Action):
    def __init__(self, option_strings, dest):
        super().__init__(option_strings, dest, nargs=0)

    def __call__(self, parser, namespace, values, option_string=None):
        import sys
        assert isinstance(parser, ClapArgumentParser)
        parser.print_version()
        sys.exit(0)


class HelpAction(argparse.Action):
    def __init__(self, option_strings, dest):
        super().__init__(option_strings, dest, nargs=0)

    def __call__(self, parser, namespace, values, option_string=None):
        import sys
        assert isinstance(parser, ClapArgumentParser)
        if isinstance(option_string, str) and len(option_string) == 2:
            parser.print_short_help()
        else:
            parser.print_long_help()
        sys.exit(0)


class ShortHelpAction(argparse.Action):
    def __init__(self, option_strings, dest):
        super().__init__(option_strings, dest, nargs=0)

    def __call__(self, parser, namespace, values, option_string=None):
        import sys
        assert isinstance(parser, ClapArgumentParser)
        parser.print_short_help()
        sys.exit(0)


class LongHelpAction(argparse.Action):
    def __init__(self, option_strings, dest):
        super().__init__(option_strings, dest, nargs=0)

    def __call__(self, parser, namespace, values, option_string=None):
        import sys
        assert isinstance(parser, ClapArgumentParser)
        parser.print_long_help()
        sys.exit(0)


def create_command(cls: type, command_path: str = "") -> Command:
    command: Command = getattr(cls, _COMMAND_DATA)

    if getattr(cls, _SUBCOMMAND_MARKER, False):
        assert command.parser_config.name is not None
        command_path += command.parser_config.name + "."
        command.subcommand_class = cls

    for field_name in dir(cls):
        value = getattr(cls, field_name, None)
        if isinstance(value, Group):
            if value in command.groups:
                raise ValueError(f"A group with title '{value.title}' already exists.")
            command.groups[value] = []
        if isinstance(value, Arg) and value.arg_config.action in (
            HelpAction,
            ShortHelpAction,
            LongHelpAction,
            VersionAction,
        ):
            command.arguments[command_path + field_name] = value

    docstrings: dict[str, str] = extract_docstrings(cls)
    type_hints = get_type_hints(cls)

    for field_name, type_hint in type_hints.items():
        ty = parse_type_hint(type_hint)
        value = getattr(cls, field_name, None)
        if isinstance(ty, ArgType.SubcommandDest):
            configure_subcommands(ty, command, value, field_name, command_path)
        elif isinstance(value, Group):
            continue  # already handled in the previous loop
        else:
            if value is not None and not isinstance(value, Arg):
                raise TypeError(
                    "Can only assign 'arg(...)', 'group(...)', 'mutex(...)', or 'subparsers(...)' "
                    "to a field of an arguments class."
                )
            arg = value or Arg()
            add_argument(arg, ty, command, field_name, command_path, docstrings)

    if not command.disable_help_flag:
        command.arguments[_HELP_DEST] = Arg(
            arg_config=ArgConfig(action=HelpAction, dest=_HELP_DEST),
            short="-h",
            long="--help",
            about="Print help"
        )

    if not command.disable_version_flag:
        command.arguments[_VERSION_DEST] = Arg(
            arg_config=ArgConfig(action=VersionAction, dest=_VERSION_DEST),
            short="-V",
            long="--version",
            about="Print version",
        )

    setattr(cls, _COMMAND_DATA, command)
    return command


def configure_parser(parser: argparse.ArgumentParser, command: Command):
    for arg in command.arguments.values():
        if arg.group is not None or arg.mutex is not None:
            continue
        parser.add_argument(*arg.get_flags(), **arg.get_kwargs())

    # groups can have mutexes in them, so storing them temporarily in a dict
    groups = {
        group_obj: parser.add_argument_group(**group_obj.get_kwargs())
        for group_obj in command.groups
    }

    # when both group and mutex are provided for an argument, the argument is
    # only added to the mutex when the command is created
    for group, arguments in command.groups.items():
        for arg in arguments:
            groups[group].add_argument(*arg.get_flags(), **arg.get_kwargs())

    for mutex, arguments in command.mutexes.items():
        if mutex.parent is None:
            mutex_group = parser.add_mutually_exclusive_group(required=mutex.required)
        else:
            mutex_group = groups[mutex.parent].add_mutually_exclusive_group(
                required=mutex.required
            )
        for arg in arguments:
            mutex_group.add_argument(*arg.get_flags(), **arg.get_kwargs())

    if (subparser_info := command.subparsers_config) is not None:
        subparsers = parser.add_subparsers(**subparser_info.get_kwargs())
        for subcommand in command.subcommands.values():
            parser = subparsers.add_parser(
                command=subcommand, **subcommand.parser_config.get_kwargs()
            )
            configure_parser(parser, subcommand)


def create_parser(cls: type):
    command = create_command(cls)
    parser = ClapArgumentParser(command, **command.parser_config.get_kwargs())
    configure_parser(parser, command)
    return parser


def apply_parsed_arguments(args: dict[str, Any], instance: Any):
    command: Command = getattr(instance, _COMMAND_DATA)
    subcommand_args: dict[str, Any] = {}

    for attr_name, value in args.items():
        if attr_name.find('.') != -1:
            subcommand_args[attr_name.split(".", maxsplit=1)[1]] = value
        else:
            if attr_name == command.subcommand_dest:
                continue
            match command.arguments[attr_name].ty:
                case ArgType.Tuple():
                    if value is not None:
                        value = tuple(value)
                case ArgType.Enum(choice_to_enum_member=choice_to_enum_member):
                    if isinstance(value, str):
                        value = choice_to_enum_member[value]
            setattr(instance, attr_name, value)

    # no subcommands
    if command.subcommand_dest is None:
        return

    # subcommand not provided
    subcommand_name = args[command.subcommand_dest]
    if subcommand_name is None:
        if not hasattr(instance, command.subcommand_dest):
            setattr(instance, command.subcommand_dest, None)
        return

    # If an alias is used, argparse gives that instead of the subcommand name
    subcommand_name = cast(str, subcommand_name)
    subcommand_name = command.subcommand_aliases.get(subcommand_name, subcommand_name)

    # only one subcommand can be provided
    cls = command.subcommands[subcommand_name].subcommand_class
    assert cls is not None
    subcommand_instance = object.__new__(cls)
    apply_parsed_arguments(subcommand_args, subcommand_instance)
    setattr(instance, command.subcommand_dest, subcommand_instance)
