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

        args = Cli.parse([])
        assert args.files is None

        args = Cli.parse(["one"])
        assert args.files == ["one"]

        args = Cli.parse(["one", "two"])
        assert args.files == ["one", "two"]

    def test_store_const_action(self):
        @clap.command
        class Cli(clap.Parser):
            mode: Optional[str] = arg(long, default_missing_value="debug", num_args=0)

        args = Cli.parse([])
        assert args.mode is None

        args = Cli.parse(["--mode"])
        assert args.mode == "debug"

        with pytest.raises(SystemExit):
            Cli.parse(["--mode", "extra_arg"])

    def test_append_action_optional_type(self):
        @clap.command
        class Cli(clap.Parser):
            include: Optional[list[str]] = arg(short="I", action=ArgAction.Append)

        args = Cli.parse(["-I", "path1", "-I", "path2", "-I", "path3"])
        assert args.include == ["path1", "path2", "path3"]

        args = Cli.parse([])
        assert args.include is None

        with pytest.raises(SystemExit):
            Cli.parse(["-I"])

    def test_count_action(self):
        @clap.command
        class Cli(clap.Parser):
            verbose: int = arg(short, action=ArgAction.Count)

        args = Cli.parse([])
        assert args.verbose == 0

        args = Cli.parse(["-v"])
        assert args.verbose == 1

        args = Cli.parse(["-vvv"])
        assert args.verbose == 3

        with pytest.raises(SystemExit):
            Cli.parse(["-x"])

    def test_store_false_action(self):
        @clap.command
        class Cli(clap.Parser):
            no_cache: bool = arg(long, action=ArgAction.SetFalse, default_value=True)

        args = Cli.parse([])
        assert args.no_cache

        args = Cli.parse(["--no-cache"])
        assert not args.no_cache

        with pytest.raises(SystemExit):
            Cli.parse(["--no-cache", "false"])

    def test_append_action(self):
        @clap.command
        class Cli(clap.Parser):
            libs: list[str] = arg(short, action=ArgAction.Append)

        args = Cli.parse([])
        assert args.libs == []

        args = Cli.parse(["-l", "lib1", "-l", "lib2"])
        assert args.libs == ["lib1", "lib2"]

        with pytest.raises(SystemExit):
            Cli.parse(["-l"])

    def test_append_action_with_explicit_default(self):
        @clap.command
        class Cli(clap.Parser):
            flags: list[str] = arg(long, action=ArgAction.Append, default_value=["default"])

        args = Cli.parse([])
        assert args.flags == ["default"]

        args = Cli.parse(["--flags", "custom"])
        assert args.flags == ["default", "custom"]

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

        args = Cli.parse([])
        assert args.features == []

        args = Cli.parse(["--enable-feature", "--enable-feature"])
        assert args.features == ["feature1", "feature1"]

        with pytest.raises(SystemExit):
            Cli.parse(["--enable-feature", "value"])

    def test_extend_action(self):
        @clap.command
        class Cli(clap.Parser):
            items: list[str] = arg(long, num_args="+")

        args = Cli.parse([])
        assert args.items == []

        args = Cli.parse(["--items", "a", "b", "--items", "c", "d"])
        assert args.items == ["a", "b", "c", "d"]

        with pytest.raises(SystemExit):
            Cli.parse(["--items"])

    def test_store_const_with_required(self):
        @clap.command
        class Cli(clap.Parser):
            mode: str = arg(long, default_missing_value="production", num_args=0)

        args = Cli.parse(["--mode"])
        assert args.mode == "production"

        with pytest.raises(SystemExit):
            Cli.parse([])

        with pytest.raises(SystemExit):
            Cli.parse(["--unknown"])

    def test_store_true_false_defaults(self):
        @clap.command
        class Cli(clap.Parser):
            enable: bool = arg(long, action=ArgAction.SetTrue)
            disable: bool = arg(long, action=ArgAction.SetFalse)

        args = Cli.parse([])
        assert not args.enable
        assert args.disable

        args = Cli.parse(["--enable", "--disable"])
        assert args.enable
        assert not args.disable

        with pytest.raises(SystemExit):
            Cli.parse(["--enable", "true"])

    def test_count_action_with_default(self):
        @clap.command
        class Cli(clap.Parser):
            level: int = arg(short="l", action=ArgAction.Count, default_value=5)

        args = Cli.parse([])
        assert args.level == 5

        args = Cli.parse(["-ll"])
        assert args.level == 7

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

        args = Cli.parse(["-vv", "--debug", "-I", "lib1", "-I", "lib2", "--feature"])
        assert args.verbose == 2
        assert args.debug
        assert args.includes == ["lib1", "lib2"]
        assert args.features == ["enabled"]

        args = Cli.parse([])
        assert args.verbose == 0
        assert not args.debug
        assert args.includes == []
        assert args.features == []

        with pytest.raises(SystemExit):
            Cli.parse(["-I"])


class TestActionTypeErrors(unittest.TestCase):
    def test_count_with_optional_type_error(self):
        @clap.command
        class Cli(clap.Parser):
            count: Optional[int] = arg(short="c", action=ArgAction.Count)

        with pytest.raises(TypeError):
            Cli.parse()

    def test_store_true_with_optional_type_error(self):
        @clap.command
        class Cli(clap.Parser):
            flag: Optional[bool] = arg(long, action=ArgAction.SetTrue)

        with pytest.raises(TypeError):
            Cli.parse()

    def test_store_false_with_optional_type_error(self):
        @clap.command
        class Cli(clap.Parser):
            flag: Optional[bool] = arg(long, action=ArgAction.SetFalse)

        with pytest.raises(TypeError):
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

        with pytest.raises(TypeError):
            Cli.parse()

    def test_store_with_required_and_optional_error(self):
        @clap.command
        class Cli(clap.Parser):
            value: Optional[str] = arg(long, action=ArgAction.Set, required=True)

        with pytest.raises(TypeError):
            Cli.parse()

    def test_store_with_default_and_optional_error(self):
        @clap.command
        class Cli(clap.Parser):
            value: Optional[str] = arg(long, action=ArgAction.Set, default_value="test")

        with pytest.raises(TypeError):
            Cli.parse()


if __name__ == "__main__":
    unittest.main()
