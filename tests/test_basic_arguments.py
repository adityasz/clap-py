"""Tests for basic argument parsing functionality."""

import unittest
from pathlib import Path
from typing import Optional

import clap
from clap import arg, long, short


class TestBasicArgumentParsing(unittest.TestCase):
    """Test basic argument parsing functionality."""

    def test_positional_path_argument(self):
        @clap.arguments
        class Cli(clap.Parser):
            file: Path

        args = Cli.parse_args(['/tmp/test.txt'])
        self.assertEqual(args.file, Path('/tmp/test.txt'))

    def test_optional_positional_argument(self):
        @clap.arguments
        class Cli(clap.Parser):
            file: Optional[Path]

        args = Cli.parse_args(['/tmp/test.txt'])
        self.assertEqual(args.file, Path('/tmp/test.txt'))

        args = Cli.parse_args([])
        self.assertEqual(args.file, None)

    def test_optional_string_argument(self):
        @clap.arguments
        class Cli(clap.Parser):
            name: Optional[str]

        args = Cli.parse_args(['value'])
        self.assertEqual(args.name, 'value')

        args = Cli.parse_args([])
        self.assertIsNone(args.name)

    def test_bool_flag_with_manual_flags(self):
        @clap.arguments
        class Cli(clap.Parser):
            verbose: bool = arg("v", "verbose")

        args = Cli.parse_args([])
        self.assertFalse(args.verbose)

        args = Cli.parse_args(['-v'])
        self.assertTrue(args.verbose)

        args = Cli.parse_args(['--verbose'])
        self.assertTrue(args.verbose)

    def test_bool_flag_with_hyphenated_flags(self):
        @clap.arguments
        class Cli(clap.Parser):
            verbose: bool = arg("-v", "--verbose")

        args = Cli.parse_args([])
        self.assertFalse(args.verbose)

        args = Cli.parse_args(['-v'])
        self.assertTrue(args.verbose)

        args = Cli.parse_args(['--verbose'])
        self.assertTrue(args.verbose)

    def test_bool_flag_with_short_long(self):
        @clap.arguments
        class Cli(clap.Parser):
            verbose: bool = arg(short, long)

        args = Cli.parse_args([])
        self.assertFalse(args.verbose)

        args = Cli.parse_args(['-v'])
        self.assertTrue(args.verbose)

        args = Cli.parse_args(['--verbose'])
        self.assertTrue(args.verbose)

    def test_option_with_value(self):
        @clap.arguments
        class Cli(clap.Parser):
            output: Optional[str] = arg(long)

        args = Cli.parse_args(['--output', 'file.txt'])
        self.assertEqual(args.output, 'file.txt')

        args = Cli.parse_args([])
        self.assertIsNone(args.output)

    def test_multiple_arguments_mixed(self):
        @clap.arguments
        class Cli(clap.Parser):
            input_file: Path
            output_file: Optional[Path] = arg(long, metavar="<PATH>")
            verbose: bool = arg(short, long)

        args = Cli.parse_args(['input.txt', '--output', 'output.txt', '-v'])
        self.assertEqual(args.input_file, Path('input.txt'))
        self.assertEqual(args.output_file, Path('output.txt'))
        self.assertTrue(args.verbose)

    def test_argument_with_default_value(self):
        @clap.arguments
        class Cli(clap.Parser):
            count: int = arg(long, default=42)

        args = Cli.parse_args([])
        self.assertEqual(args.count, 42)

        args = Cli.parse_args(['--count', '100'])
        self.assertEqual(args.count, 100)


class TestArgumentErrors(unittest.TestCase):
    """Test error handling for invalid arguments."""

    def test_missing_required_positional(self):
        @clap.arguments
        class Cli(clap.Parser):
            name: str

        with self.assertRaises(SystemExit):
            Cli.parse_args([])


if __name__ == '__main__':
    unittest.main()
