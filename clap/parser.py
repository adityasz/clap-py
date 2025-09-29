import argparse
import ast
import sys
from enum import EnumType
from inspect import getsource
from textwrap import dedent
from typing import Any, Optional, Union, get_args, get_origin, get_type_hints, override

from clap.core import (
    Arg,
    ArgAction,
    ArgType,
    Command,
    Group,
    long,
    short,
    to_kebab_case,
)
from clap.help import HelpRenderer

_SUBCOMMAND_MARKER = "__com.github.adityasz.clap_py.subcommand_marker__"
_COMMAND_DATA = "__command_data__"
_SUBCOMMAND_DEFAULTS = "__subcommand_defaults__"
_HELP_DEST = "0h"
_VERSION_DEST = "0v"


class ClapArgParser(argparse.ArgumentParser):
    def __init__(self, command: Command, **kwargs):
        self.command = command
        self.help_renderer = HelpRenderer(command)
        # override usage for argparse error messages
        kwargs["usage"] = self.help_renderer.format_usage()
        super().__init__(**kwargs, add_help=False)

    def print_version(self, use_long: bool):
        if use_long:
            version = self.command.long_version or self.command.version
            print(f"{self.command.name} {version}")
        else:
            version = self.command.version or self.command.long_version
            print(f"{self.command.name} {version}")
        sys.exit(0)

    def print_nice_help(self, use_long: bool):
        self.help_renderer.set_use_long(use_long)
        self.help_renderer.render()
        sys.exit(0)


class DocstringExtractor(ast.NodeVisitor):
    def __init__(self):
        self.docstrings: dict[str, str] = {}

    @override
    def visit_ClassDef(self, node):
        for stmt_1, stmt_2 in zip(node.body[:-1], node.body[1:], strict=False):
            # Class attributes do not have __doc__, but the interpreter does
            # not strip away the docstrings either. So we can get them from
            # the AST.
            #
            # >>> file: Path
            # >>> """Path to the input file"""
            if not (
                isinstance(stmt_2, ast.Expr)
                and isinstance(stmt_2.value, ast.Constant)
                and isinstance(stmt_2.value.value, str)
            ):
                continue
            if isinstance(stmt_1, ast.AnnAssign) and isinstance(stmt_1.target, ast.Name):
                self.docstrings[stmt_1.target.id] = stmt_2.value.value.strip()
            if isinstance(stmt_1, ast.Assign) and isinstance(stmt_1.targets[0], ast.Name):
                # for groups:
                # g = group("Input options")  # this does not need an annotation
                # """This group contains options for..."""
                self.docstrings[stmt_1.targets[0].id] = stmt_2.value.value.strip()


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


def get_help_from_docstring(docstring: str) -> tuple[str, str]:
    paragraphs: list[str] = []
    curr_paragraph: list[str] = []
    for line in map(str.strip, docstring.splitlines()):
        if line:
            curr_paragraph.append(line)
        else:
            if curr_paragraph:
                paragraphs.append(" ".join(curr_paragraph))
                curr_paragraph.clear()
    if curr_paragraph:
        paragraphs.append(" ".join(curr_paragraph))
    if not paragraphs:
        return "", ""
    short_help = paragraphs[0]
    if short_help[-1] == "." and (len(short_help) == 1 or short_help[-2] != "."):
        short_help = short_help[:-1]
    if len(paragraphs) == 1:
        return short_help, short_help
    return short_help, "\n\n".join(paragraphs)


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


def parse_type_hint(type_hint: Any, optional: bool = False) -> ArgType.Base:
    if type(type_hint) is type:
        if is_subcommand(type_hint):
            return ArgType.SubcommandDest(optional, [type_hint])
        if type_hint is type(None):
            raise TypeError
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
    elif isinstance(arg.short, str):
        if arg.short[0] not in prefix_chars:
            arg.short = prefix_chars[0] + arg.short
        if len(arg.short) != 2 or arg.short[1] in prefix_chars:
            raise ValueError

    if arg.long == long:
        arg.long = 2 * prefix_chars[0] + to_kebab_case(field_name)
    elif isinstance(arg.long, str) and arg.long[0] not in prefix_chars:
        arg.long = 2 * prefix_chars[0] + arg.long


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
                        break
        case ArgType.List(t, optional):
            if arg.action is None:
                if not arg.is_positional():
                    arg.action = ArgAction.Append
                    return
                if arg.num_args is None:
                    arg.num_args = "*"
                if optional:
                    match arg.num_args:
                        case 0 | "?": ...
                        case "*": ...
                        case "+":
                            arg.num_args = "*"
                        case _:
                            raise TypeError(
                                "argparse limitation: Please use `num_args='*'` "
                                "with manual validation."
                            )
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
            if arg.default_value is not None:
                if optional_type_hint:
                    raise TypeError("An argument with a default value can never be None.")
                if arg.is_positional():
                    arg.num_args = "?"
                    arg.required = None
                else:
                    arg.required = False
            if arg.default_value is None:
                if not optional_type_hint:
                    if arg.num_args not in ("?", "*"):
                        arg.required = True
                    else:
                        arg.required = False
                        if isinstance(arg.ty, ArgType.List):
                            arg.default_value = []
                else:
                    arg.required = False
                if arg.is_positional():
                    if optional_type_hint:
                        arg.num_args = "?"
                    arg.required = None
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
        case _:
            pass


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
                case ArgAction.Set | ArgAction.Append:
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
    if (docstring := docstrings.get(field_name)) is not None:
        help, long_help = get_help_from_docstring(docstring)
        if arg.help is None:
            arg.help = help
        if arg.long_help is None:
            arg.long_help = long_help

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
        subcommand = create_command(cmd, command_path, command)
        name = subcommand.name
        command.subcommands[name] = subcommand


def create_command(cls: type, command_path: str = "", parent: Optional[Command] = None) -> Command:
    command: Command = getattr(cls, _COMMAND_DATA)
    docstrings: dict[str, str] = extract_docstrings(cls)

    if parent:
        parent.propagate_subcommand(command)

    if getattr(cls, _SUBCOMMAND_MARKER, False):
        command_path += command.name + "."
        command.subcommand_class = cls
        attrs = getattr(cls, _SUBCOMMAND_DEFAULTS)
        for name, attr in attrs.items():
            setattr(cls, name, attr)

    for field_name in dir(cls):
        value = getattr(cls, field_name, None)
        if isinstance(group := value, Group):
            if group in command.groups:
                raise ValueError(
                    f"A group with title '{group.title}' and the same description already exists."
                )
            if (docstring := docstrings.get(field_name)) is not None:
                about, long_about = get_help_from_docstring(docstring)
                if group.about is None:
                    group.about = about
                if group.long_about is None:
                    group.about = long_about
            command.groups[group] = []
        if isinstance(arg := value, Arg) and arg.action in (
            ArgAction.Help,
            ArgAction.HelpShort,
            ArgAction.HelpLong,
            ArgAction.Version,
        ):
            # no processing to be done
            command.args[command_path + field_name] = arg

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
            action=ArgAction.Help, dest=_HELP_DEST, short="-h", long="--help", help="Print help"
        )

    if not command.disable_version_flag and (command.version or command.long_version):
        command.args[command_path + _VERSION_DEST] = Arg(
            action=ArgAction.Version,
            dest=_VERSION_DEST,
            short="-V",
            long="--version",
            help="Print version",
        )

    setattr(cls, _COMMAND_DATA, command)
    return command


def configure_parser(parser: ClapArgParser, command: Command):
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
                case ArgType.List(_, optional):
                    if optional and command.args[attr_name].is_positional():
                        if value == []:
                            value = None
                        if isinstance(value, list) and all(v is None for v in value):
                            value = None
                case ArgType.Tuple():
                    if value is not None:
                        value = tuple(value)
                case ArgType.Enum(choice_to_enum_member=choice_to_enum_member):
                    if isinstance(value, str):
                        value = choice_to_enum_member[value]
                case _:
                    pass
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
