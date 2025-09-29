import unittest
from enum import Enum, auto
from typing import Optional

import pytest

import clap
from clap import ColorChoice, arg, long, short


class Priority(Enum):
    Low = auto()
    Medium = auto()
    High = auto()


class LogLevel(Enum):
    Debug = auto()
    Info = auto()
    Warning = auto()
    Error = auto()


class PascalEnum(Enum):
    OptionOne = auto()
    optionTwo = auto()
    option_three = auto()
    Option_Four = auto()
    OPTION_FIVE = auto()
    HAtom = auto()


class TestEnums(unittest.TestCase):
    def test_color_choice_enum(self):
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

    def test_optional_color_choice(self):
        @clap.command
        class Cli(clap.Parser):
            color: Optional[ColorChoice] = arg(long)

        args = Cli.parse([])
        assert args.color is None

        args = Cli.parse(["--color", "always"])
        assert args.color == ColorChoice.Always

        with pytest.raises(SystemExit):
            Cli.parse(["--color"])

        with pytest.raises(SystemExit):
            Cli.parse(["--color", "invalid"])

    def test_enum_kebab_conversion(self):
        @clap.command
        class Cli(clap.Parser):
            option: PascalEnum

        args = Cli.parse(["option-one"])
        assert args.option == PascalEnum.OptionOne

        args = Cli.parse(["option-two"])
        assert args.option == PascalEnum.optionTwo

        args = Cli.parse(["option-three"])
        assert args.option == PascalEnum.option_three

        args = Cli.parse(["option-four"])
        assert args.option == PascalEnum.Option_Four

        args = Cli.parse(["option-five"])
        assert args.option == PascalEnum.OPTION_FIVE

        args = Cli.parse(["h-atom"])
        assert args.option == PascalEnum.HAtom

        with pytest.raises(SystemExit):
            Cli.parse(["OptionOne"])

        with pytest.raises(SystemExit):
            Cli.parse(["option_one"])

        with pytest.raises(SystemExit):
            Cli.parse(["non-existent"])

    def test_optional_enum(self):
        @clap.command
        class Cli(clap.Parser):
            priority: Optional[Priority] = arg(short, long)

        args = Cli.parse([])
        assert args.priority is None

        args = Cli.parse(["-p", "high"])
        assert args.priority == Priority.High

        args = Cli.parse(["--priority", "high"])
        assert args.priority == Priority.High

        with pytest.raises(SystemExit):
            Cli.parse(["-p", "urgent"])

        with pytest.raises(SystemExit):
            Cli.parse(["-p"])

        with pytest.raises(SystemExit):
            Cli.parse(["--priority", "High"])

    def test_enum_with_default(self):
        @clap.command
        class Cli(clap.Parser):
            level: LogLevel = arg(long, default_value=LogLevel.Info)

        args = Cli.parse([])
        assert args.level == LogLevel.Info

        args = Cli.parse(["--level", "error"])
        assert args.level == LogLevel.Error

        with pytest.raises(SystemExit):
            Cli.parse(["--level", "fatal"])

        with pytest.raises(SystemExit):
            Cli.parse(["--level"])


class TestEnumErrors(unittest.TestCase):
    def test_invalid_enum_value(self):
        @clap.command
        class Cli(clap.Parser):
            priority: Priority

        with pytest.raises(SystemExit):
            Cli.parse(["invalid"])

        with pytest.raises(SystemExit):
            Cli.parse([""])

        with pytest.raises(SystemExit):
            Cli.parse(["low", "medium"])


if __name__ == "__main__":
    unittest.main()
