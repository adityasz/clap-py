import unittest
from enum import Enum
from pathlib import Path
from typing import Optional

import clap
from clap import arg, long


class TestActions(unittest.TestCase):
    def test_store_const_action(self):
        @clap.command
        class Cli(clap.Parser):
            mode: Optional[str] = arg(long, action="store_const", default_missing_value="debug")

        args = Cli.parse_args([])
        self.assertIsNone(args.mode)

        args = Cli.parse_args(["--mode"])
        self.assertEqual(args.mode, "debug")

        with self.assertRaises(SystemExit):
            Cli.parse_args(["--mode", "extra_arg"])

    def test_append_action_optional_type(self):
        @clap.command
        class Cli(clap.Parser):
            include: Optional[list[str]] = arg(long="-I", action="append")

        args = Cli.parse_args(["-I", "path1", "-I", "path2", "-I", "path3"])
        self.assertEqual(args.include, ["path1", "path2", "path3"])

        args = Cli.parse_args([])
        self.assertIsNone(args.include)

        with self.assertRaises(SystemExit):
            Cli.parse_args(["-I"])

    def test_count_action(self):
        @clap.command
        class Cli(clap.Parser):
            verbose: int = arg(short="-v", action="count")

        args = Cli.parse_args([])
        self.assertEqual(args.verbose, 0)

        args = Cli.parse_args(["-v"])
        self.assertEqual(args.verbose, 1)

        args = Cli.parse_args(["-vvv"])
        self.assertEqual(args.verbose, 3)

        with self.assertRaises(SystemExit):
            Cli.parse_args(["-x"])

    def test_store_false_action(self):
        @clap.command
        class Cli(clap.Parser):
            no_cache: bool = arg(long, action="store_false", default_value=True)

        args = Cli.parse_args([])
        self.assertTrue(args.no_cache)

        args = Cli.parse_args(["--no-cache"])
        self.assertFalse(args.no_cache)

        with self.assertRaises(SystemExit):
            Cli.parse_args(["--no-cache", "false"])

    def test_append_action(self):
        @clap.command
        class Cli(clap.Parser):
            libs: list[str] = arg(long="-l", action="append")

        args = Cli.parse_args([])
        self.assertEqual(args.libs, [])

        args = Cli.parse_args(["-l", "lib1", "-l", "lib2"])
        self.assertEqual(args.libs, ["lib1", "lib2"])

        with self.assertRaises(SystemExit):
            Cli.parse_args(["-l"])

    def test_append_action_with_explicit_default(self):
        @clap.command
        class Cli(clap.Parser):
            flags: list[str] = arg(long, action="append", default_value=["default"])

        args = Cli.parse_args([])
        self.assertEqual(args.flags, ["default"])

        args = Cli.parse_args(["--flags", "custom"])
        self.assertEqual(args.flags, ["default", "custom"])

        with self.assertRaises(SystemExit):
            Cli.parse_args(["--invalid-flag", "value"])

    def test_append_const_action(self):
        @clap.command
        class Cli(clap.Parser):
            features: list[str] = arg(
                long="--enable-feature", action="append_const", default_missing_value="feature1"
            )

        args = Cli.parse_args([])
        self.assertEqual(args.features, [])

        args = Cli.parse_args(["--enable-feature", "--enable-feature"])
        self.assertEqual(args.features, ["feature1", "feature1"])

        with self.assertRaises(SystemExit):
            Cli.parse_args(["--enable-feature", "value"])

    def test_extend_action(self):
        @clap.command
        class Cli(clap.Parser):
            items: list[str] = arg(long, action="extend", num_args="+")

        args = Cli.parse_args([])
        self.assertEqual(args.items, [])

        args = Cli.parse_args(["--items", "a", "b", "--items", "c", "d"])
        self.assertEqual(args.items, ["a", "b", "c", "d"])

        with self.assertRaises(SystemExit):
            Cli.parse_args(["--items"])

    def test_store_const_with_required(self):
        @clap.command
        class Cli(clap.Parser):
            mode: str = arg(long, action="store_const", default_missing_value="production")

        args = Cli.parse_args(["--mode"])
        self.assertEqual(args.mode, "production")

        with self.assertRaises(SystemExit):
            Cli.parse_args([])

        with self.assertRaises(SystemExit):
            Cli.parse_args(["--unknown"])

    def test_store_true_false_defaults(self):
        @clap.command
        class Cli(clap.Parser):
            enable: bool = arg(long, action="store_true")
            disable: bool = arg(long, action="store_false")

        args = Cli.parse_args([])
        self.assertFalse(args.enable)
        self.assertTrue(args.disable)

        args = Cli.parse_args(["--enable", "--disable"])
        self.assertTrue(args.enable)
        self.assertFalse(args.disable)

        with self.assertRaises(SystemExit):
            Cli.parse_args(["--enable", "true"])

    def test_count_action_with_default(self):
        @clap.command
        class Cli(clap.Parser):
            level: int = arg(short="-l", action="count", default_value=5)

        args = Cli.parse_args([])
        self.assertEqual(args.level, 5)

        args = Cli.parse_args(["-ll"])
        self.assertEqual(args.level, 7)

        with self.assertRaises(SystemExit):
            Cli.parse_args(["-lx"])

    def test_multiple_action_combinations(self):
        @clap.command
        class Cli(clap.Parser):
            verbose: int = arg(short="-v", action="count")
            debug: bool = arg(long, action="store_true")
            includes: list[str] = arg(short="-I", action="append")
            features: list[str] = arg(long="--feature", action="append_const", default_missing_value="enabled")

        args = Cli.parse_args(["-vv", "--debug", "-I", "lib1", "-I", "lib2", "--feature"])
        self.assertEqual(args.verbose, 2)
        self.assertTrue(args.debug)
        self.assertEqual(args.includes, ["lib1", "lib2"])
        self.assertEqual(args.features, ["enabled"])

        args = Cli.parse_args([])
        self.assertEqual(args.verbose, 0)
        self.assertFalse(args.debug)
        self.assertEqual(args.includes, [])
        self.assertEqual(args.features, [])

        with self.assertRaises(SystemExit):
            Cli.parse_args(["-I"])


class TestActionTypeErrors(unittest.TestCase):
    def test_count_with_optional_type_error(self):
        with self.assertRaises(TypeError):
            @clap.command
            class Cli(clap.Parser):
                count: Optional[int] = arg(short="-c", action="count")

    def test_store_true_with_optional_type_error(self):
        with self.assertRaises(TypeError):
            @clap.command
            class Cli(clap.Parser):
                flag: Optional[bool] = arg(long, action="store_true")

    def test_store_false_with_optional_type_error(self):
        with self.assertRaises(TypeError):
            @clap.command
            class Cli(clap.Parser):
                flag: Optional[bool] = arg(long, action="store_false")

    def test_store_const_with_optional_and_default_error(self):
        with self.assertRaises(TypeError):
            @clap.command
            class Cli(clap.Parser):
                mode: Optional[str] = arg(
                    long, action="store_const", default_missing_value="test", default_value="default"
                )

    def test_store_with_required_and_optional_error(self):
        with self.assertRaises(TypeError):
            @clap.command
            class Cli(clap.Parser):
                value: Optional[str] = arg(long, action="store", required=True)

    def test_store_with_default_and_optional_error(self):
        with self.assertRaises(TypeError):
            @clap.command
            class Cli(clap.Parser):
                value: Optional[str] = arg(long, action="store", default_value="test")


class TestActionsWithComplexTypes(unittest.TestCase):
    def test_append_with_enum_choices(self):
        class Color(Enum):
            RED = "red"
            GREEN = "green"
            BLUE = "blue"

        @clap.command
        class Cli(clap.Parser):
            colors: list[Color] = arg(long, action="append")

        args = Cli.parse_args(["--colors", "red", "--colors", "blue"])
        self.assertEqual(args.colors, [Color.RED, Color.BLUE])

        args = Cli.parse_args([])
        self.assertEqual(args.colors, [])

        with self.assertRaises(SystemExit):
            Cli.parse_args(["--colors", "purple"])

    def test_extend_with_path_type(self):
        @clap.command
        class Cli(clap.Parser):
            files: list[Path] = arg(long, action="extend", num_args="+")

        args = Cli.parse_args(["--files", "a.txt", "b.txt", "--files", "c.txt"])
        self.assertEqual(args.files, [Path("a.txt"), Path("b.txt"), Path("c.txt")])

        args = Cli.parse_args([])
        self.assertEqual(args.files, [])

        with self.assertRaises(SystemExit):
            Cli.parse_args(["--files"])


if __name__ == "__main__":
    unittest.main()
