"""Tests for argument groups and mutually exclusive groups."""

import unittest
from typing import Optional

import pytest

import clap
from clap import Group, MutexGroup, arg, long, short


class TestArgumentGroups(unittest.TestCase):
    def test_basic_argument_group(self):
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

    def test_multiple_groups(self):
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

    def test_standalone_and_grouped_arguments(self):
        @clap.command
        class Cli(clap.Parser):
            input_file: str
            verbose: bool = arg(short, long)

            output_group = Group(title="Output Options")
            output_file: Optional[str] = arg(long, group=output_group)

            mode_mutex = MutexGroup(required=True)
            process: bool = arg(long, mutex=mode_mutex)
            analyze: bool = arg(long, mutex=mode_mutex)

            format_group = Group(title="Format Options")
            format_mutex = MutexGroup(parent=format_group)
            json_out: bool = arg(long, mutex=format_mutex)
            csv_out: bool = arg(long, mutex=format_mutex)

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


class TestMutuallyExclusiveGroups(unittest.TestCase):
    def test_basic_mutex_group(self):
        @clap.command
        class Cli(clap.Parser):
            mode_mutex = MutexGroup(required=True)

            create: bool = arg(long, mutex=mode_mutex)
            update: bool = arg(long, mutex=mode_mutex)
            delete: bool = arg(long, mutex=mode_mutex)

        args = Cli.parse(["--create"])
        assert args.create
        assert not args.update
        assert not args.delete

        args = Cli.parse(["--update"])
        assert not args.create
        assert args.update
        assert not args.delete

        with pytest.raises(SystemExit):
            Cli.parse(["--create", "--update"])

        with pytest.raises(SystemExit):
            Cli.parse([])

        with pytest.raises(SystemExit):
            Cli.parse(["--create", "--update", "--delete"])

    def test_optional_mutex_group(self):
        @clap.command
        class Cli(clap.Parser):
            mode_mutex = MutexGroup(required=False)

            create: bool = arg(long, mutex=mode_mutex)
            update: bool = arg(long, mutex=mode_mutex)

        args = Cli.parse([])
        assert not args.create
        assert not args.update

        with pytest.raises(SystemExit):
            Cli.parse(["--create", "--update"])

    def test_mutex_with_values(self):
        @clap.command
        class Cli(clap.Parser):
            source_mutex = MutexGroup(required=True)

            file: Optional[str] = arg(long, mutex=source_mutex)
            url: Optional[str] = arg(long, mutex=source_mutex)
            stdin: bool = arg(long, mutex=source_mutex)

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


class TestGroupsWithMutexes(unittest.TestCase):
    def test_mutex_within_group(self):
        @clap.command
        class Cli(clap.Parser):
            config_group = Group(title="Configuration Options")
            format_mutex = MutexGroup(parent=config_group, required=True)

            config_file: Optional[str] = arg(long, group=config_group)

            json_format: bool = arg(long, mutex=format_mutex)
            yaml_format: bool = arg(long, mutex=format_mutex)
            xml_format: bool = arg(long, mutex=format_mutex)

        args = Cli.parse(["--config-file", "config.txt", "--json-format"])
        assert args.config_file == "config.txt"
        assert args.json_format
        assert not args.yaml_format
        assert not args.xml_format

        with pytest.raises(SystemExit):
            Cli.parse([])

        with pytest.raises(SystemExit):
            Cli.parse(["--json-format", "--yaml-format"])

        with pytest.raises(SystemExit):
            Cli.parse(["--config-file", "config.txt"])

    def test_multiple_mutexes_in_group(self):
        @clap.command
        class Cli(clap.Parser):
            network_group = Group(title="Network Options")

            protocol_mutex = MutexGroup(parent=network_group, required=True)
            auth_mutex = MutexGroup(parent=network_group, required=False)

            http: bool = arg(long, mutex=protocol_mutex)
            https: bool = arg(long, mutex=protocol_mutex)
            ftp: bool = arg(long, mutex=protocol_mutex)

            basic_auth: bool = arg(long, mutex=auth_mutex)
            token_auth: bool = arg(long, mutex=auth_mutex)

            timeout: Optional[int] = arg(long, group=network_group)

        args = Cli.parse(["--https", "--basic-auth", "--timeout", "30"])
        assert not args.http
        assert args.https
        assert not args.ftp
        assert args.basic_auth
        assert not args.token_auth
        assert args.timeout == 30

        args = Cli.parse(["--https"])
        assert args.https
        assert not args.http
        assert not args.ftp
        assert not args.basic_auth
        assert not args.token_auth
        assert args.timeout is None

        with pytest.raises(SystemExit):
            Cli.parse([])

        with pytest.raises(SystemExit):
            Cli.parse(["--http", "--https"])

        with pytest.raises(SystemExit):
            Cli.parse(["--https", "--basic-auth", "--token-auth"])

        with pytest.raises(SystemExit):
            Cli.parse(["--https", "--timeout", "invalid"])

    def test_group_and_mutex_conflict_within_parent(self):
        @clap.command
        class Cli(clap.Parser):
            parent_group = Group(title="Parent Group")
            child_mutex = MutexGroup(parent=parent_group)

            option_a: bool = arg(long, mutex=child_mutex)
            option_b: bool = arg(long, mutex=child_mutex)

        with pytest.raises(SystemExit):
            Cli.parse(["--option-a", "--option-b"])

        args = Cli.parse(["--option-a"])
        assert args.option_a
        assert not args.option_b

        args = Cli.parse([])
        assert not args.option_a
        assert not args.option_b

    def test_mutex_parent_mismatch(self):
        with pytest.raises(ValueError):  # noqa: PT011 until parser is written from scratch with good error messages
            @clap.command
            class _:
                g1 = Group("Group 1")
                g2 = Group("Group 2")
                m = MutexGroup(parent=g1)

                arg1: bool = arg(long, group=g2, mutex=m)


if __name__ == "__main__":
    unittest.main()
