import argparse
import ast
import inspect
from dataclasses import dataclass
from textwrap import dedent
from typing import Literal, Optional, Self, Sequence, TypeVar, Union

from .stuff import argument


class DocstringExtractor(ast.NodeVisitor):
    def __init__(self):
        ...

    def visit_ClassDef(self, node):
        print(type(node.body[1]))


def extract_docstrings(cls: type):
    extractor = DocstringExtractor()
    source = dedent(inspect.getsource(cls))
    print(source)
    tree = ast.parse(source)
    extractor.visit(tree)


T = TypeVar('T')


@dataclass
class Subcommand:
    name: str
    usage: str
    help: str
    arguments: list[Union[Argument, Self]]


def analyze_arguments(cls) -> list[Union[Argument, Subcommand]]:
    return []


def create_parser(cls, conflict_handler: str, exit_on_error: bool):
    extract_docstrings(cls)
    parser = argparse.ArgumentParser(
        add_help=False,
        conflict_handler=conflict_handler,
        exit_on_error=exit_on_error
    )
    # arguments = analyze_arguments(cls)
    # for arg in arguments:
    #     arg_kwargs = {}
    return parser
