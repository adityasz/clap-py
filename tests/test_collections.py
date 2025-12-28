import unittest
from pathlib import Path
from typing import Optional

import pytest

import clap
from clap import arg, long


class TestListArguments(unittest.TestCase):
    def test_positional_with_nargs_star(self):
        @clap.command
        class Cli(clap.Parser):
            files: list[str] = arg(num_args="*")

        args = Cli.parse([])
        assert args.files == []

        args = Cli.parse(["file1.txt", "file2.txt", "file3.txt"])
        assert args.files == ["file1.txt", "file2.txt", "file3.txt"]

        with pytest.raises(SystemExit):
            Cli.parse(["--unknown", "file1.txt"])

    def test_option_with_nargs_star(self):
        @clap.command
        class Cli(clap.Parser):
            files: list[str] = arg(long, num_args="*")

        args = Cli.parse([])
        assert args.files == []

        args = Cli.parse(["--files", "file1.txt", "file2.txt", "file3.txt"])
        assert args.files == ["file1.txt", "file2.txt", "file3.txt"]

        with pytest.raises(SystemExit):
            Cli.parse(["--unknown", "file1.txt"])

    def test_list_of_paths(self):
        @clap.command
        class Cli(clap.Parser):
            files: list[Path] = arg(num_args="+")

        args = Cli.parse(["file1.txt", "file2.txt"])
        assert args.files == [Path("file1.txt"), Path("file2.txt")]

        with pytest.raises(SystemExit):
            Cli.parse([])

        args = Cli.parse(["file.txt"])
        assert args.files == [Path("file.txt")]

        with pytest.raises(SystemExit):
            Cli.parse(["file1.txt", "--unknown"])

    def test_optional_list_argument(self):
        @clap.command
        class Cli(clap.Parser):
            tags: Optional[list[str]] = arg(long, num_args="*")

        args = Cli.parse([])
        assert args.tags is None

        args = Cli.parse(["--tags"])
        assert args.tags == []

        args = Cli.parse(["--tags", "tag1", "tag2"])
        assert args.tags == ["tag1", "tag2"]


class TestTupleArguments(unittest.TestCase):
    def test_tuple_three_elements(self):
        @clap.command
        class Cli(clap.Parser):
            color: tuple[int, int, int]

        args = Cli.parse(["255", "128", "0"])
        assert args.color == (255, 128, 0)

        with pytest.raises(SystemExit):
            Cli.parse([])

        with pytest.raises(SystemExit):
            Cli.parse(["255", "128"])

        with pytest.raises(SystemExit):
            Cli.parse(["255", "128", "0", "255"])

        with pytest.raises(SystemExit):
            Cli.parse(["255", "not_a_number", "0"])

    def test_tuple_nargs_mismatch_error(self):
        @clap.command
        class Cli(clap.Parser):
            point: tuple[int, int] = arg(num_args=3)

        with pytest.raises(SystemExit):
            Cli.parse()

    def test_optional_tuple(self):
        @clap.command
        class Cli(clap.Parser):
            size: Optional[tuple[int, int]] = arg(long, num_args=2)

        args = Cli.parse([])
        assert args.size is None

        args = Cli.parse(["--size", "800", "600"])
        assert args.size == (800, 600)

        with pytest.raises(SystemExit):
            Cli.parse(["--size"])

        with pytest.raises(SystemExit):
            Cli.parse(["--size", "800"])

        with pytest.raises(SystemExit):
            Cli.parse(["--size", "width", "height"])

        with pytest.raises(SystemExit):
            Cli.parse(["--size", "800", "600", "300"])


if __name__ == "__main__":
    unittest.main()
