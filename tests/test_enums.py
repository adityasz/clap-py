import unittest
from enum import Enum, auto
from typing import Optional

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

        args = Cli.parse_args(["auto"])
        self.assertEqual(args.color, ColorChoice.Auto)

        args = Cli.parse_args(["always"])
        self.assertEqual(args.color, ColorChoice.Always)

        args = Cli.parse_args(["never"])
        self.assertEqual(args.color, ColorChoice.Never)

        with self.assertRaises(SystemExit):
            Cli.parse_args(["invalid"])

        with self.assertRaises(SystemExit):
            Cli.parse_args([])

        with self.assertRaises(SystemExit):
            Cli.parse_args(["Auto"])

    def test_optional_color_choice(self):
        @clap.command
        class Cli(clap.Parser):
            color: Optional[ColorChoice] = arg(long)

        args = Cli.parse_args([])
        self.assertIsNone(args.color)

        args = Cli.parse_args(["--color", "always"])
        self.assertEqual(args.color, ColorChoice.Always)

        with self.assertRaises(SystemExit):
            Cli.parse_args(["--color"])

        with self.assertRaises(SystemExit):
            Cli.parse_args(["--color", "invalid"])

    def test_enum_kebab_conversion(self):
        @clap.command
        class Cli(clap.Parser):
            option: PascalEnum

        args = Cli.parse_args(["option-one"])
        self.assertEqual(args.option, PascalEnum.OptionOne)

        args = Cli.parse_args(["option-two"])
        self.assertEqual(args.option, PascalEnum.optionTwo)

        args = Cli.parse_args(["option-three"])
        self.assertEqual(args.option, PascalEnum.option_three)

        args = Cli.parse_args(["option-four"])
        self.assertEqual(args.option, PascalEnum.Option_Four)

        args = Cli.parse_args(["option-five"])
        self.assertEqual(args.option, PascalEnum.OPTION_FIVE)

        args = Cli.parse_args(["h-atom"])
        self.assertEqual(args.option, PascalEnum.HAtom)

        with self.assertRaises(SystemExit):
            Cli.parse_args(["OptionOne"])

        with self.assertRaises(SystemExit):
            Cli.parse_args(["option_one"])

        with self.assertRaises(SystemExit):
            Cli.parse_args(["non-existent"])

    def test_optional_enum(self):
        @clap.command
        class Cli(clap.Parser):
            priority: Optional[Priority] = arg(short, long)

        args = Cli.parse_args([])
        self.assertIsNone(args.priority)

        args = Cli.parse_args(["-p", "high"])
        self.assertEqual(args.priority, Priority.High)

        args = Cli.parse_args(["--priority", "high"])
        self.assertEqual(args.priority, Priority.High)

        with self.assertRaises(SystemExit):
            Cli.parse_args(["-p", "urgent"])

        with self.assertRaises(SystemExit):
            Cli.parse_args(["-p"])

        with self.assertRaises(SystemExit):
            Cli.parse_args(["--priority", "High"])

    def test_enum_with_default(self):
        @clap.command
        class Cli(clap.Parser):
            level: LogLevel = arg(long, default_value=LogLevel.Info)

        args = Cli.parse_args([])
        self.assertEqual(args.level, LogLevel.Info)

        args = Cli.parse_args(["--level", "error"])
        self.assertEqual(args.level, LogLevel.Error)

        with self.assertRaises(SystemExit):
            Cli.parse_args(["--level", "fatal"])

        with self.assertRaises(SystemExit):
            Cli.parse_args(["--level"])


class TestEnumErrors(unittest.TestCase):
    def test_invalid_enum_value(self):
        @clap.command
        class Cli(clap.Parser):
            priority: Priority

        with self.assertRaises(SystemExit):
            Cli.parse_args(["invalid"])

        with self.assertRaises(SystemExit):
            Cli.parse_args([""])

        with self.assertRaises(SystemExit):
            Cli.parse_args(["low", "medium"])


if __name__ == "__main__":
    unittest.main()
