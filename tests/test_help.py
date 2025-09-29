import unittest
from enum import Enum, auto
from io import StringIO
from unittest.mock import patch

import pytest

import clap
from clap import arg, long
from clap.styling import AnsiColor, ColorChoice, Style, Styles


def help_output(cls: type) -> str:
    with patch("sys.stdout", new_callable=StringIO) as stdout:
        with pytest.raises(SystemExit):
            cls.parse(["--help"])
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

        assert help_output(Cli) == (
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

        assert help_output(Cli) == (
            "Usage: pytest [OPTIONS]\n"
            "\n"
            "Options:\n"
            "      --this-is-a-really-really-long-option <THIS_IS_A_REALLY_REALLY_LONG_OPTION>\n"
            "          [default: 0]\n"
            "\n"
            "  -h, --help\n"
            "          Print help\n"
        )

    def test_spec_vals_empty_about(self):
        class Foo(Enum):
            A = auto()
            B = auto()

        @clap.command
        class Cli(clap.Parser):
            foo: Foo

        assert help_output(Cli) == (
            "Usage: pytest <FOO>\n"
            "\n"
            "Arguments:\n"
            "  <FOO>  [possible values: a, b]\n"
            "\n"
            "Options:\n"
            "  -h, --help  Print help\n"
        )

    # TODO: Write more tests!
