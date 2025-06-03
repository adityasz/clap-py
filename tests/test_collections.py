import unittest
from pathlib import Path
from typing import Optional

import clap
from clap import arg, long


class TestListArguments(unittest.TestCase):
    def test_list_with_nargs_star(self):
        @clap.arguments
        class Cli(clap.Parser):
            files: list[str] = arg(nargs="*")

        args = Cli.parse_args([])
        self.assertEqual(args.files, [])

        args = Cli.parse_args(["file1.txt", "file2.txt", "file3.txt"])
        self.assertEqual(args.files, ["file1.txt", "file2.txt", "file3.txt"])

        with self.assertRaises(SystemExit):
            Cli.parse_args(["--unknown", "file1.txt"])

    def test_list_of_paths(self):
        @clap.arguments
        class Cli(clap.Parser):
            files: list[Path] = arg(nargs="+")

        args = Cli.parse_args(["file1.txt", "file2.txt"])
        self.assertEqual(args.files, [Path("file1.txt"), Path("file2.txt")])

        with self.assertRaises(SystemExit):
            Cli.parse_args([])

        args = Cli.parse_args(["file.txt"])
        self.assertEqual(args.files, [Path("file.txt")])

        with self.assertRaises(SystemExit):
            Cli.parse_args(["file1.txt", "--unknown"])

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
    def test_tuple_three_elements(self):
        @clap.arguments
        class Cli(clap.Parser):
            color: tuple[int, int, int]

        args = Cli.parse_args(["255", "128", "0"])
        self.assertEqual(args.color, (255, 128, 0))

        with self.assertRaises(SystemExit):
            Cli.parse_args([])

        with self.assertRaises(SystemExit):
            Cli.parse_args(["255", "128"])

        with self.assertRaises(SystemExit):
            Cli.parse_args(["255", "128", "0", "255"])

        with self.assertRaises(SystemExit):
            Cli.parse_args(["255", "not_a_number", "0"])

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

        with self.assertRaises(SystemExit):
            Cli.parse_args(["--size"])

        with self.assertRaises(SystemExit):
            Cli.parse_args(["--size", "800"])

        with self.assertRaises(SystemExit):
            Cli.parse_args(["--size", "width", "height"])

        with self.assertRaises(SystemExit):
            Cli.parse_args(["--size", "800", "600", "300"])


if __name__ == "__main__":
    unittest.main()
