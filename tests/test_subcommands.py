import unittest
from pathlib import Path
from typing import Optional, Union

import clap
from clap import arg, long, short


class TestBasicSubcommands(unittest.TestCase):
    def test_simple_subcommand(self):
        @clap.subcommand
        class Create:
            name: str

        @clap.command
        class Cli(clap.Parser):
            command: Create

        args = Cli.parse_args(["create", "test-name"])
        self.assertIsInstance(args.command, Create)
        self.assertEqual(args.command.name, "test-name")

    def test_multiple_subcommands(self):
        @clap.subcommand
        class Create:
            name: str

        @clap.subcommand
        class Delete:
            name: str
            force: bool = arg(long)

        @clap.command
        class Cli(clap.Parser):
            command: Union[Create, Delete]

        args = Cli.parse_args(["create", "test-name"])
        self.assertIsInstance(args.command, Create)
        self.assertEqual(args.command.name, "test-name")

        args = Cli.parse_args(["delete", "test-name", "--force"])
        if not isinstance(args.command, Delete):
            self.fail()
        self.assertEqual(args.command.name, "test-name")
        self.assertTrue(args.command.force)

    def test_subcommand_with_options(self):
        @clap.subcommand
        class Process:
            input_file: Path
            output: Optional[Path] = arg(long)
            verbose: bool = arg(short, long)
            threads: int = arg(long, default_value=1)

        @clap.command
        class Cli(clap.Parser):
            command: Process

        args = Cli.parse_args([
            "process",
            "input.txt",
            "--output",
            "out.txt",
            "-v",
            "--threads",
            "4",
        ])
        self.assertIsInstance(args.command, Process)
        self.assertEqual(args.command.input_file, Path("input.txt"))
        self.assertEqual(args.command.output, Path("out.txt"))
        self.assertTrue(args.command.verbose)
        self.assertEqual(args.command.threads, 4)

    def test_optional_subcommand(self):
        @clap.subcommand
        class Action:
            target: str

        @clap.command
        class Cli(clap.Parser):
            command: Optional[Action]

        args = Cli.parse_args(["action", "target-name"])
        if not isinstance(args.command, Action):
            self.fail()
        self.assertEqual(args.command.target, "target-name")

        args = Cli.parse_args([])
        self.assertIsNone(args.command)


class TestNestedSubcommands(unittest.TestCase):
    def test_two_level_nested_subcommands(self):
        @clap.subcommand
        class Push:
            message: Optional[str] = arg(long)

        @clap.subcommand
        class Pop:
            index: Optional[int] = arg(long)

        @clap.subcommand
        class Stash:
            subcommand: Union[Push, Pop]

        @clap.command
        class Cli(clap.Parser):
            command: Stash

        args = Cli.parse_args(["stash", "push", "--message", "work in progress"])
        self.assertIsInstance(args.command, Stash)
        if not isinstance(args.command.subcommand, Push):
            self.fail()
        self.assertEqual(args.command.subcommand.message, "work in progress")

        args = Cli.parse_args(["stash", "pop", "--index", "0"])
        self.assertIsInstance(args.command, Stash)
        if not isinstance(args.command.subcommand, Pop):
            self.fail()
        self.assertEqual(args.command.subcommand.index, 0)

    def test_three_level_nested_subcommands(self):
        @clap.subcommand
        class Status:
            verbose: bool = arg(short, long)

        @clap.subcommand
        class Start:
            service: str

        @clap.subcommand
        class Service:
            action: Union[Status, Start]

        @clap.subcommand
        class System:
            component: Service

        @clap.command
        class Cli(clap.Parser):
            command: System

        args = Cli.parse_args(["system", "service", "status", "--verbose"])
        self.assertIsInstance(args.command, System)
        self.assertIsInstance(args.command.component, Service)
        if not isinstance(args.command.component.action, Status):
            self.fail()
        self.assertTrue(args.command.component.action.verbose)

    def test_mixed_nested_and_flat_subcommands(self):
        @clap.subcommand
        class ListItems:
            pattern: Optional[str] = arg(long)

        @clap.subcommand
        class AddItem:
            name: str
            value: str

        @clap.subcommand
        class Database:
            operation: Union[ListItems, AddItem]

        @clap.subcommand
        class Status:
            verbose: bool = arg(long)

        @clap.command
        class Cli(clap.Parser):
            command: Union[Database, Status]

        args = Cli.parse_args(["database", "add-item", "key", "value"])
        if not isinstance(args.command, Database):
            self.fail()
        if not isinstance(args.command.operation, AddItem):
            self.fail()
        self.assertEqual(args.command.operation.name, "key")
        self.assertEqual(args.command.operation.value, "value")

        args = Cli.parse_args(["status", "--verbose"])
        if not isinstance(args.command, Status):
            self.fail()
        self.assertTrue(args.command.verbose)


class TestSubcommandNamingAndAliases(unittest.TestCase):
    def test_automatic_naming_conversion(self):
        @clap.subcommand
        class CreateProject:
            name: str

        @clap.subcommand
        class DeleteAll:
            confirm: bool = arg(long)

        @clap.command
        class Cli(clap.Parser):
            command: Union[CreateProject, DeleteAll]

        args = Cli.parse_args(["create-project", "my-app"])
        if not isinstance(args.command, CreateProject):
            self.fail()
        self.assertEqual(args.command.name, "my-app")

        args = Cli.parse_args(["delete-all", "--confirm"])
        if not isinstance(args.command, DeleteAll):
            self.fail()
        self.assertTrue(args.command.confirm)

    def test_subcommand_with_custom_name(self):
        @clap.subcommand(name="ls")
        class ListFiles:
            directory: str = arg(num_args="?", default_value=".")

        @clap.command
        class Cli(clap.Parser):
            command: ListFiles

        args = Cli.parse_args(["ls", "/tmp"])
        self.assertIsInstance(args.command, ListFiles)
        self.assertEqual(args.command.directory, "/tmp")

    def test_subcommand_with_aliases(self):
        @clap.subcommand(aliases=("rm", "del"))
        class Remove:
            target: str

        @clap.command
        class Cli(clap.Parser):
            command: Remove

        args = Cli.parse_args(["remove", "file.txt"])
        self.assertIsInstance(args.command, Remove)
        self.assertEqual(args.command.target, "file.txt")

        args = Cli.parse_args(["rm", "file.txt"])
        self.assertIsInstance(args.command, Remove)
        self.assertEqual(args.command.target, "file.txt")

        args = Cli.parse_args(["del", "file.txt"])
        self.assertIsInstance(args.command, Remove)
        self.assertEqual(args.command.target, "file.txt")


class TestSubcommandErrors(unittest.TestCase):
    def test_subcommand_mixed_types(self):
        with self.assertRaises(TypeError):
            @clap.command
            class _:
                @clap.subcommand
                class SubCmd:
                    ...

                cmd: Union[SubCmd, str]

    def test_multiple_subcommand_destinations(self):
        """Test error when multiple subcommand destinations are defined."""
        with self.assertRaises(TypeError):
            @clap.command
            class _:
                @clap.subcommand
                class Sub1:
                    pass

                @clap.subcommand
                class Sub2:
                    pass

                cmd1: Sub1
                cmd2: Sub2

    def test_subcommand_field_assignment(self):
        """Test error when assigning value to subcommand field."""
        with self.assertRaises(TypeError):
            @clap.command
            class _:
                @clap.subcommand
                class Sub:
                    ...

                cmd: Sub = "invalid"  # type: ignore

    def test_unknown_subcommand(self):
        @clap.subcommand
        class Valid:
            arg: str

        @clap.command
        class Cli(clap.Parser):
            command: Valid

        with self.assertRaises(SystemExit):
            Cli.parse_args(["invalid", "arg"])

    def test_missing_required_subcommand(self):
        @clap.subcommand
        class Required:
            arg: str

        @clap.command
        class Cli(clap.Parser):
            command: Required

        with self.assertRaises(SystemExit):
            Cli.parse_args([])

    def test_subcommand_with_invalid_args(self):
        @clap.subcommand
        class Command:
            count: int

        @clap.command
        class Cli(clap.Parser):
            command: Command

        with self.assertRaises(SystemExit):
            Cli.parse_args(["command", "not_a_number"])

    def test_missing_arguments_to_subcommand(self):
        @clap.subcommand
        class Command:
            required_arg: str

        @clap.command
        class Cli(clap.Parser):
            command: Command

        with self.assertRaises(SystemExit):
            Cli.parse_args(["command"])


class TestSubcommandIntegration(unittest.TestCase):
    def test_subcommand_with_global_options(self):
        @clap.subcommand
        class Action:
            target: str
            verbose: bool = arg(short, long)

        @clap.command
        class Cli(clap.Parser):
            verbose: bool = arg(short, long)
            command: Action

        args = Cli.parse_args(["--verbose", "action", "target-name"])
        self.assertTrue(args.verbose)
        self.assertFalse(args.command.verbose)
        self.assertIsInstance(args.command, Action)
        self.assertEqual(args.command.target, "target-name")

        args = Cli.parse_args(["--verbose", "action", "target-name", "--verbose"])
        self.assertTrue(args.verbose)
        self.assertTrue(args.command.verbose)
        self.assertIsInstance(args.command, Action)
        self.assertEqual(args.command.target, "target-name")

    def test_subcommand_with_enums(self):
        from clap import ColorChoice

        @clap.subcommand
        class Configure:
            color: ColorChoice

        @clap.command
        class Cli(clap.Parser):
            command: Configure

        args = Cli.parse_args(["configure", "always"])
        self.assertIsInstance(args.command, Configure)
        self.assertEqual(args.command.color, ColorChoice.Always)

    def test_subcommand_with_lists(self):
        @clap.subcommand
        class Process:
            files: list[str] = arg(num_args="+")
            exclude: list[str] = arg(long, num_args="*")

        @clap.command
        class Cli(clap.Parser):
            command: Process

        args = Cli.parse_args(["process", "file1.txt", "file2.txt", "--exclude", "tmp", "cache"])
        self.assertIsInstance(args.command, Process)
        self.assertEqual(args.command.files, ["file1.txt", "file2.txt"])
        self.assertEqual(args.command.exclude, ["tmp", "cache"])


if __name__ == "__main__":
    unittest.main()
