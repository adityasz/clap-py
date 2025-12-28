import unittest
from pathlib import Path
from typing import Optional, Union, cast

import pytest

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

        args = Cli.parse(["create", "test-name"])
        assert isinstance(args.command, Create)
        assert args.command.name == "test-name"

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

        args = Cli.parse(["create", "test-name"])
        assert isinstance(args.command, Create)
        assert args.command.name == "test-name"

        args = Cli.parse(["delete", "test-name", "--force"])
        if not isinstance(args.command, Delete):
            self.fail()
        assert args.command.name == "test-name"
        assert args.command.force

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

        args = Cli.parse([
            "process",
            "input.txt",
            "--output",
            "out.txt",
            "-v",
            "--threads",
            "4",
        ])
        assert isinstance(args.command, Process)
        assert args.command.input_file == Path("input.txt")
        assert args.command.output == Path("out.txt")
        assert args.command.verbose
        assert args.command.threads == 4

    def test_optional_subcommand(self):
        @clap.subcommand
        class Action:
            target: str

        @clap.command
        class Cli(clap.Parser):
            command: Optional[Action]

        args = Cli.parse(["action", "target-name"])
        if not isinstance(args.command, Action):
            self.fail()
        assert args.command.target == "target-name"

        args = Cli.parse([])
        assert args.command is None


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

        args = Cli.parse(["stash", "push", "--message", "work in progress"])
        assert isinstance(args.command, Stash)
        if not isinstance(args.command.subcommand, Push):
            self.fail()
        assert args.command.subcommand.message == "work in progress"

        args = Cli.parse(["stash", "pop", "--index", "0"])
        assert isinstance(args.command, Stash)
        if not isinstance(args.command.subcommand, Pop):
            self.fail()
        assert args.command.subcommand.index == 0

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

        args = Cli.parse(["system", "service", "status", "--verbose"])
        assert isinstance(args.command, System)
        assert isinstance(args.command.component, Service)
        if not isinstance(args.command.component.action, Status):
            self.fail()
        assert args.command.component.action.verbose

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

        args = Cli.parse(["database", "add-item", "key", "value"])
        if not isinstance(args.command, Database):
            self.fail()
        if not isinstance(args.command.operation, AddItem):
            self.fail()
        assert args.command.operation.name == "key"
        assert args.command.operation.value == "value"

        args = Cli.parse(["status", "--verbose"])
        if not isinstance(args.command, Status):
            self.fail()
        assert args.command.verbose


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

        args = Cli.parse(["create-project", "my-app"])
        if not isinstance(args.command, CreateProject):
            self.fail()
        assert args.command.name == "my-app"

        args = Cli.parse(["delete-all", "--confirm"])
        if not isinstance(args.command, DeleteAll):
            self.fail()
        assert args.command.confirm

    def test_subcommand_with_custom_name(self):
        @clap.subcommand(name="ls")
        class ListFiles:
            directory: str = arg(num_args="?", default_value=".")

        @clap.command
        class Cli(clap.Parser):
            command: ListFiles

        args = Cli.parse(["ls", "/tmp"])
        assert isinstance(args.command, ListFiles)
        assert args.command.directory == "/tmp"

    def test_subcommand_with_aliases(self):
        @clap.subcommand(aliases=("rm", "del"))
        class Remove:
            target: str

        @clap.command
        class Cli(clap.Parser):
            command: Remove

        args = Cli.parse(["remove", "file.txt"])
        assert isinstance(args.command, Remove)
        assert args.command.target == "file.txt"

        args = Cli.parse(["rm", "file.txt"])
        assert isinstance(args.command, Remove)
        assert args.command.target == "file.txt"

        args = Cli.parse(["del", "file.txt"])
        assert isinstance(args.command, Remove)
        assert args.command.target == "file.txt"


class TestSubcommandErrors(unittest.TestCase):
    def test_subcommand_mixed_types(self):
        @clap.command
        class Cli(clap.Parser):
            @clap.subcommand
            class SubCmd: ...

            cmd: Union[SubCmd, str]

        with pytest.raises(SystemExit):
            Cli.parse()

    def test_multiple_subcommand_destinations(self):
        """Test error when multiple subcommand destinations are defined."""

        @clap.command
        class Cli(clap.Parser):
            @clap.subcommand
            class Sub1:
                pass

            @clap.subcommand
            class Sub2:
                pass

            cmd1: Sub1
            cmd2: Sub2

        with pytest.raises(SystemExit):
            Cli.parse()

    def test_subcommand_field_assignment(self):
        """Test error when assigning value to subcommand field."""

        @clap.command
        class Cli(clap.Parser):
            @clap.subcommand
            class Sub: ...

            cmd: Sub = cast(Sub, "invalid")

        with pytest.raises(SystemExit):
            Cli.parse()

    def test_unknown_subcommand(self):
        @clap.subcommand
        class Valid:
            arg: str

        @clap.command
        class Cli(clap.Parser):
            command: Valid

        with pytest.raises(SystemExit):
            Cli.parse(["invalid", "arg"])

    def test_missing_required_subcommand(self):
        @clap.subcommand
        class Required:
            arg: str

        @clap.command
        class Cli(clap.Parser):
            command: Required

        with pytest.raises(SystemExit):
            Cli.parse([])

    def test_subcommand_with_invalid_args(self):
        @clap.subcommand
        class Command:
            count: int

        @clap.command
        class Cli(clap.Parser):
            command: Command

        with pytest.raises(SystemExit):
            Cli.parse(["command", "not_a_number"])

    def test_missing_arguments_to_subcommand(self):
        @clap.subcommand
        class Command:
            required_arg: str

        @clap.command
        class Cli(clap.Parser):
            command: Command

        with pytest.raises(SystemExit):
            Cli.parse(["command"])


class TestSubcommandIntegration(unittest.TestCase):
    def test_subcommand_with_global_options(self):
        @clap.subcommand
        class Action:
            target: str
            verbose: bool = arg(short, long)

        @clap.command
        class Cli(clap.Parser):
            command: Action
            verbose: bool = arg(short, long)

        args = Cli.parse(["--verbose", "action", "target-name"])
        assert args.verbose
        assert not args.command.verbose
        assert isinstance(args.command, Action)
        assert args.command.target == "target-name"

        args = Cli.parse(["--verbose", "action", "target-name", "--verbose"])
        assert args.verbose
        assert args.command.verbose
        assert isinstance(args.command, Action)
        assert args.command.target == "target-name"

    def test_subcommand_with_enums(self):
        from clap import ColorChoice

        @clap.subcommand
        class Configure:
            color: ColorChoice

        @clap.command
        class Cli(clap.Parser):
            command: Configure

        args = Cli.parse(["configure", "always"])
        assert isinstance(args.command, Configure)
        assert args.command.color == ColorChoice.Always

    def test_subcommand_with_lists(self):
        @clap.subcommand
        class Process:
            files: list[str] = arg(num_args="+")
            exclude: list[str] = arg(long, num_args="*")

        @clap.command
        class Cli(clap.Parser):
            command: Process

        args = Cli.parse(["process", "file1.txt", "file2.txt", "--exclude", "tmp", "cache"])
        assert isinstance(args.command, Process)
        assert args.command.files == ["file1.txt", "file2.txt"]
        assert args.command.exclude == ["tmp", "cache"]


if __name__ == "__main__":
    unittest.main()
