import unittest
from enum import Enum, auto
from io import StringIO
from textwrap import dedent
from unittest.mock import patch

import pytest

import clap
from clap import arg, long
from clap.api import _PARSER
from clap.styling import AnsiColor, ColorChoice, Style, Styles


def help_output(cls: type, long: bool = True) -> str:
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

        @clap.command(color=ColorChoice.Always, styles=styles)
        class Cli(clap.Parser):
            a: int
            """A."""

        assert help_output(Cli, True) == (
            f"{styles.usage_style}Usage:{styles.usage_style:#} "
            f"{styles.literal_style}pytest{styles.literal_style:#} "
            f"{styles.placeholder_style}<A>{styles.placeholder_style:#}\n"
            "\n"
            f"{styles.header_style}Arguments:{styles.header_style:#}\n"
            f"  {styles.placeholder_style}<A>{styles.placeholder_style:#}  A\n"
            "\n"
            f"{styles.header_style}Options:{styles.header_style:#}\n"
            f"  {styles.literal_style}-h{styles.literal_style:#}, "
            f"{styles.literal_style}--help{styles.literal_style:#}  Print help\n"
        )

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
            B = auto()
            """Help for B."""

        @clap.command
        class Cli(clap.Parser):
            foo: Foo

        assert help_output(Cli, False) == dedent("""\
            Usage: pytest <FOO>

            Arguments:
              <FOO>  [possible values: a, b]

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
                      - a: Help for A
                      - b: Help for B

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

    # TODO: Write more tests!
