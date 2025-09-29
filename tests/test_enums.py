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

        args = Cli.parse(["auto"])
        self.assertEqual(args.color, ColorChoice.Auto)

        args = Cli.parse(["always"])
        self.assertEqual(args.color, ColorChoice.Always)

        args = Cli.parse(["never"])
        self.assertEqual(args.color, ColorChoice.Never)

        with self.assertRaises(SystemExit):
            Cli.parse(["invalid"])

        with self.assertRaises(SystemExit):
            Cli.parse([])

        with self.assertRaises(SystemExit):
            Cli.parse(["Auto"])

    def test_optional_color_choice(self):
        @clap.command
        class Cli(clap.Parser):
            color: Optional[ColorChoice] = arg(long)

        args = Cli.parse([])
        self.assertIsNone(args.color)

        args = Cli.parse(["--color", "always"])
        self.assertEqual(args.color, ColorChoice.Always)

        with self.assertRaises(SystemExit):
            Cli.parse(["--color"])

        with self.assertRaises(SystemExit):
            Cli.parse(["--color", "invalid"])

    def test_enum_kebab_conversion(self):
        @clap.command
        class Cli(clap.Parser):
            option: PascalEnum

        args = Cli.parse(["option-one"])
        self.assertEqual(args.option, PascalEnum.OptionOne)

        args = Cli.parse(["option-two"])
        self.assertEqual(args.option, PascalEnum.optionTwo)

        args = Cli.parse(["option-three"])
        self.assertEqual(args.option, PascalEnum.option_three)

        args = Cli.parse(["option-four"])
        self.assertEqual(args.option, PascalEnum.Option_Four)

        args = Cli.parse(["option-five"])
        self.assertEqual(args.option, PascalEnum.OPTION_FIVE)

        args = Cli.parse(["h-atom"])
        self.assertEqual(args.option, PascalEnum.HAtom)

        with self.assertRaises(SystemExit):
            Cli.parse(["OptionOne"])

        with self.assertRaises(SystemExit):
            Cli.parse(["option_one"])

        with self.assertRaises(SystemExit):
            Cli.parse(["non-existent"])

    def test_optional_enum(self):
        @clap.command
        class Cli(clap.Parser):
            priority: Optional[Priority] = arg(short, long)

        args = Cli.parse([])
        self.assertIsNone(args.priority)

        args = Cli.parse(["-p", "high"])
        self.assertEqual(args.priority, Priority.High)

        args = Cli.parse(["--priority", "high"])
        self.assertEqual(args.priority, Priority.High)

        with self.assertRaises(SystemExit):
            Cli.parse(["-p", "urgent"])

        with self.assertRaises(SystemExit):
            Cli.parse(["-p"])

        with self.assertRaises(SystemExit):
            Cli.parse(["--priority", "High"])

    def test_enum_with_default(self):
        @clap.command
        class Cli(clap.Parser):
            level: LogLevel = arg(long, default_value=LogLevel.Info)

        args = Cli.parse([])
        self.assertEqual(args.level, LogLevel.Info)

        args = Cli.parse(["--level", "error"])
        self.assertEqual(args.level, LogLevel.Error)

        with self.assertRaises(SystemExit):
            Cli.parse(["--level", "fatal"])

        with self.assertRaises(SystemExit):
            Cli.parse(["--level"])


class TestEnumErrors(unittest.TestCase):
    def test_invalid_enum_value(self):
        @clap.command
        class Cli(clap.Parser):
            priority: Priority

        with self.assertRaises(SystemExit):
            Cli.parse(["invalid"])

        with self.assertRaises(SystemExit):
            Cli.parse([""])

        with self.assertRaises(SystemExit):
            Cli.parse(["low", "medium"])


if __name__ == "__main__":
    unittest.main()
