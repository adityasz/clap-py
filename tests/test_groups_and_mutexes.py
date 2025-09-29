"""Tests for argument groups and mutually exclusive groups."""

import unittest
from typing import Optional

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
        self.assertEqual(args.input_file, "input.txt")
        self.assertTrue(args.verbose)
        self.assertTrue(args.debug)

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
        self.assertEqual(args.input_file, "input.txt")
        self.assertIsNone(args.input_dir)
        self.assertIsNone(args.output_file)
        self.assertEqual(args.output_dir, "out/")

        args = Cli.parse([])
        self.assertIsNone(args.input_file)
        self.assertIsNone(args.input_dir)
        self.assertIsNone(args.output_file)
        self.assertIsNone(args.output_dir)

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

        self.assertEqual(args.input_file, "input.txt")
        self.assertTrue(args.verbose)
        self.assertEqual(args.output_file, "out.txt")
        self.assertTrue(args.process)
        self.assertFalse(args.analyze)
        self.assertTrue(args.json_out)
        self.assertFalse(args.csv_out)

        with self.assertRaises(SystemExit):
            Cli.parse(["input.txt", "--verbose"])

        with self.assertRaises(SystemExit):
            Cli.parse(["input.txt", "--process", "--analyze"])

        with self.assertRaises(SystemExit):
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
        self.assertTrue(args.create)
        self.assertFalse(args.update)
        self.assertFalse(args.delete)

        args = Cli.parse(["--update"])
        self.assertFalse(args.create)
        self.assertTrue(args.update)
        self.assertFalse(args.delete)

        with self.assertRaises(SystemExit):
            Cli.parse(["--create", "--update"])

        with self.assertRaises(SystemExit):
            Cli.parse([])

        with self.assertRaises(SystemExit):
            Cli.parse(["--create", "--update", "--delete"])

    def test_optional_mutex_group(self):
        @clap.command
        class Cli(clap.Parser):
            mode_mutex = MutexGroup(required=False)

            create: bool = arg(long, mutex=mode_mutex)
            update: bool = arg(long, mutex=mode_mutex)

        args = Cli.parse([])
        self.assertFalse(args.create)
        self.assertFalse(args.update)

        with self.assertRaises(SystemExit):
            Cli.parse(["--create", "--update"])

    def test_mutex_with_values(self):
        @clap.command
        class Cli(clap.Parser):
            source_mutex = MutexGroup(required=True)

            file: Optional[str] = arg(long, mutex=source_mutex)
            url: Optional[str] = arg(long, mutex=source_mutex)
            stdin: bool = arg(long, mutex=source_mutex)

        args = Cli.parse(["--file", "input.txt"])
        self.assertEqual(args.file, "input.txt")
        self.assertIsNone(args.url)
        self.assertFalse(args.stdin)

        args = Cli.parse(["--url", "http://example.com"])
        self.assertIsNone(args.file)
        self.assertEqual(args.url, "http://example.com")
        self.assertFalse(args.stdin)

        with self.assertRaises(SystemExit):
            Cli.parse(["--file", "input.txt", "--stdin"])

        with self.assertRaises(SystemExit):
            Cli.parse(["--file"])

        with self.assertRaises(SystemExit):
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
        self.assertEqual(args.config_file, "config.txt")
        self.assertTrue(args.json_format)
        self.assertFalse(args.yaml_format)
        self.assertFalse(args.xml_format)

        with self.assertRaises(SystemExit):
            Cli.parse([])

        with self.assertRaises(SystemExit):
            Cli.parse(["--json-format", "--yaml-format"])

        with self.assertRaises(SystemExit):
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
        self.assertFalse(args.http)
        self.assertTrue(args.https)
        self.assertFalse(args.ftp)
        self.assertTrue(args.basic_auth)
        self.assertFalse(args.token_auth)
        self.assertEqual(args.timeout, 30)

        args = Cli.parse(["--https"])
        self.assertTrue(args.https)
        self.assertFalse(args.http)
        self.assertFalse(args.ftp)
        self.assertFalse(args.basic_auth)
        self.assertFalse(args.token_auth)
        self.assertEqual(args.timeout, None)

        with self.assertRaises(SystemExit):
            Cli.parse([])

        with self.assertRaises(SystemExit):
            Cli.parse(["--http", "--https"])

        with self.assertRaises(SystemExit):
            Cli.parse(["--https", "--basic-auth", "--token-auth"])

        with self.assertRaises(SystemExit):
            Cli.parse(["--https", "--timeout", "invalid"])

    def test_group_and_mutex_conflict_within_parent(self):
        @clap.command
        class Cli(clap.Parser):
            parent_group = Group(title="Parent Group")
            child_mutex = MutexGroup(parent=parent_group)

            option_a: bool = arg(long, mutex=child_mutex)
            option_b: bool = arg(long, mutex=child_mutex)

        with self.assertRaises(SystemExit):
            Cli.parse(["--option-a", "--option-b"])

        args = Cli.parse(["--option-a"])
        self.assertTrue(args.option_a)
        self.assertFalse(args.option_b)

        args = Cli.parse([])
        self.assertFalse(args.option_a)
        self.assertFalse(args.option_b)

    def test_mutex_parent_mismatch(self):
        with self.assertRaises(ValueError):
            @clap.command
            class _:
                g1 = Group("Group 1")
                g2 = Group("Group 2")
                m = MutexGroup(parent=g1)

                arg1: bool = arg(long, group=g2, mutex=m)


if __name__ == "__main__":
    unittest.main()
