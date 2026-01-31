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

        cli = Cli.parse(["/tmp/test.txt"])
        assert cli.file == Path("/tmp/test.txt")

        with pytest.raises(SystemExit):
            Cli.parse([])

        with pytest.raises(SystemExit):
            Cli.parse(["/tmp/test.txt", "extra.txt"])

    def test_optional_positional(self):
        @clap.command
        class Cli(clap.Parser):
            file: Optional[Path]

        cli = Cli.parse(["/tmp/test.txt"])
        assert cli.file == Path("/tmp/test.txt")

        cli = Cli.parse([])
        assert cli.file is None

        with pytest.raises(SystemExit):
            Cli.parse(["/tmp/test.txt", "extra.txt"])

    def test_flag_handling_with_manual_flags(self):
        @clap.command
        class Cli(clap.Parser):
            verbose: bool = arg(short="v", long="verbose")

        cli = Cli.parse([])
        assert not cli.verbose

        cli = Cli.parse(["-v"])
        assert cli.verbose

        cli = Cli.parse(["--verbose"])
        assert cli.verbose

        with pytest.raises(SystemExit):
            Cli.parse(["-x"])

        with pytest.raises(SystemExit):
            Cli.parse(["--verbose", "true"])

    def test_flag_handling_with_hyphenated_flags(self):
        @clap.command
        class Cli(clap.Parser):
            verbose: bool = arg(short="-v", long="--verbose")

        cli = Cli.parse([])
        assert not cli.verbose

        cli = Cli.parse(["-v"])
        assert cli.verbose

        cli = Cli.parse(["--verbose"])
        assert cli.verbose

        with pytest.raises(SystemExit):
            Cli.parse(["--unknown"])

    def test_flag_handling_with_bools(self):
        @clap.command
        class Cli(clap.Parser):
            verbose: bool = arg(short=True, long=True)

        cli = Cli.parse([])
        assert not cli.verbose

        cli = Cli.parse(["-v"])
        assert cli.verbose

        cli = Cli.parse(["--verbose"])
        assert cli.verbose

        with pytest.raises(SystemExit):
            Cli.parse(["--unknown"])

    def test_flag_handling_with_short_long(self):
        @clap.command
        class Cli(clap.Parser):
            verbose: bool = arg(short, long)

        cli = Cli.parse([])
        assert not cli.verbose

        cli = Cli.parse(["-v"])
        assert cli.verbose

        cli = Cli.parse(["--verbose"])
        assert cli.verbose

    def test_option_with_value(self):
        @clap.command
        class Cli(clap.Parser):
            output: Optional[str] = arg(long)

        cli = Cli.parse(["--output", "file.txt"])
        assert cli.output == "file.txt"

        cli = Cli.parse([])
        assert cli.output is None

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

        cli = Cli.parse(["input.txt", "--output", "output.txt", "-v"])
        assert cli.input_file == Path("input.txt")
        assert cli.output_file == Path("output.txt")
        assert cli.verbose

        cli = Cli.parse(["input.txt"])
        assert cli.input_file == Path("input.txt")
        assert cli.output_file is None
        assert not cli.verbose

        with pytest.raises(SystemExit):
            Cli.parse(["--output", "output.txt", "-v"])

        with pytest.raises(SystemExit):
            Cli.parse(["--output", "output.txt", "input.txt", "--invalid"])

    def test_argument_with_default_value(self):
        @clap.command
        class Cli(clap.Parser):
            asdf: int = arg(default_value=42)

        cli = Cli.parse([])
        assert cli.asdf == 42

        cli = Cli.parse(["100"])
        assert cli.asdf == 100

        with pytest.raises(SystemExit):
            Cli.parse(["string"])

    def test_option_with_default_value(self):
        @clap.command
        class Cli(clap.Parser):
            asdf: int = arg(long, default_value=42)

        cli = Cli.parse([])
        assert cli.asdf == 42

        cli = Cli.parse(["--asdf", "100"])
        assert cli.asdf == 100

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

        cli = Cli.parse([])
        assert cli.output == "file.txt"

        cli = Cli.parse(["--output"])
        assert cli.output == "stdout"

        cli = Cli.parse(["--output", "custom.txt"])
        assert cli.output == "custom.txt"

        with pytest.raises(SystemExit):
            Cli.parse(["--unknown"])

        with pytest.raises(SystemExit):
            Cli.parse(["--output", "custom.txt", "extra"])


if __name__ == "__main__":
    unittest.main()
