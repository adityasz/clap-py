"""Tests for argument groups and mutually exclusive groups."""

import unittest
from typing import Optional

import clap
from clap import arg, group, long, mutex_group, short


class TestArgumentGroups(unittest.TestCase):
    def test_basic_argument_group(self):
        @clap.arguments
        class Cli(clap.Parser):
            input_file: str
            debug_group = group(title="Debug Options", description="Options for debugging")
            verbose: bool = arg(short, long, group=debug_group)
            debug: bool = arg(short, long, group=debug_group)

        args = Cli.parse_args(['input.txt', '--verbose', '--debug'])
        self.assertEqual(args.input_file, 'input.txt')
        self.assertTrue(args.verbose)
        self.assertTrue(args.debug)

    def test_multiple_groups(self):
        @clap.arguments
        class Cli(clap.Parser):
            input_group = group(title="Input Options")
            output_group = group(title="Output Options")

            input_file: Optional[str] = arg(long, group=input_group)
            input_dir: Optional[str] = arg(long, group=input_group)

            output_file: Optional[str] = arg(long, group=output_group)
            output_dir: Optional[str] = arg(long, group=output_group)

        args = Cli.parse_args(['--input-file', 'input.txt', '--output-dir', 'out/'])
        self.assertEqual(args.input_file, 'input.txt')
        self.assertIsNone(args.input_dir)
        self.assertIsNone(args.output_file)
        self.assertEqual(args.output_dir, 'out/')


class TestMutuallyExclusiveGroups(unittest.TestCase):
    def test_basic_mutex_group(self):
        @clap.arguments
        class Cli(clap.Parser):
            mode_mutex = mutex_group(required=True)

            create: bool = arg(long, mutex=mode_mutex)
            update: bool = arg(long, mutex=mode_mutex)
            delete: bool = arg(long, mutex=mode_mutex)

        args = Cli.parse_args(['--create'])
        self.assertTrue(args.create)
        self.assertFalse(args.update)
        self.assertFalse(args.delete)

        args = Cli.parse_args(['--update'])
        self.assertFalse(args.create)
        self.assertTrue(args.update)
        self.assertFalse(args.delete)

        with self.assertRaises(SystemExit):
            Cli.parse_args(['--create', '--update'])

        with self.assertRaises(SystemExit):
            Cli.parse_args([])

    def test_optional_mutex_group(self):
        @clap.arguments
        class Cli(clap.Parser):
            mode_mutex = mutex_group(required=False)

            create: bool = arg(long, mutex=mode_mutex)
            update: bool = arg(long, mutex=mode_mutex)

        args = Cli.parse_args([])
        self.assertFalse(args.create)
        self.assertFalse(args.update)

    def test_mutex_with_values(self):
        @clap.arguments
        class Cli(clap.Parser):
            source_mutex = mutex_group(required=True)

            file: Optional[str] = arg(long, mutex=source_mutex)
            url: Optional[str] = arg(long, mutex=source_mutex)
            stdin: bool = arg(long, mutex=source_mutex)

        args = Cli.parse_args(['--file', 'input.txt'])
        self.assertEqual(args.file, 'input.txt')
        self.assertIsNone(args.url)
        self.assertFalse(args.stdin)

        args = Cli.parse_args(['--url', 'http://example.com'])
        self.assertIsNone(args.file)
        self.assertEqual(args.url, 'http://example.com')
        self.assertFalse(args.stdin)


class TestGroupsWithMutexes(unittest.TestCase):
    def test_mutex_within_group(self):
        @clap.arguments
        class Cli(clap.Parser):
            config_group = group(title="Configuration Options")
            format_mutex = mutex_group(parent_group=config_group, required=True)

            config_file: Optional[str] = arg(long, group=config_group)

            json_format: bool = arg(long, mutex=format_mutex)
            yaml_format: bool = arg(long, mutex=format_mutex)
            xml_format: bool = arg(long, mutex=format_mutex)

        args = Cli.parse_args(['--config-file', 'config.txt', '--json-format'])
        self.assertEqual(args.config_file, 'config.txt')
        self.assertTrue(args.json_format)
        self.assertFalse(args.yaml_format)
        self.assertFalse(args.xml_format)

        with self.assertRaises(SystemExit):
            Cli.parse_args([])

    def test_multiple_mutexes_in_group(self):
        @clap.arguments
        class Cli(clap.Parser):
            network_group = group(title="Network Options")

            protocol_mutex = mutex_group(parent_group=network_group, required=True)
            auth_mutex = mutex_group(parent_group=network_group, required=False)

            http: bool = arg(long, mutex=protocol_mutex)
            https: bool = arg(long, mutex=protocol_mutex)
            ftp: bool = arg(long, mutex=protocol_mutex)

            basic_auth: bool = arg(long, mutex=auth_mutex)
            token_auth: bool = arg(long, mutex=auth_mutex)

            timeout: Optional[int] = arg(long, group=network_group)

        args = Cli.parse_args(['--https', '--basic-auth', '--timeout', '30'])
        self.assertFalse(args.http)
        self.assertTrue(args.https)
        self.assertFalse(args.ftp)
        self.assertTrue(args.basic_auth)
        self.assertFalse(args.token_auth)
        self.assertEqual(args.timeout, 30)

        args = Cli.parse_args(['--https'])
        self.assertTrue(args.https)
        self.assertFalse(args.http)
        self.assertFalse(args.ftp)
        self.assertFalse(args.basic_auth)
        self.assertFalse(args.token_auth)
        self.assertEqual(args.timeout, None)

        with self.assertRaises(SystemExit):
            Cli.parse_args([])

    def test_group_and_mutex_conflict_within_parent(self):
        @clap.arguments
        class Cli(clap.Parser):
            parent_group = group(title="Parent Group")
            child_mutex = mutex_group(parent_group=parent_group)

            option_a: bool = arg(long, mutex=child_mutex)
            option_b: bool = arg(long, mutex=child_mutex)

        with self.assertRaises(SystemExit):
            Cli.parse_args(['--option-a', '--option-b'])


class TestComplexGroupScenarios(unittest.TestCase):
    def test_standalone_and_grouped_arguments(self):
        @clap.arguments
        class Cli(clap.Parser):
            input_file: str
            verbose: bool = arg(short, long)

            output_group = group(title="Output Options")
            output_file: Optional[str] = arg(long, group=output_group)

            mode_mutex = mutex_group(required=True)
            process: bool = arg(long, mutex=mode_mutex)
            analyze: bool = arg(long, mutex=mode_mutex)

            format_group = group(title="Format Options")
            format_mutex = mutex_group(parent_group=format_group)
            json_out: bool = arg(long, mutex=format_mutex)
            csv_out: bool = arg(long, mutex=format_mutex)

        args = Cli.parse_args([
            'input.txt', '--verbose', '--output-file', 'out.txt',
            '--process', '--json-out'
        ])

        self.assertEqual(args.input_file, 'input.txt')
        self.assertTrue(args.verbose)
        self.assertEqual(args.output_file, 'out.txt')
        self.assertTrue(args.process)
        self.assertFalse(args.analyze)
        self.assertTrue(args.json_out)
        self.assertFalse(args.csv_out)

    def test_nested_group_structure(self):
        @clap.arguments
        class Cli(clap.Parser):
            input_group = group(title="Input Options")
            processing_group = group(title="Processing Options")

            input_file: Optional[str] = arg(long, group=input_group)
            input_format_mutex = mutex_group(parent_group=input_group)
            auto_detect: bool = arg(long, mutex=input_format_mutex)
            force_json: bool = arg(long, mutex=input_format_mutex)

            threads: Optional[int] = arg(long, group=processing_group)
            algorithm_mutex = mutex_group(parent_group=processing_group, required=True)
            fast: bool = arg(long, mutex=algorithm_mutex)
            accurate: bool = arg(long, mutex=algorithm_mutex)

        args = Cli.parse_args([
            '--input-file', 'data.txt', '--auto-detect',
            '--threads', '4', '--fast'
        ])

        self.assertEqual(args.input_file, 'data.txt')
        self.assertTrue(args.auto_detect)
        self.assertFalse(args.force_json)
        self.assertEqual(args.threads, 4)
        self.assertTrue(args.fast)
        self.assertFalse(args.accurate)


if __name__ == '__main__':
    unittest.main()
