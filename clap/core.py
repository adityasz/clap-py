import argparse
import ast
import builtins
import re
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field, fields
from enum import Enum, EnumType, auto
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
_PARSER_CONFIG = "__argparse_parser_config__"


# will be useful when help output is implemented
class ColorChoice(Enum):
    Auto = auto()
    Always = auto()
    Never = auto()


class _ShortFlag:
    ...


class _LongFlag:
    ...


short = _ShortFlag()
"""Generate short from the first character in the case-converted field name."""

long = _LongFlag()
"""Generate long from the case-converted field name."""

ActionType = Union[
    argparse.Action,
    Literal[
        "store",
        "store_const",
        "store_true",
        "store_false",
        "append",
        "append_const",
        "extend",
        "count",
        "help",
        "version"
    ]
]


NargsType = Union[Literal['?', '*', '+'], int]


class ArgType:
    class Base: ...

    @dataclass
    class SimpleType(Base):
        ty: type
        optional: bool

    class Enum(Base):
        def __init__(self, enum: type, optional: bool):
            self.enum = enum
            members = enum.__members__
            self.choices = list(
                map(to_kebab_case, members.keys())
            )
            if len(set(self.choices)) != len(members):
                raise TypeError
            self.choice_to_enum_member: dict[str, type] = {
                c: m for c, m in zip(self.choices, members.values(), strict=False)
            }
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
class ArgparseConfig(ConfigBase):
    action: Optional[ActionType] = None
    nargs: Optional[NargsType] = None
    const: Optional[Any] = None
    default: Optional[Any] = None
    type: Optional[builtins.type] = None
    choices: Optional[Sequence[str]] = None
    required: Optional[bool] = None
    help: Optional[str] = None
    metavar: Optional[str] = None
    deprecated: Optional[bool] = None
    dest: Optional[str] = None


@dataclass
class Argument:
    argparse_config: ArgparseConfig = field(default_factory=ArgparseConfig)
    """The kwargs for `parser.add_argument()`."""

    short: Optional[Union[_ShortFlag, str]] = None
    """The short flag."""
    long: Optional[Union[_LongFlag, str]] = None
    """The long flag."""
    is_positional: bool = False
    """True if positional argument."""
    ty: Optional[ArgType.Base] = None
    """Stores type information for the argument."""
    group: Optional[Group] = None
    """The group for the argument."""
    mutex: Optional[MutexGroup] = None
    """The mutually exclusive group for the argument."""

    def __repr__(self):
        attrs = []

        if self.short is not None:
            attrs.append(f'"{self.short}"' if isinstance(self.short, str) else "short")
        if self.long is not None:
            attrs.append(f'"{self.long}"' if isinstance(self.long, str) else "long")

        for attr, val in self.argparse_config.get_kwargs().items():
            attrs.append(f"{attr}={val}")

        for f in fields(self):
            if (
                f.name not in ("arg_kwargs", "short", "long", "ty")
                and (value := getattr(self, f.name)) is not None
            ):
                attrs.append(f"{f.name}={value}")

        return f"{self.__class__.__name__}({", ".join(attrs)})"

    def get_flags(self) -> list[str]:
        flags = []
        if self.short is not None:
            flags.append(self.short)
        if self.long is not None:
            flags.append(self.long)
        return flags

    def get_kwargs(self) -> dict[str, Any]:
        kwargs = self.argparse_config.get_kwargs()
        # argparse does not add an argument to the `argparse.Namespace` that
        # `argparse.ArgumentParser.parser_args()` returns unless it has a value.
        # So, to get everything, set default value to None if not already set.
        kwargs.setdefault("default", None)
        return kwargs


@dataclass
class SubparsersConfig(ConfigBase):
    title: Optional[str] = None
    description: Optional[str] = None
    prog: Optional[str] = None
    parser_class: Optional[type] = None
    action: Optional[ActionType] = None
    required: Optional[bool] = None
    help: Optional[str] = None
    metavar: Optional[str] = None
    dest: Optional[str] = None


@dataclass
class ParserConfig(ConfigBase):
    prog: Optional[str] = None
    usage: Optional[str] = None
    description: Optional[str] = None
    epilog: Optional[str] = None
    parents: Optional[Sequence[argparse.ArgumentParser]] = None
    formatter_class = None
    prefix_chars: Optional[str] = None
    fromfile_prefix_chars: Optional[str] = None
    conflict_handler: Optional[str] = None
    add_help: Optional[bool] = None
    allow_abbrev: Optional[bool] = None
    exit_on_error: Optional[bool] = None
    # The following are used by subcommands (subparsers.add_parser()):
    name: Optional[str] = None
    deprecated: Optional[bool] = None
    help: Optional[str] = None
    aliases: Optional[Sequence[str]] = None


@dataclass
class Command:
    parser_config: ParserConfig
    """Contains kwargs for argparse.ArgumentParser() and subparsers.add_parser()."""
    subparsers_config: Optional[SubparsersConfig] = None
    """Contains kwargs for parser.add_subparsers() if the command has subcommands."""
    subcommand_class: Optional[type] = None
    """Contains the class if the command is a subcommand."""

    arguments: dict[str, Argument] = field(default_factory=dict)
    subcommands: dict[str, Self] = field(default_factory=dict)
    subcommand_aliases: dict[str, str] = field(default_factory=dict)
    subcommand_dest: Optional[str] = None
    groups: dict[Group, list[Argument]] = field(default_factory=dict)
    mutexes: defaultdict[MutexGroup, list[Argument]] = field(
        default_factory=lambda: defaultdict(list)
    )
    convert_to_tuple: set[str] = field(default_factory=set)


def is_subcommand(cls: type) -> bool:
    return getattr(cls, _SUBCOMMAND_MARKER, False)


def contains_subcommands(types: list[type]) -> bool:
    flag = None
    for ty in types:
        if is_subcommand(ty):
            if flag is False:
                raise TypeError
            flag = True
        else:
            if flag is True:
                raise TypeError
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
                self.docstrings[stmt_1.target.id] = stmt_2.value.value
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
            raise TypeError
        if type(None) is types[0]:
            return parse_type_hint(types[1], True)
        elif type(None) is types[1]:
            return parse_type_hint(types[0], True)
    if origin is list:
        return ArgType.List(types[0], optional)
    if origin is tuple:
        for ty in types:
            if ty != (types[0]):
                raise TypeError
        if (n := len(types)) == 1:
            raise TypeError
        return ArgType.Tuple(types[0], n, optional)
    raise TypeError


def configure_flags(arg: Argument, field_name: str):
    """Sets short and long flags of the argument."""
    if isinstance(arg.short, _ShortFlag):
        arg.short = "-" + field_name[0].lower()
    elif isinstance(arg.short, str) and not arg.short.startswith("-"):
        arg.short = "-" + arg.short

    if isinstance(arg.long, _LongFlag):
        arg.long = "--" + to_kebab_case(field_name)
    elif isinstance(arg.long, str) and not arg.long.startswith("-"):
        arg.long = "--" + arg.long


def configure_action_behavior(arg: Argument, optional_type_hint: bool):
    kwargs = arg.argparse_config

    match kwargs.action:
        case "append" | "append_const" | "extend":
            if not optional_type_hint and not kwargs.default:
                kwargs.default = []
            if kwargs.required is None:
                kwargs.required = False
        case "count":
            if kwargs.default is None:
                kwargs.default = 0
            if kwargs.required is None:
                kwargs.required = False
            if optional_type_hint:
                raise TypeError
        case "store":
            if kwargs.required is not None:
                if kwargs.required and optional_type_hint:
                    raise TypeError
                return
            if kwargs.default is not None and optional_type_hint:
                raise TypeError
            if kwargs.default is None:
                kwargs.required = not optional_type_hint
        case "store_const":
            if kwargs.default is not None:
                if optional_type_hint:
                    raise TypeError
                kwargs.required = False
            if kwargs.required is None:
                kwargs.required = not optional_type_hint
        case "store_false":
            if optional_type_hint:
                raise TypeError
            if kwargs.default is None:
                kwargs.default = True
            if kwargs.required is None:
                kwargs.required = False
        case "store_true":
            if optional_type_hint:
                raise TypeError
            if kwargs.default is None:
                kwargs.default = False
            if kwargs.required is None:
                kwargs.required = False

    if arg.is_positional:
        if optional_type_hint:
            if (nargs := kwargs.nargs) is not None and nargs != '?':
                raise TypeError
            kwargs.nargs = '?'
        kwargs.required = None

    if kwargs.action in ("store_const", "append_const", "count", "store_true", "store_false"):
        kwargs.type = None


def configure_argument(
    arg: Argument,
    ty: ArgType.Base,
    command: Command,
    field_name: str,
    command_path: str,
    docstrings: dict[str, str],
):
    configure_flags(arg, field_name)

    arg.ty = ty
    kwargs = arg.argparse_config
    if arg.short is None and arg.long is None:
        arg.is_positional = True
        arg.long = command_path + field_name
    else:
        kwargs.dest = command_path + field_name
    if kwargs.help is None:
        kwargs.help = docstrings.get(field_name)

    match ty:
        case ArgType.SimpleType(t):
            if t is bool:
                if kwargs.action is None:
                    kwargs.action = "store_true"
            else:
                if kwargs.action is None:
                    kwargs.action = "store"
                kwargs.type = t
        case ArgType.Enum(choices=choices):
            if kwargs.action is None:
                kwargs.action = "store"
            kwargs.type = str
            kwargs.choices = choices
        case ArgType.List(t):
            if kwargs.action is None:
                kwargs.action = "store"
            if kwargs.nargs is None and kwargs.action == "store":
                kwargs.nargs = "*"
            kwargs.type = t
        case ArgType.Tuple(t, n):
            if kwargs.action is None:
                kwargs.action = "store"
            command.convert_to_tuple.add(field_name)
            kwargs.type = t
            if (nargs := kwargs.nargs) is not None:
                if nargs != n:
                    raise TypeError(f"nargs = {nargs} != {n}")
            else:
                kwargs.nargs = n
        case _:
            raise TypeError

    configure_action_behavior(arg, ty.optional)

    command.arguments[field_name] = arg

    if (mutex := arg.mutex) is not None:
        if (group := arg.group) is not None and mutex.parent != group:
            raise ValueError
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
            f"{command.subcommand_dest} is already the subcommand destination"
        )
    command.subcommand_dest = field_name
    if value is not None:
        if isinstance(value, SubparserInfo):
            command.subparser_info = value
            if command.subparser_info.required == ty.optional:
                raise TypeError("check 'required'")
        else:
            raise TypeError(f"can't assign {type(value)} to subcommand destination")
    else:
        command.subparsers_config = SubparsersConfig()
        command.subparsers_config.required = not ty.optional
    # if dest is not provided to add_subparsers(), argparse does not give the
    # command name, and if a subcommand shares a flag name with the command and
    # the flag is provided for both of them, argparse simply overwrites it in
    # the output (argparse.Namespace)
    command.subparsers_config.dest = command_path + command.subcommand_dest
    for cmd in ty.subcommands:
        subcommand = create_command(cmd, command_path)
        name = subcommand.parser_config.name
        assert name is not None
        command.subcommands[name] = subcommand
        if subcommand.parser_config.aliases:
            for alias in subcommand.parser_config.aliases:
                command.subcommand_aliases[alias] = name


def create_command(cls: type, command_path: str = "") -> Command:
    command = Command(ParserConfig(**getattr(cls, _PARSER_CONFIG)))

    if getattr(cls, _SUBCOMMAND_MARKER, False):
        assert command.parser_config.name is not None
        command_path += command.parser_config.name + "."
        command.subcommand_class = cls

    for field_name in dir(cls):
        value = getattr(cls, field_name, None)
        if isinstance(value, Group):
            if value in command.groups:
                raise ValueError
            command.groups[value] = []

    docstrings: dict[str, str] = extract_docstrings(cls)
    type_hints = get_type_hints(cls)

    for field_name, type_hint in type_hints.items():
        ty = parse_type_hint(type_hint)
        value = getattr(cls, field_name, None)
        if isinstance(ty, ArgType.SubcommandDest):
            configure_subcommands(ty, command, value, field_name, command_path)
        elif isinstance(value, Group):
            continue  # already handled in the previous loop
        elif isinstance(value, MutexGroup):
            continue  # nothing to do
        elif isinstance(value, Argument):
            configure_argument(value, ty, command, field_name, command_path, docstrings)
        elif value is None:
            configure_argument(Argument(), ty, command, field_name, command_path, docstrings)
        else:
            raise TypeError

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
            kwargs = arg.argparse_config.get_kwargs()
            kwargs.setdefault("default", None)
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
            parser = subparsers.add_parser(**subcommand.parser_config.get_kwargs())
            configure_parser(parser, subcommand)


def create_parser(cls: type, **kwargs):
    command = create_command(cls)
    parser = argparse.ArgumentParser(**command.parser_config.get_kwargs())
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

    # If an alias is used, argparse gives that instead of the subcommand name!
    # head-exploding-emoji
    # (If dest is not provided to add_subparsers(), it does not even tell
    # which command was provided!)
    subcommand_name = cast(str, subcommand_name)
    subcommand_name = command.subcommand_aliases.get(subcommand_name, subcommand_name)

    # only one subcommand can be provided
    cls = command.subcommands[subcommand_name].subcommand_class
    assert cls is not None
    subcommand_instance = cls()
    apply_parsed_arguments(subcommand_args, subcommand_instance)
    setattr(instance, command.subcommand_dest, subcommand_instance)
