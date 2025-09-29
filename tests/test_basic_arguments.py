"""Tests for basic argument parsing functionality."""

import unittest
from pathlib import Path
from typing import Optional

import pytest

import clap
from clap import arg, long, short


class TestBasicArgumentParsing(unittest.TestCase):
    def test_positional(self):
        @clap.command
        class Cli(clap.Parser):
            file: Path

        args = Cli.parse(["/tmp/test.txt"])
        assert args.file == Path("/tmp/test.txt")

        with pytest.raises(SystemExit):
            Cli.parse([])

        with pytest.raises(SystemExit):
            Cli.parse(["/tmp/test.txt", "extra.txt"])

    def test_optional_positional(self):
        @clap.command
        class Cli(clap.Parser):
            file: Optional[Path]

        args = Cli.parse(["/tmp/test.txt"])
        assert args.file == Path("/tmp/test.txt")

        args = Cli.parse([])
        assert args.file is None

        with pytest.raises(SystemExit):
            Cli.parse(["/tmp/test.txt", "extra.txt"])

    def test_bool_flag_with_manual_flags(self):
        @clap.command
        class Cli(clap.Parser):
            verbose: bool = arg(short="v", long="verbose")

        args = Cli.parse([])
        assert not args.verbose

        args = Cli.parse(["-v"])
        assert args.verbose

        args = Cli.parse(["--verbose"])
        assert args.verbose

        with pytest.raises(SystemExit):
            Cli.parse(["-x"])

        with pytest.raises(SystemExit):
            Cli.parse(["--verbose", "true"])

    def test_bool_flag_with_hyphenated_flags(self):
        @clap.command
        class Cli(clap.Parser):
            verbose: bool = arg(short="-v", long="--verbose")

        args = Cli.parse([])
        assert not args.verbose

        args = Cli.parse(["-v"])
        assert args.verbose

        args = Cli.parse(["--verbose"])
        assert args.verbose

        with pytest.raises(SystemExit):
            Cli.parse(["--unknown"])

    def test_bool_flag_with_short_long(self):
        @clap.command
        class Cli(clap.Parser):
            verbose: bool = arg(short, long)

        args = Cli.parse([])
        assert not args.verbose

        args = Cli.parse(["-v"])
        assert args.verbose

        args = Cli.parse(["--verbose"])
        assert args.verbose

    def test_option_with_value(self):
        @clap.command
        class Cli(clap.Parser):
            output: Optional[str] = arg(long)

        args = Cli.parse(["--output", "file.txt"])
        assert args.output == "file.txt"

        args = Cli.parse([])
        assert args.output is None

        with pytest.raises(SystemExit):
            Cli.parse(["--output"])

        with pytest.raises(SystemExit):
            Cli.parse(["--invalid", "value"])

    def test_multiple_arguments_mixed(self):
        @clap.command
        class Cli(clap.Parser):
            input_file: Path
            output_file: Optional[Path] = arg(long, value_name="<PATH>")
            verbose: bool = arg(short, long)

        args = Cli.parse(["input.txt", "--output", "output.txt", "-v"])
        assert args.input_file == Path("input.txt")
        assert args.output_file == Path("output.txt")
        assert args.verbose

        args = Cli.parse(["input.txt"])
        assert args.input_file == Path("input.txt")
        assert args.output_file is None
        assert not args.verbose

        with pytest.raises(SystemExit):
            Cli.parse(["--output", "output.txt", "-v"])

        with pytest.raises(SystemExit):
            Cli.parse(["--output", "output.txt", "input.txt", "--invalid"])

    def test_argument_with_default_value(self):
        @clap.command
        class Cli(clap.Parser):
            asdf: int = arg(default_value=42)

        args = Cli.parse([])
        assert args.asdf == 42

        args = Cli.parse(["100"])
        assert args.asdf == 100

        with pytest.raises(SystemExit):
            Cli.parse(["string"])

    def test_option_with_default_value(self):
        @clap.command
        class Cli(clap.Parser):
            asdf: int = arg(long, default_value=42)

        args = Cli.parse([])
        assert args.asdf == 42

        args = Cli.parse(["--asdf", "100"])
        assert args.asdf == 100

        with pytest.raises(SystemExit):
            Cli.parse(["--asdf", "not_a_number"])

        with pytest.raises(SystemExit):
            Cli.parse(["--asdf"])

    def test_const_default(self):
        @clap.command
        class Cli(clap.Parser):
            output: str = arg(
                long, num_args="?", default_missing_value="stdout", default_value="file.txt"
            )

        args = Cli.parse([])
        assert args.output == "file.txt"

        args = Cli.parse(["--output"])
        assert args.output == "stdout"

        args = Cli.parse(["--output", "custom.txt"])
        assert args.output == "custom.txt"

        with pytest.raises(SystemExit):
            Cli.parse(["--unknown"])

        with pytest.raises(SystemExit):
            Cli.parse(["--output", "custom.txt", "extra"])


if __name__ == "__main__":
    unittest.main()
