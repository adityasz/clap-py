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

        cli = Cli.parse(["create", "test-name"])
        assert isinstance(cli.command, Create)
        assert cli.command.name == "test-name"

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

        cli = Cli.parse(["create", "test-name"])
        assert isinstance(cli.command, Create)
        assert cli.command.name == "test-name"

        cli = Cli.parse(["delete", "test-name", "--force"])
        if not isinstance(cli.command, Delete):
            self.fail()
        assert cli.command.name == "test-name"
        assert cli.command.force

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

        cli = Cli.parse([
            "process",
            "input.txt",
            "--output",
            "out.txt",
            "-v",
            "--threads",
            "4",
        ])
        assert isinstance(cli.command, Process)
        assert cli.command.input_file == Path("input.txt")
        assert cli.command.output == Path("out.txt")
        assert cli.command.verbose
        assert cli.command.threads == 4

    def test_optional_subcommand(self):
        @clap.subcommand
        class Action:
            target: str

        @clap.command
        class Cli(clap.Parser):
            command: Optional[Action]

        cli = Cli.parse(["action", "target-name"])
        if not isinstance(cli.command, Action):
            self.fail()
        assert cli.command.target == "target-name"

        cli = Cli.parse([])
        assert cli.command is None


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

        cli = Cli.parse(["stash", "push", "--message", "work in progress"])
        assert isinstance(cli.command, Stash)
        if not isinstance(cli.command.subcommand, Push):
            self.fail()
        assert cli.command.subcommand.message == "work in progress"

        cli = Cli.parse(["stash", "pop", "--index", "0"])
        assert isinstance(cli.command, Stash)
        if not isinstance(cli.command.subcommand, Pop):
            self.fail()
        assert cli.command.subcommand.index == 0

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

        cli = Cli.parse(["system", "service", "status", "--verbose"])
        assert isinstance(cli.command, System)
        assert isinstance(cli.command.component, Service)
        if not isinstance(cli.command.component.action, Status):
            self.fail()
        assert cli.command.component.action.verbose

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

        cli = Cli.parse(["database", "add-item", "key", "value"])
        if not isinstance(cli.command, Database):
            self.fail()
        if not isinstance(cli.command.operation, AddItem):
            self.fail()
        assert cli.command.operation.name == "key"
        assert cli.command.operation.value == "value"

        cli = Cli.parse(["status", "--verbose"])
        if not isinstance(cli.command, Status):
            self.fail()
        assert cli.command.verbose


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

        cli = Cli.parse(["create-project", "my-app"])
        if not isinstance(cli.command, CreateProject):
            self.fail()
        assert cli.command.name == "my-app"

        cli = Cli.parse(["delete-all", "--confirm"])
        if not isinstance(cli.command, DeleteAll):
            self.fail()
        assert cli.command.confirm

    def test_subcommand_with_custom_name(self):
        @clap.subcommand(name="ls")
        class ListFiles:
            directory: str = arg(num_args="?", default_value=".")

        @clap.command
        class Cli(clap.Parser):
            command: ListFiles

        cli = Cli.parse(["ls", "/tmp"])
        assert isinstance(cli.command, ListFiles)
        assert cli.command.directory == "/tmp"

    def test_subcommand_with_aliases(self):
        @clap.subcommand(aliases=("rm", "del"))
        class Remove:
            target: str

        @clap.command
        class Cli(clap.Parser):
            command: Remove

        cli = Cli.parse(["remove", "file.txt"])
        assert isinstance(cli.command, Remove)
        assert cli.command.target == "file.txt"

        cli = Cli.parse(["rm", "file.txt"])
        assert isinstance(cli.command, Remove)
        assert cli.command.target == "file.txt"

        cli = Cli.parse(["del", "file.txt"])
        assert isinstance(cli.command, Remove)
        assert cli.command.target == "file.txt"


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

        cli = Cli.parse(["--verbose", "action", "target-name"])
        assert cli.verbose
        assert not cli.command.verbose
        assert isinstance(cli.command, Action)
        assert cli.command.target == "target-name"

        cli = Cli.parse(["--verbose", "action", "target-name", "--verbose"])
        assert cli.verbose
        assert cli.command.verbose
        assert isinstance(cli.command, Action)
        assert cli.command.target == "target-name"

    def test_subcommand_with_enums(self):
        from clap import ColorChoice

        @clap.subcommand
        class Configure:
            color: ColorChoice

        @clap.command
        class Cli(clap.Parser):
            command: Configure

        cli = Cli.parse(["configure", "always"])
        assert isinstance(cli.command, Configure)
        assert cli.command.color == ColorChoice.Always

    def test_subcommand_with_lists(self):
        @clap.subcommand
        class Process:
            files: list[str] = arg(num_args="+")
            exclude: list[str] = arg(long, num_args="*")

        @clap.command
        class Cli(clap.Parser):
            command: Process

        cli = Cli.parse(["process", "file1.txt", "file2.txt", "--exclude", "tmp", "cache"])
        assert isinstance(cli.command, Process)
        assert cli.command.files == ["file1.txt", "file2.txt"]
        assert cli.command.exclude == ["tmp", "cache"]


if __name__ == "__main__":
    unittest.main()
