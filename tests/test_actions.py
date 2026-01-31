import unittest
from typing import Optional

import pytest

import clap
from clap import ArgAction, arg, long, short


class TestActions(unittest.TestCase):
    def test_optional_positional_with_num_args_plus(self):
        """Test error for optional positional with incompatible num_args."""

        @clap.command
        class Cli(clap.Parser):
            files: Optional[list[str]] = arg(num_args="+")

        cli = Cli.parse([])
        assert cli.files is None

        cli = Cli.parse(["one"])
        assert cli.files == ["one"]

        cli = Cli.parse(["one", "two"])
        assert cli.files == ["one", "two"]

    def test_store_const_action(self):
        @clap.command
        class Cli(clap.Parser):
            mode: Optional[str] = arg(long, default_missing_value="debug", num_args=0)

        cli = Cli.parse([])
        assert cli.mode is None

        cli = Cli.parse(["--mode"])
        assert cli.mode == "debug"

        with pytest.raises(SystemExit):
            Cli.parse(["--mode", "extra_arg"])

    def test_append_action_optional_type(self):
        @clap.command
        class Cli(clap.Parser):
            include: Optional[list[str]] = arg(short="I", action=ArgAction.Append)

        cli = Cli.parse(["-I", "path1", "-I", "path2", "-I", "path3"])
        assert cli.include == ["path1", "path2", "path3"]

        cli = Cli.parse([])
        assert cli.include is None

        with pytest.raises(SystemExit):
            Cli.parse(["-I"])

    def test_count_action(self):
        @clap.command
        class Cli(clap.Parser):
            verbose: int = arg(short, action=ArgAction.Count)

        cli = Cli.parse([])
        assert cli.verbose == 0

        cli = Cli.parse(["-v"])
        assert cli.verbose == 1

        cli = Cli.parse(["-vvv"])
        assert cli.verbose == 3

        with pytest.raises(SystemExit):
            Cli.parse(["-x"])

    def test_store_false_action(self):
        @clap.command
        class Cli(clap.Parser):
            no_cache: bool = arg(long, action=ArgAction.SetFalse, default_value=True)

        cli = Cli.parse([])
        assert cli.no_cache

        cli = Cli.parse(["--no-cache"])
        assert not cli.no_cache

        with pytest.raises(SystemExit):
            Cli.parse(["--no-cache", "false"])

    def test_append_action(self):
        @clap.command
        class Cli(clap.Parser):
            libs: list[str] = arg(short, action=ArgAction.Append)

        cli = Cli.parse([])
        assert cli.libs == []

        cli = Cli.parse(["-l", "lib1", "-l", "lib2"])
        assert cli.libs == ["lib1", "lib2"]

        with pytest.raises(SystemExit):
            Cli.parse(["-l"])

    def test_append_action_with_explicit_default(self):
        @clap.command
        class Cli(clap.Parser):
            flags: list[str] = arg(long, action=ArgAction.Append, default_value=["default"])

        cli = Cli.parse([])
        assert cli.flags == ["default"]

        cli = Cli.parse(["--flags", "custom"])
        assert cli.flags == ["default", "custom"]

        with pytest.raises(SystemExit):
            Cli.parse(["--invalid-flag", "value"])

    def test_append_const_action(self):
        @clap.command
        class Cli(clap.Parser):
            features: list[str] = arg(
                long="enable-feature",
                action=ArgAction.Append,
                num_args=0,
                default_missing_value="feature1",
            )

        cli = Cli.parse([])
        assert cli.features == []

        cli = Cli.parse(["--enable-feature", "--enable-feature"])
        assert cli.features == ["feature1", "feature1"]

        with pytest.raises(SystemExit):
            Cli.parse(["--enable-feature", "value"])

    def test_extend_action(self):
        @clap.command
        class Cli(clap.Parser):
            items: list[str] = arg(long, num_args="+")

        cli = Cli.parse([])
        assert cli.items == []

        cli = Cli.parse(["--items", "a", "b", "--items", "c", "d"])
        assert cli.items == ["a", "b", "c", "d"]

        with pytest.raises(SystemExit):
            Cli.parse(["--items"])

    def test_store_const_with_required(self):
        @clap.command
        class Cli(clap.Parser):
            mode: str = arg(long, default_missing_value="production", num_args=0)

        cli = Cli.parse(["--mode"])
        assert cli.mode == "production"

        with pytest.raises(SystemExit):
            Cli.parse([])

        with pytest.raises(SystemExit):
            Cli.parse(["--unknown"])

    def test_store_true_false_defaults(self):
        @clap.command
        class Cli(clap.Parser):
            enable: bool = arg(long, action=ArgAction.SetTrue)
            disable: bool = arg(long, action=ArgAction.SetFalse)

        cli = Cli.parse([])
        assert not cli.enable
        assert cli.disable

        cli = Cli.parse(["--enable", "--disable"])
        assert cli.enable
        assert not cli.disable

        with pytest.raises(SystemExit):
            Cli.parse(["--enable", "true"])

    def test_count_action_with_default(self):
        @clap.command
        class Cli(clap.Parser):
            level: int = arg(short="l", action=ArgAction.Count, default_value=5)

        cli = Cli.parse([])
        assert cli.level == 5

        cli = Cli.parse(["-ll"])
        assert cli.level == 7

        with pytest.raises(SystemExit):
            Cli.parse(["-lx"])

    def test_multiple_action_combinations(self):
        @clap.command
        class Cli(clap.Parser):
            verbose: int = arg(short="v", action=ArgAction.Count)
            debug: bool = arg(long, action=ArgAction.SetTrue)
            includes: list[str] = arg(short="I", action=ArgAction.Append)
            features: list[str] = arg(
                long="feature",
                action=ArgAction.Append,
                default_missing_value="enabled",
                num_args=0,
            )

        cli = Cli.parse(["-vv", "--debug", "-I", "lib1", "-I", "lib2", "--feature"])
        assert cli.verbose == 2
        assert cli.debug
        assert cli.includes == ["lib1", "lib2"]
        assert cli.features == ["enabled"]

        cli = Cli.parse([])
        assert cli.verbose == 0
        assert not cli.debug
        assert cli.includes == []
        assert cli.features == []

        with pytest.raises(SystemExit):
            Cli.parse(["-I"])


class TestActionTypeErrors(unittest.TestCase):
    def test_count_with_optional_type_error(self):
        @clap.command
        class Cli(clap.Parser):
            count: Optional[int] = arg(short="c", action=ArgAction.Count)

        with pytest.raises(SystemExit):
            Cli.parse()

    def test_store_true_with_optional_type_error(self):
        @clap.command
        class Cli(clap.Parser):
            flag: Optional[bool] = arg(long, action=ArgAction.SetTrue)

        with pytest.raises(SystemExit):
            Cli.parse()

    def test_store_false_with_optional_type_error(self):
        @clap.command
        class Cli(clap.Parser):
            flag: Optional[bool] = arg(long, action=ArgAction.SetFalse)

        with pytest.raises(SystemExit):
            Cli.parse()

    def test_store_const_with_optional_and_default_error(self):
        @clap.command
        class Cli(clap.Parser):
            mode: Optional[str] = arg(
                long,
                action=ArgAction.Set,
                default_missing_value="test",
                num_args=0,
                default_value="default",
            )

        with pytest.raises(SystemExit):
            Cli.parse()

    def test_store_with_required_and_optional_error(self):
        @clap.command
        class Cli(clap.Parser):
            value: Optional[str] = arg(long, action=ArgAction.Set, required=True)

        with pytest.raises(SystemExit):
            Cli.parse()

    def test_store_with_default_and_optional_error(self):
        @clap.command
        class Cli(clap.Parser):
            value: Optional[str] = arg(long, action=ArgAction.Set, default_value="test")

        with pytest.raises(SystemExit):
            Cli.parse()


if __name__ == "__main__":
    unittest.main()
