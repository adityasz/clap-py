import argparse
import ast
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
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)


# useful when help output is implemented
class ColorChoice(Enum):
    Auto = auto()
    Always = auto()
    Never = auto()


SUBCOMMAND_ATTR = "com.github.adityasz.clap_py.subcommand"
SUBCOMMAND_TITLE = "Commands"
SUBCOMMAND_KWARGS = "__subcommand_kwargs__"
COMMAND_ATTR = "com.github.adityasz.clap_py.command"
COMMAND_KWARGS = "__command_kwargs__"
PARSER_ATTR = "__parser__"

T = TypeVar('T')


class _Short:
    ...


class _Long:
    ...


@dataclass
class Group:
    name: str


@dataclass
class MutexGroup:
    parent: Optional[Group] = None


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

T = TypeVar('T')
U = TypeVar('U')


@dataclass
class _FilterKwargs:
    def get_kwargs(self) -> dict[str, Any]:
        kwargs = asdict(self)
        for k, v in kwargs.items():
            if v is None:
                kwargs.pop(k)
        return kwargs


@dataclass
class ArgparseArgumentInfo[T, U](_FilterKwargs):
    short: Optional[Union[_Short, str]] = None
    """The short flag for the argument."""
    long: Optional[Union[_Long, str]] = None
    """The long flag for the argument."""
    action: Optional[_Action] = None
    """The action to be taken when this argument is encountered."""
    nargs: Optional[_Nargs] = None
    """The number of command-line arguments that should be consumed."""
    const: Optional[U] = None
    """The constant value required by some action and nargs selections."""
    default: Optional[U] = None
    """The default value for the argument if not provided."""
    type_: Optional[type[T]] = None
    """The type to which the command-line argument should be converted."""
    choices: Optional[Sequence[str]] = None
    """A sequence of valid choices for the argument."""
    required: bool = True
    """Whether the argument is required or optional."""
    help: Optional[str] = None
    """A brief description of what the argument does."""
    metavar: Optional[str] = None
    """The name for the argument in usage messages."""
    deprecated: bool = False
    """Whether this argument is deprecated and should not be used."""


@dataclass
class Argument:
    argparse_info: ArgparseArgumentInfo = ArgparseArgumentInfo()

    group: Optional[Group] = None
    """The group for the argument."""
    mutex: Optional[MutexGroup] = None
    """The mutually exclusive group for the argument."""
    choices: Optional[list[str]] = None
    choice_to_member: Optional[dict[str, type]] = None


@dataclass
class SubcommandInfo(_FilterKwargs):
    name: Optional[str] = None
    deprecated: bool = False
    help: Optional[str] = None
    aliases: Optional[Sequence[str]] = None


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


@dataclass
class ParserInfo(_FilterKwargs):
    prog: Optional[str] = None
    usage: Optional[str] = None
    description: Optional[str] = None
    epilog: Optional[str] = None
    parents: Optional[Sequence[argparse.ArgumentParser]] = None
    formatter_class = argparse.HelpFormatter
    prefix_chars: str = "-"
    fromfile_prefix_chars: Optional[str] = None
    conflict_handler: str = "error"
    add_help: bool = True
    allow_abbrev: bool = True
    exit_on_error: bool = True


@dataclass
class Command:
    parser_info: ParserInfo
    subparser_info: Optional[SubparserInfo] = None
    """Contains kwargs for parser.add_subparsers() if the command has subcommands."""
    subcommand_info: Optional[SubcommandInfo] = None
    """Contains kwargs for subparsers.add_parser() if the command is a subcommand."""

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


# for pattern matching
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
    if (ty := type(type_hint)) is type:
        if is_subcommand(type):
            return ArgType.SubcommandDest([ty], False)
        return ArgType.Type(ty)
    if type(type_hint) is EnumType:
        choices = list(map(lambda s: s.lower().replace("_", "-"), type_hint.__members__.keys()))
        if len(set(choices)) != len(choices):
            TypeError(f"can't extract choices from '{type_hint}': bad members")
        return ArgType.Enumm(choices)
    if get_origin(type_hint) is Union:
        types = get_args(type_hint)
        required = True
        for ty in types:
            if type(ty) is None:
                required = False
        if is_subcommand_dest(types):
            return ArgType.SubcommandDest(list(types), required)
        if len(types) != 2 or required:
            raise TypeError
        return ArgType.Optional(types[0])
    if get_origin(type_hint) is list:
        return ArgType.List(get_args(type_hint)[0])
    if get_origin(type_hint) is tuple:
        types = get_args(type_hint)
        for ty in types:
            if ty != types[0]:
                raise TypeError
        return ArgType.Tuple(types[0], len(types))
    raise TypeError


def create_command(cls: type, level: int = 0) -> Command:
    def bad_annotation(message: str = "") -> NoReturn:
        raise TypeError(
            f"bad type annotation '{field_name}: {type_hint}'"
            f"{": " if message else ""}{message}"
        )

    command = Command(ParserInfo(getattr(cls, COMMAND_KWARGS)))
    command.subcommand_info = getattr(cls, SUBCOMMAND_KWARGS, None)

    docstrings: dict[str, str] = extract_docstrings(cls)

    type_hints = get_type_hints(cls)
    for field_name, type_hint in type_hints:
        try:
            ty = get_type(type_hint)
        except TypeError as e:
            bad_annotation(str(e))
        if value := getattr(cls, field_name, None):
            if isinstance(value, Group):
                if field_name in command.groups:
                    raise RuntimeError(f"group '{value.name}' already exists")
                command.groups[value] = []
                continue
            if isinstance(value, MutexGroup):
                continue
            if isinstance(value, Argument):
                arg = value
                option = False
                if arg.argparse_info.short == short:
                    arg.argparse_info.short = field_name[0]
                    option = True
                if arg.argparse_info.long == long:
                    arg.argparse_info.long = field_name.lower().replace("_", "-")
                    option = True
                match ty:
                    case ArgType.Type(type):
                        arg.argparse_info.type_ = type
                        if type is bool:
                            arg.argparse_info.action = "store_true"
                            arg.argparse_info.required = False
                    case ArgType.Enum(choices=choices, choice_to_member=choice_to_member):
                        arg.argparse_info.type_ = str
                        arg.choices = choices
                        arg.choice_to_member = choice_to_member
                    case ArgType.List(type):
                        if arg.argparse_info.nargs is None:
                            raise bad_annotation("'nargs' is missing")
                        arg.argparse_info.type_ = type
                    case ArgType.Tuple(type, n):
                        if (nargs := arg.argparse_info.nargs) is not None:
                            if nargs != n:
                                raise bad_annotation("nargs = {nargs} != {nargs}")
                        else:
                            arg.argparse_info.nargs = n
                        arg.argparse_info.type_ = type
                    case ArgType.Optional(type):
                        arg.argparse_info.type_ = type
                        if option:
                            arg.argparse_info.required = False
                        else:
                            arg.argparse_info.nargs = '?'
                    case ArgType.SubcommandDest():
                        raise bad_annotation("can't assign 'arg(...)' to subcommand destination")
                if (group := arg.group) is not None:
                    command.groups[group].append(arg)
                elif (mutex := arg.mutex) is not None:
                    command.mutexes[mutex].append(arg)
                else:
                    command.arguments.append(arg)
            if isinstance(value, SubparserInfo):
                match ty:
                    case ArgType.SubcommandDest(subcommands, required):
                        command.subcommand_dest = field_name
                        for subcommand in subcommands:
                            command.subcommands.append(create_command(subcommand, level=level + 1))
                            if command.subcommands[-1].parser_info != required:
                                raise bad_annotation("check 'required'")
                    case _:
                        bad_annotation()
        else:
            arg = Argument()
            match ty:
                case ArgType.Type(type):
                    arg.argparse_info.type_ = type
                    if type is bool:
                        arg.argparse_info.action = "store_true"
                        arg.argparse_info.required = False
                    command.arguments.append(arg)
                case ArgType.Enum(choices=choices, choice_to_member=choice_to_member):
                    arg.argparse_info.type_ = str
                    arg.choices = choices
                    arg.choice_to_member = choice_to_member
                    command.arguments.append(arg)
                case ArgType.List(type):
                    if arg.argparse_info.nargs is None:
                        raise bad_annotation("'nargs' is missing")
                    arg.argparse_info.type_ = type
                    command.arguments.append(arg)
                case ArgType.Tuple(type, n):
                    if (nargs := arg.argparse_info.nargs) is not None:
                        if nargs != n:
                            raise bad_annotation("nargs = {nargs} != {nargs}")
                    else:
                        arg.argparse_info.nargs = n
                    arg.argparse_info.type_ = type
                    command.arguments.append(arg)
                case ArgType.Optional(type):
                    arg.argparse_info.type_ = type
                    arg.argparse_info.nargs = '?'
                    command.arguments.append(arg)
                case ArgType.SubcommandDest(subcommands, required):
                    command.subcommand_dest = field_name
                    for subcommand in subcommands:
                        command.subcommands.append(create_command(subcommand, level=level + 1))
                        if command.subcommands[-1].parser_info != required:
                            raise bad_annotation("check 'required'")
    return command

def create_parser(cls: type, **kwargs):
    info = create_command(cls)
    parser = argparse.ArgumentParser()
    ...
    return parser
    ...
