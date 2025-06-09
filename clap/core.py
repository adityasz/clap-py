# TODO: Add support for argparse.Action

import argparse
import ast
import re
import sys
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
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

HELP_TEMPLATE = """\
{before-help}{about-with-newline}
{usage-heading} {usage}

{all-args}{after-help}\
"""


class AutoFlag(Enum):
    Short = auto()
    Long = auto()


class ArgAction(StrEnum):
    Set = "store"
    SetTrue = "store_true"
    SetFalse = "store_false"
    Append = "append"
    Extend = "extend"
    Count = "count"

    class Version(argparse.Action):
        def __init__(self, option_strings, dest, **kwargs):
            super().__init__(option_strings, dest, nargs=0)

        def __call__(self, parser, namespace, values, option_string=None):
            parser = cast(ClapArgParser, parser)
            parser.print_version()
            sys.exit(0)

    class Help(argparse.Action):
        def __init__(self, option_strings, dest, **kwargs):
            super().__init__(option_strings, dest, nargs=0)

        def __call__(self, parser, namespace, values, option_string=None):
            import sys
            parser = cast(ClapArgParser, parser)
            if isinstance(option_string, str) and len(option_string) == 2:
                parser.print_short_help()
            else:
                parser.print_long_help()
            sys.exit(0)

    class HelpShort(argparse.Action):
        def __init__(self, option_strings, dest, **kwargs):
            super().__init__(option_strings, dest, nargs=0)

        def __call__(self, parser, namespace, values, option_string=None):
            parser = cast(ClapArgParser, parser)
            parser.print_short_help()
            sys.exit(0)

    class HelpLong(argparse.Action):
        def __init__(self, option_strings, dest, **kwargs):
            super().__init__(option_strings, dest, nargs=0)

        def __call__(self, parser, namespace, values, option_string=None):
            parser = cast(ClapArgParser, parser)
            parser.print_long_help()
            sys.exit(0)


short = AutoFlag.Short
"""Generate short from the first character in the case-converted field name."""
long = AutoFlag.Long
"""Generate long from the case-converted field name."""

type NargsType = Union[Literal['?', '*', '+'], int]


class ArgType:
    @dataclass
    class Base:
        ty: type
        optional: bool

    @dataclass
    class SimpleType(Base): ...

    @dataclass
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

    @dataclass
    class List(Base): ...

    @dataclass
    class Tuple(Base):
        n: int

    @dataclass
    class SubcommandDest(Base):
        subcommands: list[type]
        ty: type = field(init=False)

        # TODO: this is ugly; figure out a better pattern matching scheme
        def __post_init__(self):
            self.ty = type(None)


@dataclass
class Group:
    title: str
    description: Optional[str] = None
    prefix_chars: Optional[str] = None
    conflict_handler: Optional[str] = None

    def __hash__(self):
        return hash((self.title, self.description))

    def get_argparse_kwargs(self):
        kwargs = {}
        kwargs.update({
            k: v
            for k, v in {
                "title": self.title,
                "description": self.description,
                "prefix_chars": self.prefix_chars,
                "conflict_handler": self.conflict_handler,
            }.items()
            if v is not None
        })
        return kwargs


@dataclass
class MutexGroup:
    parent: Optional[Group] = None
    required: bool = False

    def __hash__(self):
        return hash(id(self))


@dataclass
class Arg:
    short: Optional[Union[AutoFlag, str]] = None
    """The short flag."""
    long: Optional[Union[AutoFlag, str]] = None
    """The long flag."""
    about: Optional[str] = None
    long_about: Optional[str] = None
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
            kwargs.pop("required", None)
            kwargs.pop("dest")

            if self.required is False:
                if self.num_args is not None and self.num_args != "?":
                    raise TypeError(
                        "A positional argument with 'num_args != ?' can never be None; an empty list "
                        "is returned when no argument is provided with 'num_args' is 0 or *."
                    )
                kwargs["nargs"] = "?"

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


@dataclass
class Command:
    name: str
    aliases: Sequence[str] = field(default_factory=list)
    usage: Optional[str] = None
    version: Optional[str] = None
    about: Optional[str] = None
    long_about: Optional[str] = None
    before_help: Optional[str] = None
    after_help: Optional[str] = None
    subcommand_help_heading: str = "Commands"
    subcommand_value_name: str = "COMMAND"
    disable_version_flag: bool = False
    disable_help_flag: bool = False
    disable_help_subcommand: bool = False
    heading_ansi_prefix: str = "\033[1;4m"
    argument_ansi_prefix: str = "\033[1m"

    args: dict[str, Arg] = field(default_factory=dict)
    groups: dict[Group, list[Arg]] = field(default_factory=dict)
    mutexes: defaultdict[MutexGroup, list[Arg]] = field(default_factory=lambda: defaultdict(list))

    subcommand_class: Optional[type] = None
    """Contains the class if it is a subcommand."""

    subcommands: dict[str, Self] = field(default_factory=dict)
    subcommand_dest: Optional[str] = None
    subparser_dest: Optional[str] = None
    subcommand_required: bool = False

    prefix_chars: str = "-"
    fromfile_prefix_chars: Optional[str] = None
    conflict_handler: Optional[str] = None
    allow_abbrev: Optional[bool] = None
    exit_on_error: Optional[bool] = None
    deprecated: Optional[bool] = None

    def generate_usage(self, usage_prefix: str = ""):
        if self.usage is not None:
            return self.usage
        self.usage = ""
        if usage_prefix:
            self.usage = usage_prefix + " "
        self.usage += usage_prefix + self.name
        if any(arg.required is not True and not arg.is_positional() for arg in self.args.values()):
            self.usage += " [OPTIONS]"
        for arg in self.args.values():
            if arg.required is True and not arg.is_positional():
                self.usage += f" {arg.long or arg.short} {arg.value_name}"
        for mutex, args in self.mutexes.items():
            if mutex.required:
                self.usage += " <"
            self.usage += " | ".join(f"{arg.short or arg.long} {arg.value_name}" for arg in args)
            self.usage += ">"
        for arg in self.args.values():
            if arg.is_positional():
                self.usage += f" {arg.value_name}"
        if self.contains_subcommands():
            for subcommand in self.subcommands.values():
                subcommand.generate_usage(self.usage)
            if self.subcommand_required is True:
                value_name = f"<{self.subcommand_value_name}>"
            else:
                value_name = f"[{self.subcommand_value_name}]"
            self.usage += f" {value_name}"
        return self.usage

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


class ClapArgParser(argparse.ArgumentParser):
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


def parse_type_hint(type_hint: Any, optional: bool = False) -> ArgType.Base:
    if type(type_hint) is type:
        if is_subcommand(type_hint):
            return ArgType.SubcommandDest(optional, [type_hint])
        return ArgType.SimpleType(type_hint, optional)
    if type(type_hint) is EnumType:
        return ArgType.Enum(optional, type_hint)
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
            return ArgType.SubcommandDest(optional, subcommands)
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
        return ArgType.Tuple(types[0], optional, len(types))
    raise TypeError(f"Could not parse {type_hint}.")


def set_flags(arg: Arg, field_name: str, prefix_chars: str):
    """Sets short and long flags of the argument."""
    if arg.short == short:
        arg.short = prefix_chars[0] + field_name[0].lower()

    if arg.long == long:
        arg.long = 2 * prefix_chars[0] + to_kebab_case(field_name)


def set_type_dependent_kwargs(arg: Arg):
    match arg.ty:
        case ArgType.SimpleType(t):
            if t is bool:
                if arg.action is None:
                    arg.action = ArgAction.SetTrue
            else:
                if arg.action is None:
                    arg.action = ArgAction.Set
        case ArgType.Enum(enum=enum, choice_to_enum_member=choice_to_enum_member):
            if arg.action is None:
                arg.action = ArgAction.Set
            arg.choices = list(choice_to_enum_member.keys())
            if isinstance(arg.default_value, enum):
                for choice, member in choice_to_enum_member.items():
                    if member == arg.default_value:
                        arg.default_value = choice  # set default to a string for help message
        case ArgType.List(t):
            if arg.action is None:
                arg.action = ArgAction.Set
            if arg.num_args is None and arg.action in (ArgAction.Set, ArgAction.Extend):
                arg.num_args = "*"
        case ArgType.Tuple(t, _, n):
            if arg.action is None:
                arg.action = ArgAction.Set
            if (num_args := arg.num_args) is not None:
                if num_args != n:
                    raise TypeError(
                        f"The tuple has {n} values but 'num_args' is set to {num_args}."
                    )
            else:
                arg.num_args = n
        case _:
            raise TypeError("An unknown error occurred.")


def set_default_and_required(arg: Arg):
    assert arg.ty is not None
    optional_type_hint = arg.ty.optional

    match arg.action:
        case ArgAction.Append:
            if not optional_type_hint and not arg.default_value:
                arg.default_value = []
        case ArgAction.Extend:
            if not optional_type_hint and not arg.default_value:
                arg.default_value = []
        case ArgAction.Count:
            if arg.default_value is None:
                arg.default_value = 0
            if optional_type_hint:
                raise TypeError(
                    "An argument with the 'count' action cannot be None. If no default is "
                    "provided, it is set to 0."
                )
        case ArgAction.Set:
            if arg.required is not None:
                if arg.required and optional_type_hint:
                    raise TypeError("An argument with 'required=True' can never be None.")
                return
            if arg.default_value is not None and optional_type_hint:
                raise TypeError("An argument with a default value can never be None.")
            if arg.default_value is None:
                arg.required = not optional_type_hint
        case ArgAction.SetFalse:
            if optional_type_hint:
                raise TypeError("An argument with the 'store_false' action can never be None.")
            if arg.default_value is None:
                arg.default_value = True
        case ArgAction.SetTrue:
            if optional_type_hint:
                raise TypeError("An argument with the 'store_true' action can never be None.")
            if arg.default_value is None:
                arg.default_value = False


def set_value_name(arg: Arg, field_name: str):
    if arg.value_name is None:
        arg.value_name = field_name.upper()

    match arg.num_args:
        case '?':
            arg.value_name = f"[{arg.value_name}]"
        case '*':
            arg.value_name = f"[<{arg.value_name}>...]"
        case '+':
            arg.value_name = f"<{arg.value_name}>..."
        case int(n):
            arg.value_name = " ".join(f"<{arg.value_name}>" for _ in range(n))
        case None:
            match arg.action:
                case ArgAction.Set | ArgAction.Append | ArgAction.Extend:
                    arg.value_name = f"<{arg.value_name}>"
                case _:
                    arg.value_name = None


def add_argument(
    arg: Arg,
    ty: ArgType.Base,
    command: Command,
    field_name: str,
    command_path: str,
    docstrings: dict[str, str],
):
    arg.ty = ty
    arg.dest = command_path + field_name
    docstring = docstrings.get(field_name)
    if docstring is not None:
        if arg.about is None:
            arg.about = get_about_from_docstring(docstring)
        if arg.long_about is None:
            arg.long_about = docstring

    set_flags(arg, field_name, command.prefix_chars)

    set_type_dependent_kwargs(arg)

    set_default_and_required(arg)

    set_value_name(arg, field_name)

    command.args[field_name] = arg

    if (group := arg.group) is not None:
        command.groups[group].append(arg)
    if (mutex := arg.mutex) is not None:
        if (group := arg.group) is not None and mutex.parent != group:
            raise ValueError(
                "The mutex group's parent group ('{}') is different from this "
                "argument's group ('{}'). It is not necessary to provide the "
                "group when the mutex group is already provided because the "
                "mutex group's parent must be the given group."
            )
        command.mutexes[mutex].append(arg)


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
    if value is not None:
        raise TypeError(
            f"{field_name} is a subcommand destination based on the annotation; "
            f"cannot assign {type(value)} to it."
        )
    command.subcommand_required = not ty.optional
    command.subcommand_dest = field_name
    # if dest is not provided to add_subparsers(), argparse does not give the
    # command name, and if a subcommand shares a flag name with the command and
    # the flag is provided for both of them, argparse simply overwrites it in
    # the output (argparse.Namespace)
    command.subparser_dest = command_path + field_name
    for cmd in ty.subcommands:
        subcommand = create_command(cmd, command_path)
        name = subcommand.name
        command.subcommands[name] = subcommand


def create_command(cls: type, command_path: str = "") -> Command:
    command: Command = getattr(cls, _COMMAND_DATA)

    if getattr(cls, _SUBCOMMAND_MARKER, False):
        command_path += command.name + "."
        command.subcommand_class = cls

    for field_name in dir(cls):
        value = getattr(cls, field_name, None)
        if isinstance(value, Group):
            if value in command.groups:
                raise ValueError(
                    f"A group with title '{value.title}' and the same description already exists."
                )
            command.groups[value] = []
        if isinstance(value, Arg) and value.action in (
            ArgAction.Help,
            ArgAction.HelpShort,
            ArgAction.HelpLong,
            ArgAction.Version,
        ):
            # no processing to be done
            command.args[command_path + field_name] = value

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
                    "Only 'arg(...)', 'group(...)', or 'mutex(...)' can be assigned to a field."
                )
            arg = value or Arg()
            add_argument(arg, ty, command, field_name, command_path, docstrings)

    if not command.disable_help_flag:
        command.args[command_path + _HELP_DEST] = Arg(
            action=ArgAction.Help, dest=_HELP_DEST, short="-h", long="--help", about="Print help"
        )

    if not command.disable_version_flag:
        command.args[command_path + _VERSION_DEST] = Arg(
            action=ArgAction.Version,
            dest=_VERSION_DEST,
            short="-V",
            long="--version",
            about="Print version",
        )

    setattr(cls, _COMMAND_DATA, command)
    return command


def configure_parser(parser: argparse.ArgumentParser, command: Command):
    for arg in command.args.values():
        if arg.group is not None or arg.mutex is not None:
            continue
        parser.add_argument(*arg.get_argparse_flags(), **arg.get_argparse_kwargs())

    # groups can have mutexes in them, so storing them temporarily in a dict
    groups = {
        group_obj: parser.add_argument_group()
        for group_obj in command.groups
    }

    # when both group and mutex are provided for an argument, the argument is
    # only added to the mutex when the command is created
    for group, args in command.groups.items():
        for arg in args:
            if arg.mutex is not None:
                continue
            groups[group].add_argument(*arg.get_argparse_flags(), **arg.get_argparse_kwargs())

    for mutex, args in command.mutexes.items():
        if mutex.parent is None:
            mutex_group = parser.add_mutually_exclusive_group(required=mutex.required)
        else:
            mutex_group = groups[mutex.parent].add_mutually_exclusive_group(
                required=mutex.required
            )
        for arg in args:
            mutex_group.add_argument(*arg.get_argparse_flags(), **arg.get_argparse_kwargs())

    if command.contains_subcommands():
        subparsers = parser.add_subparsers(
            dest=command.subparser_dest, required=command.subcommand_required
        )
        for subcommand in command.subcommands.values():
            parser = subparsers.add_parser(command=subcommand, **subcommand.get_parser_kwargs())
            configure_parser(parser, subcommand)


def create_parser(cls: type):
    command = create_command(cls)
    command.generate_usage()
    parser = ClapArgParser(command, **command.get_parser_kwargs())
    configure_parser(parser, command)
    return parser


def apply_parsed_args(args: dict[str, Any], instance: Any):
    command: Command = getattr(instance, _COMMAND_DATA)
    subcommand_args: dict[str, Any] = {}

    for attr_name, value in args.items():
        if attr_name.find('.') != -1:
            subcommand_args[attr_name.split(".", maxsplit=1)[1]] = value
        else:
            if attr_name == command.subcommand_dest:
                continue
            match command.args[attr_name].ty:
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

    # If an alias is used, argparse gives that instead of the subcommand name
    subcommand_alias = args[command.subcommand_dest]

    # subcommand not provided
    if subcommand_alias is None:
        if not hasattr(instance, command.subcommand_dest):
            setattr(instance, command.subcommand_dest, None)
        return

    subcommand_name: Optional[str] = None
    if subcommand_alias in command.subcommands:
        subcommand_name = subcommand_alias
    else:
        for name, subcommand in command.subcommands.items():
            if subcommand_alias in subcommand.aliases:
                subcommand_name = name
    assert subcommand_name is not None

    # only one subcommand can be provided
    cls = command.subcommands[subcommand_name].subcommand_class
    assert cls is not None
    subcommand_instance = object.__new__(cls)
    apply_parsed_args(subcommand_args, subcommand_instance)
    setattr(instance, command.subcommand_dest, subcommand_instance)


class ColorChoice(Enum):
    Auto = auto()
    Always = auto()
    Never = auto()
