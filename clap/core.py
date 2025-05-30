import argparse
import ast
import sys
from inspect import getsource
from dataclasses import dataclass
from textwrap import dedent
from typing import Optional, TypeVar, Union, get_args, get_origin, get_type_hints

from .stuff import ArgumentInfo, ParserInfo, Group, MutexGroup, SubcommandInfo


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
    from .decorator import SUBCOMMAND_ATTR
    return getattr(cls, SUBCOMMAND_ATTR, False)


def contains_command(types: tuple[type]) -> bool:
    """Checks if an annotation contains subcommands or not.

    If an annotation contains a mixture of subcommands and other types, TypeError is raised.
    """
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


def analyze_fields(cls: type) -> ParserInfo:
    docstrings: dict[str, str] = extract_docstrings(cls)
    type_hints = get_type_hints(cls)
    arguments: dict[str, ArgumentInfo] = {}
    for field, type_hint in type_hints:
        if hasattr(cls, field):
            arg_info = getattr(cls, field)
            if arg_info.help is None and field in docstrings:
                arg_info.help = docstrings[field]
            arguments[field] = arg_info
        else:
            types: tuple[type]
            if type(type_hint) is type:
                types = (type_hint,)
            elif get_origin(type_hint) is Union:
                types = get_args(type_hint)
            else:
                raise TypeError(f"bad type annotation: {type_hint}")
            if contains_command(types):
                ... # do subcommand stuff
            else:
                if len(types) > 2:
                    raise TypeError(f"bad type annotation: {type_hint}")
                match len(types):
                    case 1:
                        arg_info = ArgumentInfo()
                    case 2:
                        if type(None) not in types:
                            raise TypeError(f"bad type annotation: {type_hint}")
                        arg_info = ArgumentInfo(nargs='?')


def create_parser(cls: type, **kwargs):
    parser = argparse.ArgumentParser(**kwargs)
    info = analyze_fields(cls)
    ...
    return parser
