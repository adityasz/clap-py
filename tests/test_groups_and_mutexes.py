"""Tests for argument groups and mutually exclusive groups."""

import unittest
from typing import Optional

import pytest

import clap
from clap import Group, arg, long, short


class TestClassArgumentGroups(unittest.TestCase):
    def test_simple(self):
        @clap.group(title="Debug Options")
        class DebugOptions:
            verbose: bool = arg(short, long)
            debug: bool = arg(short, long)

        @clap.command
        class Cli(clap.Parser):
            input_file: str
            debug_group: DebugOptions

        cli = Cli.parse(["input.txt", "--verbose", "--debug"])
        assert cli.input_file == "input.txt"
        assert cli.debug_group.verbose
        assert cli.debug_group.debug

    def test_multiple(self):
        @clap.group(title="Input Options")
        class InputOptions:
            input_file: Optional[str] = arg(long)
            input_dir: Optional[str] = arg(long)

        @clap.group(title="Output Options")
        class OutputOptions:
            output_file: Optional[str] = arg(long)
            output_dir: Optional[str] = arg(long)

        @clap.command
        class Cli(clap.Parser):
            input_group: InputOptions
            output_group: OutputOptions

        cli = Cli.parse(["--input-file", "input.txt", "--output-dir", "out/"])
        assert cli.input_group.input_file == "input.txt"
        assert cli.input_group.input_dir is None
        assert cli.output_group.output_file is None
        assert cli.output_group.output_dir == "out/"

        cli = Cli.parse([])
        assert cli.input_group.input_file is None
        assert cli.input_group.input_dir is None
        assert cli.output_group.output_file is None
        assert cli.output_group.output_dir is None

    def test_ungrouped_and_mutex(self):
        @clap.group(title="Output Options")
        class OutputOptions:
            output_file: Optional[str] = arg(long)

        @clap.group(required=True, multiple=False)
        class ModeMutex:
            process: bool = arg(long)
            analyze: bool = arg(long)

        @clap.group(title="Format Options", multiple=False)
        class FormatMutex:
            json_out: bool = arg(long)
            csv_out: bool = arg(long)

        @clap.command
        class Cli(clap.Parser):
            input_file: str
            output_group: OutputOptions
            mode_mutex: ModeMutex
            format_mutex: FormatMutex
            verbose: bool = arg(short, long)

        cli = Cli.parse([
            "input.txt",
            "--verbose",
            "--output-file",
            "out.txt",
            "--process",
            "--json-out",
        ])

        assert cli.input_file == "input.txt"
        assert cli.verbose
        assert cli.output_group.output_file == "out.txt"
        assert cli.mode_mutex.process
        assert not cli.mode_mutex.analyze
        assert cli.format_mutex.json_out
        assert not cli.format_mutex.csv_out

        with pytest.raises(SystemExit):
            Cli.parse(["input.txt", "--verbose"])

        with pytest.raises(SystemExit):
            Cli.parse(["input.txt", "--process", "--analyze"])

        with pytest.raises(SystemExit):
            Cli.parse(["input.txt", "--process", "--json-out", "--csv-out"])

    def test_mutex_with_values(self):
        @clap.group(required=True, multiple=False)
        class SourceMutex:
            file: Optional[str] = arg(long)
            url: Optional[str] = arg(long)
            stdin: bool = arg(long)

        @clap.command
        class Cli(clap.Parser):
            source_mutex: SourceMutex

        cli = Cli.parse(["--file", "input.txt"])
        assert cli.source_mutex.file == "input.txt"
        assert cli.source_mutex.url is None
        assert not cli.source_mutex.stdin

        cli = Cli.parse(["--url", "http://example.com"])
        assert cli.source_mutex.file is None
        assert cli.source_mutex.url == "http://example.com"
        assert not cli.source_mutex.stdin

        with pytest.raises(SystemExit):
            Cli.parse(["--file", "input.txt", "--stdin"])

        with pytest.raises(SystemExit):
            Cli.parse(["--file"])

        with pytest.raises(SystemExit):
            Cli.parse([])

    def test_satisfy_type_checkers(self):
        @clap.group
        class RandomStuff:
            # The arg() is redundant at runtime but ensures that type checkers
            # see that this field is already initialized and hence RandomStuff()
            # will not raise eyebrows.
            #
            # For the runtime, the decorator injects a dummy __init__.
            bar: int = arg()
            verbose: bool = arg(long)

        @clap.command
        class Cli(clap.Parser):
            foo: int = arg()
            random_stuff: RandomStuff = RandomStuff()

        cli = Cli.parse(["1", "2", "--verbose"])
        assert cli.foo == 1
        assert cli.random_stuff.bar == 2
        assert cli.random_stuff.verbose

        cli = Cli.parse(["1", "2"])
        assert cli.foo == 1
        assert cli.random_stuff.bar == 2
        assert not cli.random_stuff.verbose

    def test_group_in_nested_subcommands(self):
        @clap.group
        class Args:
            arg: str

        @clap.subcommand
        class C:
            args: Args
            opt: bool = arg(long)

        @clap.subcommand
        class B:
            command: C
            args: Args

        @clap.subcommand
        class A:
            command: B

        @clap.command
        class Cli(clap.Parser):
            command: A

        cli = Cli.parse(["a", "b", "b", "c", "d"])
        assert not cli.command.command.command.opt
        assert cli.command.command.args.arg == "b"
        assert cli.command.command.command.args.arg == "d"

        cli = Cli.parse(["a", "b", "b", "c", "d", "--opt"])
        assert cli.command.command.command.opt
        assert cli.command.command.args.arg == "b"
        assert cli.command.command.command.args.arg == "d"

        with pytest.raises(SystemExit):
            Cli.parse([])


class TestFlattenedArgumentGroups(unittest.TestCase):
    def test_simple(self):
        @clap.command
        class Cli(clap.Parser):
            input_file: str
            debug_group = Group(title="Debug Options")
            verbose: bool = arg(short, long, group=debug_group)
            debug: bool = arg(short, long, group=debug_group)

        cli = Cli.parse(["input.txt", "--verbose", "--debug"])
        assert cli.input_file == "input.txt"
        assert cli.verbose
        assert cli.debug

    def test_multiple(self):
        @clap.command
        class Cli(clap.Parser):
            input_group = Group(title="Input Options")
            output_group = Group(title="Output Options")

            input_file: Optional[str] = arg(long, group=input_group)
            input_dir: Optional[str] = arg(long, group=input_group)

            output_file: Optional[str] = arg(long, group=output_group)
            output_dir: Optional[str] = arg(long, group=output_group)

        cli = Cli.parse(["--input-file", "input.txt", "--output-dir", "out/"])
        assert cli.input_file == "input.txt"
        assert cli.input_dir is None
        assert cli.output_file is None
        assert cli.output_dir == "out/"

        cli = Cli.parse([])
        assert cli.input_file is None
        assert cli.input_dir is None
        assert cli.output_file is None
        assert cli.output_dir is None

    def test_ungrouped_and_mutex(self):
        @clap.command
        class Cli(clap.Parser):
            input_file: str
            verbose: bool = arg(short, long)

            output_group = Group(title="Output Options")
            output_file: Optional[str] = arg(long, group=output_group)

            mode_mutex = Group(required=True, multiple=False)
            process: bool = arg(long, group=mode_mutex)
            analyze: bool = arg(long, group=mode_mutex)

            format_mutex = Group(title="Format Options", multiple=False)
            json_out: bool = arg(long, group=format_mutex)
            csv_out: bool = arg(long, group=format_mutex)

        cli = Cli.parse([
            "input.txt",
            "--verbose",
            "--output-file",
            "out.txt",
            "--process",
            "--json-out",
        ])

        assert cli.input_file == "input.txt"
        assert cli.verbose
        assert cli.output_file == "out.txt"
        assert cli.process
        assert not cli.analyze
        assert cli.json_out
        assert not cli.csv_out

        with pytest.raises(SystemExit):
            Cli.parse(["input.txt", "--verbose"])

        with pytest.raises(SystemExit):
            Cli.parse(["input.txt", "--process", "--analyze"])

        with pytest.raises(SystemExit):
            Cli.parse(["input.txt", "--process", "--json-out", "--csv-out"])

    def test_mutex_with_values(self):
        @clap.command
        class Cli(clap.Parser):
            source_mutex = Group(required=True, multiple=False)

            file: Optional[str] = arg(long, group=source_mutex)
            url: Optional[str] = arg(long, group=source_mutex)
            stdin: bool = arg(long, group=source_mutex)

        cli = Cli.parse(["--file", "input.txt"])
        assert cli.file == "input.txt"
        assert cli.url is None
        assert not cli.stdin

        cli = Cli.parse(["--url", "http://example.com"])
        assert cli.file is None
        assert cli.url == "http://example.com"
        assert not cli.stdin

        with pytest.raises(SystemExit):
            Cli.parse(["--file", "input.txt", "--stdin"])

        with pytest.raises(SystemExit):
            Cli.parse(["--file"])

        with pytest.raises(SystemExit):
            Cli.parse([])


if __name__ == "__main__":
    unittest.main()
