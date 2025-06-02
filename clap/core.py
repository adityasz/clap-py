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

COMMAND_ATTR = "__com.github.adityasz.clap_py.command__"
SUBCOMMAND_ATTR = "__com.github.adityasz.clap_py.subcommand__"
PARSER_ATTR = "__parser__"
COMMAND_DATA = "__command_data__"
SUBCOMMAND_DEST = "__subcommand_dest__"
ARGPARSE_PARSER_KWARGS = "__argparse_parser_kwargs__"


# will be useful when help output is implemented
class ColorChoice(Enum):
    Auto = auto()
    Always = auto()
    Never = auto()


class _Short:
    ...


class _Long:
    ...


short = _Short()
"""Generate short from the first character in the case-converted field name."""

long = _Long()
"""Generate long from the case-converted field name."""

_Action = Union[
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

_Nargs = Union[Literal['?', '*', '+'], int]


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
    action: Optional[_Action] = None
    nargs: Optional[_Nargs] = None
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

    short: Optional[Union[_Short, str]] = None
    """The short flag."""
    long: Optional[Union[_Long, str]] = None
    """The long flag."""
    group: Optional[Group] = None
    """The group for the argument."""
    mutex: Optional[MutexGroup] = None
    """The mutually exclusive group for the argument."""
    choice_to_member: Optional[dict[str, type]] = None


@dataclass
class SubparserInfo(_FilterKwargs):
    title: Optional[str] = None
    description: Optional[str] = None
    prog: Optional[str] = None
    parser_class: Optional[type] = None
    action: Optional[_Action] = None
    required: bool = False
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
        ...


def extract_docstrings(cls: type):
    extractor = DocstringExtractor()
    source = dedent(getsource(cls))
    tree = ast.parse(source)
    extractor.visit(tree)
    return extractor.docstrings


def is_subcommand(cls: type) -> bool:
    return getattr(cls, SUBCOMMAND_ATTR, False)


def is_subcommand_dest(types: tuple[type]) -> bool:
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
    class Type(Base):
        ty: type

    class Enum(Base):
        def __init__(self, enum: type):
            members = enum.__members__
            self.choices = list(map(lambda s: s.lower().replace("_", "-"), members.keys()))
            if len(set(self.choices)) != len(members):
                raise TypeError
            self.choice_to_member: dict[str, type] = {
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


def get_type(type_hint: str) -> ArgType.Base:
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
        return ArgType.Type(type_hint)
    if type(type_hint) is EnumType:
        return ArgType.Enum(type_hint)
    origin = get_origin(type_hint)
    types = get_args(type_hint)
    if origin is Union:
        required = True
        for ty in types:
            if type(None) is ty:
                required = False
        if is_subcommand_dest(types):
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


def create_command(cls: type, prefix: str = "") -> Command:
    def bad_annotation(message: str = "") -> NoReturn:
        raise TypeError(
            f"bad type annotation '{field_name}: {type_hint}'"
            f"{": " if message else ""}{message}"
        )

    def process_arg(option: bool = False):
        info = arg.argparse_info
        info.dest = prefix + field_name
        if info.help is None:
            info.help = docstrings.get(field_name, None)
        match ty:
            case ArgType.Type(t):
                if t is bool:
                    info.action = "store_true"
                    info.required = False
                else:
                    info.type = t
            case ArgType.Enum(choices=choices, choice_to_member=choice_to_member):
                info.type = str
                info.choices = choices
                arg.choice_to_member = choice_to_member
            case ArgType.List(t):
                if info.nargs is None:
                    bad_annotation("'nargs' is missing")
                info.type = t
            case ArgType.Tuple(t, n):
                info.type = t
                if (nargs := info.nargs) is not None:
                    if nargs != n:
                        bad_annotation(f"nargs = {nargs} != {n}")
                else:
                    info.nargs = n
            case ArgType.Optional(t):
                info.type = t
                if option:
                    info.required = False
                else:
                    info.nargs = '?'
            case _:
                print("panic: missed some case")
                bad_annotation()
        if option is False:
            # positional argument
            info.required = None
            arg.long = info.dest
            info.dest = None
        if (group := arg.group) is not None:
            command.groups[group].append(arg)
        elif (mutex := arg.mutex) is not None:
            command.mutexes[mutex].append(arg)
        else:
            command.arguments.append(arg)

    command = Command(ParserInfo(**getattr(cls, ARGPARSE_PARSER_KWARGS)))
    if getattr(cls, SUBCOMMAND_ATTR, False):
        assert(command.parser_info.name is not None)
        prefix += command.parser_info.name + "."
        command.subcommand_class = cls
    docstrings: dict[str, str] = extract_docstrings(cls)
    type_hints = get_type_hints(cls)
    for field_name, type_hint in type_hints.items():
        try:
            ty = get_type(type_hint)
        except TypeError as e:
            bad_annotation(str(e))

        value = getattr(cls, field_name, None)
        match ty:
            case ArgType.SubcommandDest(subcommands, required):
                if command.subcommand_dest is not None:
                    bad_annotation(
                        f"{command.subcommand_dest} is already the subcommand destination"
                    )
                command.subcommand_dest = field_name
                if value is not None:
                    if isinstance(value, SubparserInfo):
                        command.subparser_info = value
                        if command.subparser_info != required:
                            bad_annotation("check 'required'")
                    else:
                        bad_annotation(f"can't assign {type(value)} to subcommand destination")
                else:
                    command.subparser_info = SubparserInfo()
                for subcommand in subcommands:
                    command.subcommands.append(create_command(subcommand, prefix))
                continue
        if value is None:
            arg = Argument()
            process_arg()
        elif isinstance(value, Group):
            if field_name in command.groups:
                raise RuntimeError(f"group '{value.title}' already exists")
            command.groups[value] = []
        elif isinstance(value, MutexGroup):
            continue
        elif isinstance(value, Argument):
            arg = value
            option = False
            if isinstance(arg.short, str) and not arg.short.startswith("-"):
                arg.short = "-" + arg.short
                option = True
            elif isinstance(arg.short, _Short):
                arg.short = "-" + field_name[0].lower()
                option = True
            if isinstance(arg.long, str) and not arg.long.startswith("-"):
                arg.long = "--" + arg.long
                option = True
            elif isinstance(arg.long, _Long):
                arg.long = "--" + field_name.lower().replace("_", "-")
                option = True
            process_arg(option)
        else:
            print("panic: missed something")
            bad_annotation()
    return command


def deal_with_argparse(parser: argparse.ArgumentParser, command: Command):
    for arg in command.arguments:
        flags = []
        if arg.short is not None:
            flags.append(arg.short)
        if arg.long is not None:
            flags.append(arg.long)
        kwargs = arg.argparse_info.get_kwargs()
        kwargs.setdefault("default", None)
        if False:
            print(
                f"parser.add_argument({', '.join(flags)}{', ' if flags else ''}"
                f"{', '.join(list(map(lambda k: f'{k}={kwargs[k]}', kwargs.keys())))})"
            )
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
            deal_with_argparse(parser, subcommand)


def create_parser(cls: type, **kwargs):
    command = create_command(cls)
    setattr(cls, COMMAND_DATA, command)
    parser = argparse.ArgumentParser(**command.parser_info.get_kwargs())
    deal_with_argparse(parser, command)
    return parser


def populate_fields(args: dict[str, Any], obj: type, level: int = 0):
    command = getattr(obj, COMMAND_DATA)
    assert(isinstance(command, Command))
    subcommand_args: dict[str, Any] = {}
    for attr_name, value in args:
        if attr_name.count('.') > level:
            subcommand_args[attr_name] = value
        else:
            setattr(obj, attr_name, value)
    if command.subcommand_dest is None:
        return
    if command.subcommand_dest not in args:
        if not hasattr(obj, command.subcommand_dest):
            setattr(obj, command.subcommand_dest, None)
        return
    for subcommand in command.subcommands:
        name = subcommand.parser_info.name
        if name == args[command.subcommand_dest]:
            cls = subcommand.subcommand_class
            assert(cls is not None)
            subcommand_obj = cls()
            populate_fields(subcommand_args, subcommand_obj, level + 1)
            setattr(obj, command.subcommand_dest, subcommand_obj)
            break # since only one subcommand can be present
