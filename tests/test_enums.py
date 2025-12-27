import unittest
from enum import Enum, auto
from typing import Optional

import pytest

import clap
from clap import ColorChoice, arg, long, short


class ManyOptions(Enum):
    OptionOne = auto()
    optionTwo = auto()
    option_three = auto()
    Option_Four = auto()
    OPTION_FIVE = auto()
    HAtom = auto()


class TestEnums(unittest.TestCase):
    def test_enum(self):
        @clap.command
        class Cli(clap.Parser):
            color: ColorChoice

        args = Cli.parse(["auto"])
        assert args.color == ColorChoice.Auto

        args = Cli.parse(["always"])
        assert args.color == ColorChoice.Always

        args = Cli.parse(["never"])
        assert args.color == ColorChoice.Never

        with pytest.raises(SystemExit):
            Cli.parse(["invalid"])

        with pytest.raises(SystemExit):
            Cli.parse([])

        with pytest.raises(SystemExit):
            Cli.parse(["Auto"])

    def test_optional_enum(self):
        @clap.command
        class Cli(clap.Parser):
            color: Optional[ColorChoice] = arg(short, long)

        args = Cli.parse([])
        assert args.color is None

        args = Cli.parse(["-c", "always"])
        assert args.color == ColorChoice.Always

        args = Cli.parse(["--color", "always"])
        assert args.color == ColorChoice.Always

        with pytest.raises(SystemExit):
            Cli.parse(["-c"])

        with pytest.raises(SystemExit):
            Cli.parse(["-c", "sometimes"])

        with pytest.raises(SystemExit):
            Cli.parse(["--color", "sometimes"])

    def test_enum_with_default(self):
        @clap.command
        class Cli(clap.Parser):
            color: ColorChoice = arg(long, default_value=ColorChoice.Auto)

        args = Cli.parse([])
        assert args.color == ColorChoice.Auto

        args = Cli.parse(["--color", "always"])
        assert args.color == ColorChoice.Always

        with pytest.raises(SystemExit):
            Cli.parse(["--color"])

        with pytest.raises(SystemExit):
            Cli.parse(["--color", "sometimes"])


if __name__ == "__main__":
    unittest.main()
