import unittest
from typing import Union

import pytest

from clap.core import Arg, to_kebab_case
from clap.help import extract_docstrings, get_help_from_docstring
from clap.parser import (
    parse_type_hint,
    set_flags,
    set_value_name,
)


class TestDocstringExtraction(unittest.TestCase):
    def test_annotated_fields(self):
        """Test DocstringExtractor with annotated fields."""

        class Foo:
            field1: str
            """Field 1 docstring"""
            field2: int
            """Field 2 docstring.

            Multi-line description here."""
            field3: bool

        docstrings = extract_docstrings(Foo)

        assert docstrings["field1"] == "Field 1 docstring"
        assert docstrings["field2"] == ("Field 2 docstring.\n\n    Multi-line description here.")
        assert "field3" not in docstrings

    def test_single_paragraph(self):
        """Test help extraction from single paragraph."""
        short, long_help = get_help_from_docstring("Simple help text.")
        assert short == "Simple help text"
        assert long_help == "Simple help text"

    def test_multiple_paragraphs(self):
        """Test help extraction from multiple paragraphs."""
        docstring = """First paragraph with period.

        Second paragraph with more details.
        This continues the second paragraph.

        Third paragraph here."""
        short_help, long_help = get_help_from_docstring(docstring)
        assert short_help == "First paragraph with period"
        expected_long = (
            "First paragraph with period.\n\n"
            "Second paragraph with more details. This continues the second paragraph.\n\n"
            "Third paragraph here."
        )
        assert long_help == expected_long

    def test_empty(self):
        """Test help extraction from empty docstring."""
        short_help, long_help = get_help_from_docstring("")
        assert short_help == ""
        assert long_help == ""

    def test_whitespace_only(self):
        """Test help extraction from whitespace-only docstring."""
        short_help, long_help = get_help_from_docstring("   \n  \n  ")
        assert short_help == ""
        assert long_help == ""


class TestTypeHintParsing(unittest.TestCase):
    def test_invalid_union(self):
        with pytest.raises(TypeError):
            parse_type_hint(Union[str, int, float])

    def test_heterogeneous_tuple(self):
        with pytest.raises(TypeError):
            parse_type_hint(tuple[str, int])

    def test_unsupported_type(self):
        with pytest.raises(TypeError):
            parse_type_hint(set[str])

    def test_none_only_union(self):
        with pytest.raises(TypeError):
            parse_type_hint(type(None))


class TestFlagSetting(unittest.TestCase):
    def test_set_flags_invalid_short_flag_length(self):
        arg_obj = Arg(short="abc")
        with pytest.raises(ValueError):  # noqa: PT011 until parser is written from scratch with good error messages
            set_flags(arg_obj, "test", "-")

    def test_set_flags_short_flag_with_prefix_char(self):
        arg_obj = Arg(short="--")
        with pytest.raises(ValueError):  # noqa: PT011 until parser is written from scratch with good error messages
            set_flags(arg_obj, "test", "-")

    def test_set_flags_long_flag_without_prefix(self):
        arg_obj = Arg(long="verbose")
        set_flags(arg_obj, "test", "-")
        assert arg_obj.long == "--verbose"


class TestValueNameGeneration(unittest.TestCase):
    def test_set_value_name_question_mark(self):
        arg_obj = Arg(num_args="?")
        set_value_name(arg_obj, "input")
        assert arg_obj.value_name == "[INPUT]"

    def test_set_value_name_star(self):
        arg_obj = Arg(num_args="*")
        set_value_name(arg_obj, "files")
        assert arg_obj.value_name == "[<FILES>...]"

    def test_set_value_name_plus(self):
        arg_obj = Arg(num_args="+")
        set_value_name(arg_obj, "items")
        assert arg_obj.value_name == "<ITEMS>..."

    def test_set_value_name_integer(self):
        arg_obj = Arg(num_args=3)
        set_value_name(arg_obj, "coord")
        assert arg_obj.value_name == "<COORD> <COORD> <COORD>"

    def test_set_value_name_no_action_clears_value_name(self):
        from clap.core import ArgAction

        arg_obj = Arg(action=ArgAction.SetTrue)
        set_value_name(arg_obj, "flag")
        assert arg_obj.value_name is None


class TestKebabCaseConversion(unittest.TestCase):
    def test_pascal_case(self):
        assert to_kebab_case("PascalCase") == "pascal-case"
        assert to_kebab_case("HTTPSConnection") == "https-connection"
        assert to_kebab_case("XMLHttpRequest") == "xml-http-request"

    def test_camel_case(self):
        assert to_kebab_case("camelCase") == "camel-case"
        assert to_kebab_case("camelCaseFoo") == "camel-case-foo"

    def test_snake_case(self):
        assert to_kebab_case("snake_case") == "snake-case"
        assert to_kebab_case("get_user_id") == "get-user-id"
        assert to_kebab_case("a_b_c") == "a-b-c"
        assert to_kebab_case("a_b__c_") == "a-b-c"

    def test_screaming_snake_case(self):
        assert to_kebab_case("SCREAMING_SNAKE_CASE") == "screaming-snake-case"
        assert to_kebab_case("_MAX__RETRY___COUNT__") == "max-retry-count"

    def test_mixed_cases(self):
        assert to_kebab_case("Option_Four") == "option-four"
        assert to_kebab_case("HAtom") == "h-atom"
        assert to_kebab_case("APIKey_Value") == "api-key-value"

    def test_edge_cases(self):
        assert to_kebab_case("A") == "a"
        assert to_kebab_case("AB") == "ab"
        assert to_kebab_case("ABC") == "abc"
        assert to_kebab_case("ABc") == "a-bc"
        assert to_kebab_case("AbC") == "ab-c"
        assert to_kebab_case("a") == "a"
        assert to_kebab_case("aB") == "a-b"
        assert to_kebab_case("") == ""
        assert to_kebab_case("option1") == "option-1"
        assert to_kebab_case("Option1Two") == "option-1-two"

    def test_already_kebab_case(self):
        assert to_kebab_case("kebab-case") == "kebab-case"
        assert to_kebab_case("HAtom") == "h-atom"
        assert to_kebab_case("test--case") == "test-case"
        assert to_kebab_case("---test---") == "test"


if __name__ == "__main__":
    unittest.main()
