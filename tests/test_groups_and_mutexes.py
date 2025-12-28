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

        args = Cli.parse(["input.txt", "--verbose", "--debug"])
        assert args.input_file == "input.txt"
        assert args.debug_group.verbose
        assert args.debug_group.debug

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

        args = Cli.parse(["--input-file", "input.txt", "--output-dir", "out/"])
        assert args.input_group.input_file == "input.txt"
        assert args.input_group.input_dir is None
        assert args.output_group.output_file is None
        assert args.output_group.output_dir == "out/"

        args = Cli.parse([])
        assert args.input_group.input_file is None
        assert args.input_group.input_dir is None
        assert args.output_group.output_file is None
        assert args.output_group.output_dir is None

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

        args = Cli.parse([
            "input.txt",
            "--verbose",
            "--output-file",
            "out.txt",
            "--process",
            "--json-out",
        ])

        assert args.input_file == "input.txt"
        assert args.verbose
        assert args.output_group.output_file == "out.txt"
        assert args.mode_mutex.process
        assert not args.mode_mutex.analyze
        assert args.format_mutex.json_out
        assert not args.format_mutex.csv_out

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

        args = Cli.parse(["--file", "input.txt"])
        assert args.source_mutex.file == "input.txt"
        assert args.source_mutex.url is None
        assert not args.source_mutex.stdin

        args = Cli.parse(["--url", "http://example.com"])
        assert args.source_mutex.file is None
        assert args.source_mutex.url == "http://example.com"
        assert not args.source_mutex.stdin

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

        args = Cli.parse(["1", "2", "--verbose"])
        assert args.foo == 1
        assert args.random_stuff.bar == 2
        assert args.random_stuff.verbose

        args = Cli.parse(["1", "2"])
        assert args.foo == 1
        assert args.random_stuff.bar == 2
        assert not args.random_stuff.verbose

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

        args = Cli.parse(["a", "b", "b", "c", "d"])
        assert not args.command.command.command.opt
        assert args.command.command.args.arg == "b"
        assert args.command.command.command.args.arg == "d"

        args = Cli.parse(["a", "b", "b", "c", "d", "--opt"])
        assert args.command.command.command.opt
        assert args.command.command.args.arg == "b"
        assert args.command.command.command.args.arg == "d"

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

        args = Cli.parse(["input.txt", "--verbose", "--debug"])
        assert args.input_file == "input.txt"
        assert args.verbose
        assert args.debug

    def test_multiple(self):
        @clap.command
        class Cli(clap.Parser):
            input_group = Group(title="Input Options")
            output_group = Group(title="Output Options")

            input_file: Optional[str] = arg(long, group=input_group)
            input_dir: Optional[str] = arg(long, group=input_group)

            output_file: Optional[str] = arg(long, group=output_group)
            output_dir: Optional[str] = arg(long, group=output_group)

        args = Cli.parse(["--input-file", "input.txt", "--output-dir", "out/"])
        assert args.input_file == "input.txt"
        assert args.input_dir is None
        assert args.output_file is None
        assert args.output_dir == "out/"

        args = Cli.parse([])
        assert args.input_file is None
        assert args.input_dir is None
        assert args.output_file is None
        assert args.output_dir is None

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

        args = Cli.parse([
            "input.txt",
            "--verbose",
            "--output-file",
            "out.txt",
            "--process",
            "--json-out",
        ])

        assert args.input_file == "input.txt"
        assert args.verbose
        assert args.output_file == "out.txt"
        assert args.process
        assert not args.analyze
        assert args.json_out
        assert not args.csv_out

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

        args = Cli.parse(["--file", "input.txt"])
        assert args.file == "input.txt"
        assert args.url is None
        assert not args.stdin

        args = Cli.parse(["--url", "http://example.com"])
        assert args.file is None
        assert args.url == "http://example.com"
        assert not args.stdin

        with pytest.raises(SystemExit):
            Cli.parse(["--file", "input.txt", "--stdin"])

        with pytest.raises(SystemExit):
            Cli.parse(["--file"])

        with pytest.raises(SystemExit):
            Cli.parse([])


if __name__ == "__main__":
    unittest.main()
