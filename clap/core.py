import argparse
import ast
import builtins
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from enum import Enum, EnumType, auto
from inspect import getsource
from textwrap import dedent
from typing import (
    Any,
    Literal,
    NoReturn,
    Optional,
    Self,
    Sequence,
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


@dataclass
class _FilterKwargs:
    def get_kwargs(self) -> dict[str, Any]:
        kwargs = asdict(self)
        for k, v in kwargs.copy().items():
            if v is None:
                kwargs.pop(k)
        return kwargs


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
class ArgparseArgInfo(_FilterKwargs):
    action: Optional[ActionType] = None
    nargs: Optional[NargsType] = None
    const: Optional[Any] = None
    default: Optional[Any] = None
    type: Optional[builtins.type] = None
    choices: Optional[Sequence[str]] = None
    required: Optional[bool] = True
    help: Optional[str] = None
    metavar: Optional[str] = None
    deprecated: Optional[bool] = None
    dest: Optional[str] = None


@dataclass
class Argument:
    argparse_info: ArgparseArgInfo = field(default_factory=ArgparseArgInfo)
    """The kwargs for `parser.add_argument()`."""

    short: Optional[Union[_ShortFlag, str]] = None
    """The short flag."""
    long: Optional[Union[_LongFlag, str]] = None
    """The long flag."""
    group: Optional[Group] = None
    """The group for the argument."""
    mutex: Optional[MutexGroup] = None
    """The mutually exclusive group for the argument."""
    choice_to_enum_member: Optional[dict[str, type]] = None
    """A map from the (string) choice to the enum member."""


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
    # The following are used by subcommands:
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

    arguments: list[Argument] = field(default_factory=list)
    subcommands: list[Self] = field(default_factory=list)
    subcommand_dest: Optional[str] = None
    groups: dict[Group, list[Argument]] = field(default_factory=dict)
    mutexes: defaultdict[MutexGroup, list[Argument]] = field(
        default_factory=lambda: defaultdict(list)
    )


class DocstringExtractor(ast.NodeVisitor):
    def __init__(self):
        self.docstrings: dict[str, str] = {}

    def visit_ClassDef(self, node):
        for stmt_1, stmt_2 in zip(node.body[:-1], node.body[1:]):
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


class ArgType:
    class Base: ...

    @dataclass
    class SimpleType(Base):
        ty: type

    class Enum(Base):
        def __init__(self, enum: type):
            members = enum.__members__
            self.choices = list(map(lambda s: s.lower().replace("_", "-"), members.keys()))
            if len(set(self.choices)) != len(members):
                raise TypeError
            self.choice_to_enum_member: dict[str, type] = {
                c: m for c, m in zip(self.choices, members.values())
            }

    @dataclass
    class Optional(Base):
        ty: type

    @dataclass
    class List(Base):
        ty: type

    @dataclass
    class Tuple(Base):
        ty: type
        n: int

    @dataclass
    class SubcommandDest(Base):
        subcommands: list[type]
        required: bool


def parse_type_hint(type_hint: str) -> ArgType.Base:
    """
    Supported type annotations:

    ```python
    >>> x: T
    >>> x: Optional[T]
    >>> x: list[T]
    >>> x: tuple[T, ...]
    >>> # Subcommands:
    >>> x: C1
    >>> x: Optional[C1]
    >>> x: Union[C1, C2, ...]
    >>> x: Optional[Union[C1, C2, ...]]
    ```
    """
    if type(type_hint) is type:
        if is_subcommand(type):
            return ArgType.SubcommandDest([type_hint], False)
        return ArgType.SimpleType(type_hint)
    if type(type_hint) is EnumType:
        return ArgType.Enum(type_hint)
    origin = get_origin(type_hint)
    types = get_args(type_hint)
    if origin is Union:
        required = True
        for ty in types:
            if type(None) is ty:
                required = False
        if contains_subcommand(types):
            return ArgType.SubcommandDest(list(types), required)
        if len(types) != 2 or required:
            raise TypeError
        return ArgType.Optional(types[0])
    if origin is list:
        return ArgType.List(types[0])
    if origin is tuple:
        for ty in types:
            if ty != types[0]:
                raise TypeError
        return ArgType.Tuple(types[0], len(types))
    raise TypeError


def generate_flags(arg: Argument, field_name: str) -> bool:
    """Sets short and long flags of the argument.

    Returns:
        True if the given argument is a positional argument (no flags found),
        False otherwise.
    """
    is_positional: bool = True
    if isinstance(arg.short, str) and not arg.short.startswith("-"):
        arg.short = "-" + arg.short
        is_positional = False
    elif isinstance(arg.short, _ShortFlag):
        arg.short = "-" + field_name[0].lower()
        is_positional = False
    if isinstance(arg.long, str) and not arg.long.startswith("-"):
        arg.long = "--" + arg.long
        is_positional = False
    elif isinstance(arg.long, _LongFlag):
        arg.long = "--" + field_name.lower().replace("_", "-")
        is_positional = False
    return is_positional


def process_arg(
    arg: Argument,
    ty: ArgType.Base,
    command: Command,
    field_name: str,
    prefix: str,
    docstrings: dict[str, str],
    is_positional: bool = True,
):
    info = arg.argparse_info
    info.dest = prefix + field_name
    if info.help is None:
        info.help = docstrings.get(field_name, None)
    match ty:
        case ArgType.SimpleType(t):
            if t is bool:
                info.action = "store_true"
                info.required = False
            else:
                info.type = t
        case ArgType.Enum(choices=choices, choice_to_enum_member=choice_to_enum_member):
            info.type = str
            info.choices = choices
            arg.choice_to_enum_member = choice_to_enum_member
        case ArgType.List(t):
            if info.nargs is None:
                raise TypeError("'nargs' is missing")
            info.type = t
        case ArgType.Tuple(t, n):
            info.type = t
            if (nargs := info.nargs) is not None:
                if nargs != n:
                    raise TypeError(f"nargs = {nargs} != {n}")
            else:
                info.nargs = n
        case ArgType.Optional(t):
            info.type = t
            if is_positional:
                info.nargs = '?'
            else:
                info.required = False
        case _:
            print("panic: missed some case")
            raise TypeError
    if is_positional:
        info.required = None
        arg.long = info.dest
        info.dest = None
    if (group := arg.group) is not None:
        command.groups[group].append(arg)
    elif (mutex := arg.mutex) is not None:
        command.mutexes[mutex].append(arg)
    else:
        command.arguments.append(arg)


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
            if command.subparser_info != ty.required:
                raise TypeError("check 'required'")
        else:
            raise TypeError(f"can't assign {type(value)} to subcommand destination")
    else:
        command.subparser_info = SubparserInfo()
    for subcommand in ty.subcommands:
        command.subcommands.append(create_command(subcommand, prefix))


def create_command(cls: type, prefix: str = "") -> Command:
    command = Command(ParserInfo(**getattr(cls, _PARSER_KWARGS)))
    if getattr(cls, _SUBCOMMAND_ATTR, False):
        assert(command.parser_info.name is not None)
        prefix += command.parser_info.name + "."
        command.subcommand_class = cls

    docstrings: dict[str, str] = extract_docstrings(cls)

    type_hints = get_type_hints(cls)
    for field_name, type_hint in type_hints.items():
        try:
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
                is_positional = generate_flags(value, field_name)
                process_arg(value, ty, command, field_name, prefix, docstrings, is_positional)
            elif value is None:
                process_arg(Argument(), ty, command, field_name, prefix, docstrings)
            else:
                print("panic: missed something")
                raise TypeError
        except TypeError as e:
            raise TypeError(
                f"bad type annotation '{field_name}: {type_hint}'"
                f"{": " if str(e) else ""}{str(e)}"
            )
    return command


def setup_parser(parser: argparse.ArgumentParser, command: Command):
    for arg in command.arguments:
        flags = []
        if arg.short is not None:
            flags.append(arg.short)
        if arg.long is not None:
            flags.append(arg.long)
        kwargs = arg.argparse_info.get_kwargs()
        kwargs.setdefault("default", None)
        # print(
        #     f"parser.add_argument({', '.join(flags)}{', ' if flags else ''}"
        #     f"{', '.join(list(map(lambda k: f'{k}={kwargs[k]}', kwargs.keys())))})"
        # )
        parser.add_argument(*flags, **kwargs)

    # groups have to persist because groups can have mutexes
    groups = {group_obj: parser.add_argument_group(**group_obj.get_kwargs())
              for group_obj in command.groups.keys()}
    for group, arguments in command.groups.items():
        for arg in arguments:
            kwargs = arg.argparse_info.get_kwargs()
            kwargs.setdefault("default", None)
            groups[group].add_argument(**kwargs)

    for mutex, arguments in command.mutexes.items():
        if mutex.parent is None:
            mutex_group = parser.add_mutually_exclusive_group(required=mutex.required)
        else:
            mutex_group = groups[mutex.parent].add_mutually_exclusive_group(required=mutex.required)
        for arg in arguments:
            mutex_group.add_argument(**arg.argparse_info.get_kwargs())

    if (subparser_info := command.subparser_info) is not None:
        subparsers = parser.add_subparsers(**subparser_info.get_kwargs())
        for subcommand in command.subcommands:
            parser = subparsers.add_parser(**subcommand.parser_info.get_kwargs())
            setup_parser(parser, subcommand)


def create_parser(cls: type, **kwargs):
    command = create_command(cls)
    setattr(cls, _COMMAND_DATA, command)
    parser = argparse.ArgumentParser(**command.parser_info.get_kwargs())
    setup_parser(parser, command)
    return parser


def populate_instance_fields(args: dict[str, Any], instance: Any, depth: int = 0):
    command: Command = getattr(instance, _COMMAND_DATA)
    subcommand_args: dict[str, Any] = {}
    for attr_name, value in args.items():
        if attr_name.count('.') > depth:
            subcommand_args[attr_name] = value
        else:
            setattr(instance, attr_name, value)
    if command.subcommand_dest is None:
        # no subcommands
        return
    if command.subcommand_dest not in args:
        # subcommand not provided
        if not hasattr(instance, command.subcommand_dest):
            setattr(instance, command.subcommand_dest, None)
        return
    for subcommand in command.subcommands:
        # find the subcommand using the name
        if subcommand.parser_info.name == args[command.subcommand_dest]:
            cls = subcommand.subcommand_class
            assert(cls is not None)
            subcommand_obj = cls()
            populate_instance_fields(subcommand_args, subcommand_obj, depth + 1)
            setattr(instance, command.subcommand_dest, subcommand_obj)
            break # since only one subcommand can be provided
