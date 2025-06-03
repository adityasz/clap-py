import argparse
import ast
import builtins
import re
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from enum import Enum, EnumType, auto
from inspect import getsource
from textwrap import dedent
from typing import (
    Any,
    Literal,
    Optional,
    Self,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

_COMMAND_ATTR = "__com.github.adityasz.clap_py.command__"
_SUBCOMMAND_ATTR = "__com.github.adityasz.clap_py.subcommand__"
_PARSER_ATTR = "__parser__"
_COMMAND_DATA = "__command_data__"
_SUBCOMMAND_DEST = "__subcommand_dest__"
_PARSER_KWARGS = "__argparse_parser_kwargs__"


# will be useful when help output is implemented
class ColorChoice(Enum):
    Auto = auto()
    Always = auto()
    Never = auto()


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


def extract_docstrings(cls: type) -> dict[str, str]:
    extractor = DocstringExtractor()
    source = dedent(getsource(cls))
    tree = ast.parse(source)
    extractor.visit(tree)
    return extractor.docstrings


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
            members = enum.__members__
            self.choices = list(
                map(lambda s: s.lower().replace("_", "-"), members.keys())
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
class _FilterKwargs:
    def get_kwargs(self) -> dict[str, Any]:
        kwargs = asdict(self)
        res = {}
        for k, v in kwargs.items():
            if v is not None:
                res[k] = v
        return res


@dataclass
class Group(_FilterKwargs):
    title: Optional[str] = None
    description: Optional[str] = None
    prefix_chars: Optional[str] = None
    conflict_handler: Optional[str] = None


@dataclass
class MutexGroup:
    parent: Optional[Group] = None
    required: bool = False


@dataclass
class ArgKwargs(_FilterKwargs):
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
    arg_kwargs: ArgKwargs = field(default_factory=ArgKwargs)
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


@dataclass
class SubparserInfo(_FilterKwargs):
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
class ParserInfo(_FilterKwargs):
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
    parser_info: ParserInfo
    """Contains kwargs for argparse.ArgumentParser() and subparsers.add_parser()."""
    subparser_info: Optional[SubparserInfo] = None
    """Contains kwargs for parser.add_subparsers() if the command has subcommands."""
    subcommand_class: Optional[type] = None
    """Contains the class if the command is a subcommand."""

    arguments: dict[str, Argument] = field(default_factory=dict)
    subcommands: dict[str, Self] = field(default_factory=dict)
    subcommand_dest: Optional[str] = None
    groups: dict[Group, list[Argument]] = field(default_factory=dict)
    mutexes: defaultdict[MutexGroup, list[Argument]] = field(
        default_factory=lambda: defaultdict(list)
    )
    convert_to_tuple: set[str] = field(default_factory=set)


def is_subcommand(cls: type) -> bool:
    return getattr(cls, _SUBCOMMAND_ATTR, False)


def contains_subcommand(types: tuple[type]) -> bool:
    flag = None
    for ty in types:
        if type(ty) is None:
            continue
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


def parse_type_hint(type_hint: Any, optional: bool = False) -> ArgType.Base:
    if type(type_hint) is type:
        if is_subcommand(type):
            return ArgType.SubcommandDest([type_hint], optional)
        return ArgType.SimpleType(type_hint, optional)
    if type(type_hint) is EnumType:
        return ArgType.Enum(type_hint, optional)
    origin = get_origin(type_hint)
    types = get_args(type_hint)
    if origin is Union:
        for ty in types:
            if type(None) is ty:
                optional = True
        if contains_subcommand(types):
            return ArgType.SubcommandDest(list(types), optional)
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


def setup_flags(arg: Argument, field_name: str):
    """Sets short and long flags of the argument."""
    if isinstance(arg.short, _ShortFlag):
        arg.short = "-" + field_name[0].lower()
    elif isinstance(arg.short, str) and not arg.short.startswith("-"):
        arg.short = "-" + arg.short

    if isinstance(arg.long, _LongFlag):
        arg.long = "--" + field_name.lower().replace("_", "-")
    elif isinstance(arg.long, str) and not arg.long.startswith("-"):
        arg.long = "--" + arg.long


def set_required(arg: Argument, optional_type_hint: bool):
    kwargs = arg.arg_kwargs

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


def process_arg(
    arg: Argument,
    ty: ArgType.Base,
    command: Command,
    field_name: str,
    prefix: str,
    docstrings: dict[str, str],
):
    setup_flags(arg, field_name)

    arg.ty = ty
    kwargs = arg.arg_kwargs
    if arg.short is None and arg.long is None:
        arg.is_positional = True
        arg.long = prefix + field_name
    else:
        kwargs.dest = prefix + field_name
    if kwargs.help is None:
        kwargs.help = docstrings.get(field_name)
    if kwargs.action is None:
        kwargs.action = "store"

    match ty:
        case ArgType.SimpleType(t):
            if t is bool:
                if kwargs.action is None:
                    kwargs.action = "store_true"
            else:
                kwargs.type = t
        case ArgType.Enum(choices=choices):
            kwargs.type = str
            kwargs.choices = choices
        case ArgType.List(t):
            if kwargs.nargs is None and kwargs.action == "store":
                kwargs.nargs = "*"
            kwargs.type = t
        case ArgType.Tuple(t, n):
            command.convert_to_tuple.add(field_name)
            kwargs.type = t
            if (nargs := kwargs.nargs) is not None:
                if nargs != n:
                    raise TypeError(f"nargs = {nargs} != {n}")
            else:
                kwargs.nargs = n
        case _:
            raise TypeError

    set_required(arg, ty.optional)

    if kwargs.action in ("store_const", "append_const", "count"):
        kwargs.type = None

    if (group := arg.group) is not None:
        command.groups[group].append(arg)
    elif (mutex := arg.mutex) is not None:
        command.mutexes[mutex].append(arg)
    else:
        command.arguments[field_name] = arg


def process_subcommand_dest(
    ty: ArgType.SubcommandDest,
    command: Command,
    value: Any,
    field_name: str,
    prefix: str,
):
    if command.subcommand_dest is not None:
        raise TypeError(
            f"{command.subcommand_dest} is already the subcommand destination"
        )
    command.subcommand_dest = field_name
    if value is not None:
        if isinstance(value, SubparserInfo):
            command.subparser_info = value
            if command.subparser_info != ty.optional:
                raise TypeError("check 'required'")
        else:
            raise TypeError(f"can't assign {type(value)} to subcommand destination")
    else:
        command.subparser_info = SubparserInfo()
    for cmd in ty.subcommands:
        subcommand = create_command(cmd, prefix)
        name = subcommand.parser_info.name
        assert name is not None
        command.subcommands[name] = subcommand


def create_command(cls: type, prefix: str = "") -> Command:
    command = Command(ParserInfo(**getattr(cls, _PARSER_KWARGS)))
    if getattr(cls, _SUBCOMMAND_ATTR, False):
        assert command.parser_info.name is not None
        prefix += command.parser_info.name + "."
        command.subcommand_class = cls

    docstrings: dict[str, str] = extract_docstrings(cls)

    type_hints = get_type_hints(cls)
    for field_name, type_hint in type_hints.items():
        ty = parse_type_hint(type_hint)
        value = getattr(cls, field_name, None)
        if isinstance(ty, ArgType.SubcommandDest):
            process_subcommand_dest(ty, command, value, field_name, prefix)
        elif isinstance(value, Group):
            if field_name in command.groups:
                raise RuntimeError(f"group '{value.title}' already exists")
            command.groups[value] = []
        elif isinstance(value, MutexGroup):
            continue
        elif isinstance(value, Argument):
            process_arg(value, ty, command, field_name, prefix, docstrings)
        elif value is None:
            process_arg(Argument(), ty, command, field_name, prefix, docstrings)
        else:
            raise TypeError
    return command


def setup_parser(parser: argparse.ArgumentParser, command: Command):
    for arg in command.arguments.values():
        flags = []
        if arg.short is not None:
            flags.append(arg.short)
        if arg.long is not None:
            flags.append(arg.long)
        kwargs = arg.arg_kwargs.get_kwargs()
        kwargs.setdefault("default", None)
        parser.add_argument(*flags, **kwargs)

    # groups have to persist because groups can have mutexes
    groups = {
        group_obj: parser.add_argument_group(**group_obj.get_kwargs())
        for group_obj in command.groups
    }
    for group, arguments in command.groups.items():
        for arg in arguments:
            kwargs = arg.arg_kwargs.get_kwargs()
            kwargs.setdefault("default", None)
            groups[group].add_argument(**kwargs)

    for mutex, arguments in command.mutexes.items():
        if mutex.parent is None:
            mutex_group = parser.add_mutually_exclusive_group(required=mutex.required)
        else:
            mutex_group = groups[mutex.parent].add_mutually_exclusive_group(
                required=mutex.required
            )
        for arg in arguments:
            mutex_group.add_argument(**arg.arg_kwargs.get_kwargs())

    if (subparser_info := command.subparser_info) is not None:
        subparsers = parser.add_subparsers(**subparser_info.get_kwargs())
        for subcommand in command.subcommands.values():
            parser = subparsers.add_parser(**subcommand.parser_info.get_kwargs())
            setup_parser(parser, subcommand)


def create_parser(cls: type, **kwargs):
    command = create_command(cls)
    setattr(cls, _COMMAND_DATA, command)
    parser = argparse.ArgumentParser(**command.parser_info.get_kwargs())
    setup_parser(parser, command)
    return parser


def populate_instance_fields(args: dict[str, Any], instance: Any):
    command: Command = getattr(instance, _COMMAND_DATA)
    subcommand_args: dict[str, Any] = {}

    for attr_name, value in args.items():
        if attr_name.find('.') != -1:
            subcommand_args[attr_name.split(".", maxsplit=1)[1]] = value
        else:
            match command.arguments[attr_name].ty:
                case ArgType.Tuple():
                    if value is not None:
                        value = tuple(value)
                case ArgType.Enum(enum=enum, choice_to_enum_member=choice_to_enum_member):
                    if value is not None:
                        value = enum[choice_to_enum_member[value]]
            setattr(instance, attr_name, value)

    # no subcommands
    if command.subcommand_dest is None:
        return

    # subcommand not provided
    if command.subcommand_dest not in args:
        if not hasattr(instance, command.subcommand_dest):
            setattr(instance, command.subcommand_dest, None)
        return

    # only one subcommand can be provided
    cls = command.subcommands[command.subcommand_dest].subcommand_class
    assert cls is not None
    subcommand_instance = cls()
    populate_instance_fields(subcommand_args, subcommand_instance)
    setattr(instance, command.subcommand_dest, subcommand_instance)
