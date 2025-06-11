"""Tests for basic argument parsing functionality."""

import unittest
from pathlib import Path
from typing import Optional

import clap
from clap import arg, long, short


class TestBasicArgumentParsing(unittest.TestCase):
    def test_positional_path_argument(self):
        @clap.command
        class Cli(clap.Parser):
            file: Path

        args = Cli.parse_args(["/tmp/test.txt"])
        self.assertEqual(args.file, Path("/tmp/test.txt"))

        with self.assertRaises(SystemExit):
            Cli.parse_args([])

        with self.assertRaises(SystemExit):
            Cli.parse_args(["/tmp/test.txt", "extra.txt"])

    def test_optional_positional_argument(self):
        @clap.command
        class Cli(clap.Parser):
            file: Optional[Path]

        args = Cli.parse_args(["/tmp/test.txt"])
        self.assertEqual(args.file, Path("/tmp/test.txt"))

        args = Cli.parse_args([])
        self.assertEqual(args.file, None)

        with self.assertRaises(SystemExit):
            Cli.parse_args(["/tmp/test.txt", "extra.txt"])

    def test_bool_flag_with_manual_flags(self):
        @clap.command
        class Cli(clap.Parser):
            verbose: bool = arg(short="v", long="verbose")

        args = Cli.parse_args([])
        self.assertFalse(args.verbose)

        args = Cli.parse_args(["-v"])
        self.assertTrue(args.verbose)

        args = Cli.parse_args(["--verbose"])
        self.assertTrue(args.verbose)

        with self.assertRaises(SystemExit):
            Cli.parse_args(["-x"])

        with self.assertRaises(SystemExit):
            Cli.parse_args(["--verbose", "true"])

    def test_bool_flag_with_hyphenated_flags(self):
        @clap.command
        class Cli(clap.Parser):
            verbose: bool = arg(short="-v", long="--verbose")

        args = Cli.parse_args([])
        self.assertFalse(args.verbose)

        args = Cli.parse_args(["-v"])
        self.assertTrue(args.verbose)

        args = Cli.parse_args(["--verbose"])
        self.assertTrue(args.verbose)

        with self.assertRaises(SystemExit):
            Cli.parse_args(["--unknown"])

    def test_bool_flag_with_short_long(self):
        @clap.command
        class Cli(clap.Parser):
            verbose: bool = arg(short, long)

        args = Cli.parse_args([])
        self.assertFalse(args.verbose)

        args = Cli.parse_args(["-v"])
        self.assertTrue(args.verbose)

        args = Cli.parse_args(["--verbose"])
        self.assertTrue(args.verbose)

    def test_option_with_value(self):
        @clap.command
        class Cli(clap.Parser):
            output: Optional[str] = arg(long)

        args = Cli.parse_args(["--output", "file.txt"])
        self.assertEqual(args.output, "file.txt")

        args = Cli.parse_args([])
        self.assertIsNone(args.output)

        with self.assertRaises(SystemExit):
            Cli.parse_args(["--output"])

        with self.assertRaises(SystemExit):
            Cli.parse_args(["--invalid", "value"])

    def test_multiple_arguments_mixed(self):
        @clap.command
        class Cli(clap.Parser):
            input_file: Path
            output_file: Optional[Path] = arg(long, value_name="<PATH>")
            verbose: bool = arg(short, long)

        args = Cli.parse_args(["input.txt", "--output", "output.txt", "-v"])
        self.assertEqual(args.input_file, Path("input.txt"))
        self.assertEqual(args.output_file, Path("output.txt"))
        self.assertTrue(args.verbose)

        args = Cli.parse_args(["input.txt"])
        self.assertEqual(args.input_file, Path("input.txt"))
        self.assertIsNone(args.output_file)
        self.assertFalse(args.verbose)

        with self.assertRaises(SystemExit):
            Cli.parse_args(["--output", "output.txt", "-v"])

        with self.assertRaises(SystemExit):
            Cli.parse_args(["--output", "output.txt", "input.txt", "--invalid"])

    def test_argument_with_default_value(self):
        @clap.command
        class Cli(clap.Parser):
            asdf: int = arg(long, default_value=42)

        args = Cli.parse_args([])
        self.assertEqual(args.asdf, 42)

        args = Cli.parse_args(["--asdf", "100"])
        self.assertEqual(args.asdf, 100)

        with self.assertRaises(SystemExit):
            Cli.parse_args(["--asdf", "not_a_number"])

        with self.assertRaises(SystemExit):
            Cli.parse_args(["--asdf"])

    def test_const_default(self):
        @clap.command
        class Cli(clap.Parser):
            output: str = arg(
                long, num_args="?", default_missing_value="stdout", default_value="file.txt"
            )

        args = Cli.parse_args([])
        self.assertEqual(args.output, "file.txt")

        args = Cli.parse_args(["--output"])
        self.assertEqual(args.output, "stdout")

        args = Cli.parse_args(["--output", "custom.txt"])
        self.assertEqual(args.output, "custom.txt")

        with self.assertRaises(SystemExit):
            Cli.parse_args(["--unknown"])

        with self.assertRaises(SystemExit):
            Cli.parse_args(["--output", "custom.txt", "extra"])


if __name__ == "__main__":
    unittest.main()
