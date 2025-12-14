import unittest
from enum import Enum, auto
from io import StringIO
from textwrap import dedent
from unittest.mock import patch

import pytest

import clap
from clap import arg, long, short
from clap.api import _PARSER
from clap.styling import AnsiColor, ColorChoice, Style, Styles


def help_output(cls: type[clap.Parser], long: bool = True) -> str:
    with patch("sys.stdout", StringIO()) as stdout:
        help_flag = "--help" if long else "-h"
        with pytest.raises(SystemExit):
            cls.parse([help_flag])
        return stdout.getvalue()


class HelpPrintingTest(unittest.TestCase):
    def test_colors(self):
        styles = (
            Styles()
                .header(Style().fg_color(AnsiColor.Cyan))
                .usage(Style().fg_color(AnsiColor.Magenta))
                .literal(Style().fg_color(AnsiColor.Yellow))
                .placeholder(Style().fg_color(AnsiColor.Green))
        )

        class Choices(Enum):
            One = auto()
            """One."""
            Two = auto()
            """Two."""

        @clap.command(color=ColorChoice.Always, styles=styles)
        class Cli(clap.Parser):
            a: int
            """A."""
            b: Choices = arg(short)

        def usage(s: str) -> str:
            return f"{styles.usage_style}{s}{styles.usage_style:#}"

        def literal(s: str) -> str:
            return f"{styles.literal_style}{s}{styles.literal_style:#}"

        def placeholder(s: str) -> str:
            return f"{styles.placeholder_style}{s}{styles.placeholder_style:#}"

        def header(s: str) -> str:
            return f"{styles.header_style}{s}{styles.header_style:#}"

        assert help_output(Cli, True) == (
            f"{usage('Usage:')} "
            f"{literal('pytest')} {literal('-b')} {placeholder('<B>')} {placeholder('<A>')}\n"
            "\n"
            f"{header('Arguments:')}\n"
            f"  {placeholder('<A>')}  A\n"
            "\n"
            f"{header('Options:')}\n"
            f"  {literal('-b')} {placeholder('<B>')}\n"
            f"          Possible values:\n"
            f"          - {literal('one')}: One\n"
            f"          - {literal('two')}: Two\n"
            f"\n"
            f"  {literal('-h')}, {literal('--help')}\n"
            f"          Print help\n"
        )

    def test_group_order(self):
        @clap.command
        class Cli(clap.Parser):
            z = clap.Group(title="Z")
            a = clap.Group(title="A")

            x: int = arg(group=z)
            y: int = arg(group=a)

        assert help_output(Cli, True) == dedent("""\
            Usage: pytest <X> <Y>

            Options:
              -h, --help  Print help

            Z:
              <X>

            A:
              <Y>
        """)

    def test_spec_val_indent_in_next_line_help(self):
        @clap.command
        class Cli(clap.Parser):
            this_is_a_really_really_long_option: int = arg(long, default_value=0)

        assert help_output(Cli, True) == dedent("""\
            Usage: pytest [OPTIONS]

            Options:
                  --this-is-a-really-really-long-option <THIS_IS_A_REALLY_REALLY_LONG_OPTION>
                      [default: 0]

              -h, --help
                      Print help
        """)

    def test_choices_empty_about(self):
        class Foo(Enum):
            A = auto()
            """Help for A."""
            BC = auto()
            """Help for BC."""

        @clap.command
        class Cli(clap.Parser):
            foo: Foo

        assert help_output(Cli, False) == dedent("""\
            Usage: pytest <FOO>

            Arguments:
              <FOO>  [possible values: a, bc]

            Options:
              -h, --help  Print help
        """)

        # The entire clap pipeline will be refactored at some point in the
        # future; this is a temporary hack:
        getattr(Cli, _PARSER).help_renderer.writer.s = ""

        assert help_output(Cli, True) == dedent("""\
            Usage: pytest <FOO>

            Arguments:
              <FOO>
                      Possible values:
                      - a:  Help for A
                      - bc: Help for BC

            Options:
              -h, --help  Print help
        """)

    def test_super_long_choice(self):
        class Choice(Enum):
            Choice = auto()
            """A choice with a very long help message.
            The quick brown fox jumps over the lazy dog."""
            LongChoice = auto()
            """A long choice."""
            VeryLoooooooooooooooooooooooooooooooongChoice = auto()
            """A very long choice."""

        @clap.command
        class Cli(clap.Parser):
            choice: Choice

        assert help_output(Cli, True) == dedent("""\
            Usage: pytest <CHOICE>

            Arguments:
              <CHOICE>
                      Possible values:
                      - choice:      A choice with a very long help message. The quick brown
                                     fox jumps over the lazy dog
                      - long-choice: A long choice
                      - very-loooooooooooooooooooooooooooooooong-choice:
                                     A very long choice

            Options:
              -h, --help  Print help
        """)

    def test_spec_vals(self):
        class Foo(Enum):
            A = auto()
            """Help for A."""
            B = auto()
            """Help for B."""

        @clap.command
        class Cli(clap.Parser):
            foo: Foo = arg(default_value=Foo.A)
            """Help for foo."""

        assert help_output(Cli, False) == dedent("""\
            Usage: pytest [FOO]

            Arguments:
              [FOO]  Help for foo [possible values: a, b] [default: a]

            Options:
              -h, --help  Print help
        """)

        # The entire clap pipeline will be refactored at some point in the
        # future; this is a temporary hack:
        getattr(Cli, _PARSER).help_renderer.writer.s = ""

        assert help_output(Cli, True) == dedent("""\
            Usage: pytest [FOO]

            Arguments:
              [FOO]
                      Help for foo

                      Possible values:
                      - a: Help for A
                      - b: Help for B

                      [default: a]

            Options:
              -h, --help  Print help
        """)


if __name__ == "__main__":
    unittest.main()
