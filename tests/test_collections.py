"""Tests for collection types and nargs functionality."""

import unittest
from pathlib import Path
from typing import Optional

import clap
from clap import arg, long


class TestListArguments(unittest.TestCase):
    """Test list argument parsing."""

    def test_list_with_nargs_star(self):
        @clap.arguments
        class Cli(clap.Parser):
            files: list[str] = arg(nargs="*")

        args = Cli.parse_args([])
        self.assertEqual(args.files, [])

        args = Cli.parse_args(["file1.txt", "file2.txt", "file3.txt"])
        self.assertEqual(args.files, ["file1.txt", "file2.txt", "file3.txt"])

    def test_list_of_paths(self):
        @clap.arguments
        class Cli(clap.Parser):
            files: list[Path] = arg(nargs="+")

        args = Cli.parse_args(["file1.txt", "file2.txt"])
        self.assertEqual(args.files, [Path("file1.txt"), Path("file2.txt")])

        with self.assertRaises(SystemExit):
            Cli.parse_args([])

    def test_optional_list_argument(self):
        @clap.arguments
        class Cli(clap.Parser):
            tags: Optional[list[str]] = arg(long, nargs="*")

        args = Cli.parse_args([])
        self.assertIsNone(args.tags)

        args = Cli.parse_args(["--tags"])
        self.assertEqual(args.tags, [])

        args = Cli.parse_args(["--tags", "tag1", "tag2"])
        self.assertEqual(args.tags, ["tag1", "tag2"])


class TestTupleArguments(unittest.TestCase):
    """Test tuple argument parsing."""

    def test_tuple_three_elements(self):
        @clap.arguments
        class Cli(clap.Parser):
            color: tuple[int, int, int]

        args = Cli.parse_args(["255", "128", "0"])
        self.assertEqual(args.color, (255, 128, 0))

    def test_tuple_nargs_mismatch_error(self):
        with self.assertRaises(TypeError):
            @clap.arguments
            class Cli(clap.Parser):
                point: tuple[int, int] = arg(nargs=3)

    def test_optional_tuple(self):
        @clap.arguments
        class Cli(clap.Parser):
            size: Optional[tuple[int, int]] = arg(long, nargs=2)

        args = Cli.parse_args([])
        self.assertIsNone(args.size)

        args = Cli.parse_args(["--size", "800", "600"])
        self.assertEqual(args.size, (800, 600))


class TestArgparseActions(unittest.TestCase):
    """Test various argparse actions."""

    def test_store_const_action(self):
        @clap.arguments
        class Cli(clap.Parser):
            mode: Optional[str] = arg(long, action="store_const", const="debug")

        args = Cli.parse_args([])
        self.assertIsNone(args.mode)

        args = Cli.parse_args(["--mode"])
        self.assertEqual(args.mode, "debug")

    def test_append_action(self):
        @clap.arguments
        class Cli(clap.Parser):
            include: Optional[list[str]] = arg(long="-I", action="append")

        args = Cli.parse_args(["-I", "path1", "-I", "path2", "-I", "path3"])
        self.assertEqual(args.include, ["path1", "path2", "path3"])

    def test_count_action(self):
        @clap.arguments
        class Cli(clap.Parser):
            verbose: int = arg(short="-v", action="count")

        args = Cli.parse_args([])
        self.assertEqual(args.verbose, 0)

        args = Cli.parse_args(["-v"])
        self.assertEqual(args.verbose, 1)

        args = Cli.parse_args(["-vvv"])
        self.assertEqual(args.verbose, 3)

    def test_store_false_action(self):
        @clap.arguments
        class Cli(clap.Parser):
            no_cache: bool = arg(long, action="store_false", default=True)

        args = Cli.parse_args([])
        self.assertTrue(args.no_cache)

        args = Cli.parse_args(["--no-cache"])
        self.assertFalse(args.no_cache)


class TestNargsSpecialCases(unittest.TestCase):
    """Test special nargs cases."""

    def test_optional_positional(self):
        @clap.arguments
        class Cli(clap.Parser):
            file: str = arg(nargs="?", default="default.txt")

        args = Cli.parse_args([])
        self.assertEqual(args.file, "default.txt")

        args = Cli.parse_args(["custom.txt"])
        self.assertEqual(args.file, "custom.txt")

    def test_const_default(self):
        @clap.arguments
        class Cli(clap.Parser):
            output: str = arg(long, nargs="?", const="stdout", default="file.txt")

        args = Cli.parse_args([])
        self.assertEqual(args.output, "file.txt")

        args = Cli.parse_args(["--output"])
        self.assertEqual(args.output, "stdout")

        args = Cli.parse_args(["--output", "custom.txt"])
        self.assertEqual(args.output, "custom.txt")


if __name__ == "__main__":
    unittest.main()
