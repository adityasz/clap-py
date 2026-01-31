import unittest
from pathlib import Path
from typing import Optional

import pytest

import clap
from clap import arg, long


class TestListArguments(unittest.TestCase):
    def test_positional_nargs_star(self):
        @clap.command
        class Cli(clap.Parser):
            files: list[str] = arg(num_args="*")

        cli = Cli.parse([])
        assert cli.files == []

        cli = Cli.parse(["file1.txt", "file2.txt", "file3.txt"])
        assert cli.files == ["file1.txt", "file2.txt", "file3.txt"]

        with pytest.raises(SystemExit):
            Cli.parse(["--unknown", "file1.txt"])

    def test_option_nargs_star(self):
        @clap.command
        class Cli(clap.Parser):
            files: list[str] = arg(long, num_args="*")

        cli = Cli.parse([])
        assert cli.files == []

        cli = Cli.parse(["--files", "file1.txt", "file2.txt", "file3.txt"])
        assert cli.files == ["file1.txt", "file2.txt", "file3.txt"]

        with pytest.raises(SystemExit):
            Cli.parse(["--unknown", "file1.txt"])

    def test_positional_nargs_plus(self):
        @clap.command
        class Cli(clap.Parser):
            files: list[Path] = arg(num_args="+")

        cli = Cli.parse(["file1.txt", "file2.txt"])
        assert cli.files == [Path("file1.txt"), Path("file2.txt")]

        with pytest.raises(SystemExit):
            Cli.parse([])

        cli = Cli.parse(["file.txt"])
        assert cli.files == [Path("file.txt")]

        with pytest.raises(SystemExit):
            Cli.parse(["file1.txt", "--unknown"])

    def test_optional_list(self):
        @clap.command
        class Cli(clap.Parser):
            tags: Optional[list[str]] = arg(long, num_args="*")

        cli = Cli.parse([])
        assert cli.tags is None

        cli = Cli.parse(["--tags"])
        assert cli.tags == []

        cli = Cli.parse(["--tags", "tag1", "tag2"])
        assert cli.tags == ["tag1", "tag2"]

    def test_list_with_default_value(self):
        @clap.command
        class Cli(clap.Parser):
            values: list[int] = arg(long, default_value=[1, 2, 3], num_args="*")

        cli = Cli.parse([])
        assert cli.values == [1, 2, 3]

        cli = Cli.parse(["--values"])
        assert cli.values == []

        cli = Cli.parse(["--values", "4", "5", "6"])
        assert cli.values == [4, 5, 6]

        cli = Cli.parse(["--values", "4", "5", "--values", "6"])
        assert cli.values == [4, 5, 6]


class TestTupleArguments(unittest.TestCase):
    def test_three_elements(self):
        @clap.command
        class Cli(clap.Parser):
            color: tuple[int, int, int]

        cli = Cli.parse(["255", "128", "0"])
        assert cli.color == (255, 128, 0)

        with pytest.raises(SystemExit):
            Cli.parse([])

        with pytest.raises(SystemExit):
            Cli.parse(["255", "128"])

        with pytest.raises(SystemExit):
            Cli.parse(["255", "128", "0", "255"])

        with pytest.raises(SystemExit):
            Cli.parse(["255", "not_a_number", "0"])

    def test_nargs_mismatch_error(self):
        @clap.command
        class Cli(clap.Parser):
            point: tuple[int, int] = arg(num_args=3)

        with pytest.raises(SystemExit):
            Cli.parse()

    def test_optional_tuple(self):
        @clap.command
        class Cli(clap.Parser):
            size: Optional[tuple[int, int]] = arg(long, num_args=2)

        cli = Cli.parse([])
        assert cli.size is None

        cli = Cli.parse(["--size", "800", "600"])
        assert cli.size == (800, 600)

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
