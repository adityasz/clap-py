import ast
import unittest
from textwrap import dedent
from typing import Union

from clap.core import Arg, to_kebab_case
from clap.parser import (
    DocstringExtractor,
    get_help_from_docstring,
    parse_type_hint,
    set_flags,
    set_value_name,
)


class TestDocstringExtraction(unittest.TestCase):
    def test_annotated_fields(self):
        """Test DocstringExtractor with annotated fields."""
        source = '''
        class TestClass:
            field1: str
            """Field 1 docstring"""
            field2: int
            """Field 2 docstring.

            Multi-line description here."""
            field3: bool
        '''
        tree = ast.parse(dedent(source))
        extractor = DocstringExtractor()
        extractor.visit(tree)

        self.assertEqual(extractor.docstrings["field1"], "Field 1 docstring")
        self.assertEqual(extractor.docstrings["field2"],
                         "Field 2 docstring.\n\n    Multi-line description here.")
        self.assertNotIn("field3", extractor.docstrings)

    def test_group_docs(self):
        """Test DocstringExtractor with assigned fields (groups)."""
        source = '''
        class TestClass:
            group1 = Group("Input options")
            """Group 1 description"""
            field2 = arg(long)
        '''
        tree = ast.parse(dedent(source))
        extractor = DocstringExtractor()
        extractor.visit(tree)

        self.assertEqual(extractor.docstrings["group1"], "Group 1 description")
        self.assertNotIn("field2", extractor.docstrings)

    def test_single_paragraph(self):
        """Test help extraction from single paragraph."""
        short, long_help = get_help_from_docstring("Simple help text.")
        self.assertEqual(short, "Simple help text")
        self.assertEqual(long_help, "Simple help text")

    def test_multiple_paragraphs(self):
        """Test help extraction from multiple paragraphs."""
        docstring = """First paragraph with period.

        Second paragraph with more details.
        This continues the second paragraph.

        Third paragraph here."""
        short_help, long_help = get_help_from_docstring(docstring)
        self.assertEqual(short_help, "First paragraph with period")
        expected_long = (
            "First paragraph with period.\n\n"
            "Second paragraph with more details. This continues the second paragraph.\n\n"
            "Third paragraph here.")
        self.assertEqual(long_help, expected_long)

    def test_empty(self):
        """Test help extraction from empty docstring."""
        short_help, long_help = get_help_from_docstring("")
        self.assertEqual(short_help, "")
        self.assertEqual(long_help, "")

    def test_whitespace_only(self):
        """Test help extraction from whitespace-only docstring."""
        short_help, long_help = get_help_from_docstring("   \n  \n  ")
        self.assertEqual(short_help, "")
        self.assertEqual(long_help, "")


class TestTypeHintParsing(unittest.TestCase):
    def test_invalid_union(self):
        with self.assertRaises(TypeError):
            parse_type_hint(Union[str, int, float])

    def test_heterogeneous_tuple(self):
        with self.assertRaises(TypeError):
            parse_type_hint(tuple[str, int])

    def test_unsupported_type(self):
        with self.assertRaises(TypeError):
            parse_type_hint(set[str])

    def test_none_only_union(self):
        with self.assertRaises(TypeError):
            parse_type_hint(Union[type(None), type(None)])


class TestFlagSetting(unittest.TestCase):
    def test_set_flags_invalid_short_flag_length(self):
        arg_obj = Arg(short="abc")
        with self.assertRaises(ValueError):
            set_flags(arg_obj, "test", "-")

    def test_set_flags_short_flag_with_prefix_char(self):
        arg_obj = Arg(short="--")
        with self.assertRaises(ValueError):
            set_flags(arg_obj, "test", "-")

    def test_set_flags_long_flag_without_prefix(self):
        arg_obj = Arg(long="verbose")
        set_flags(arg_obj, "test", "-")
        self.assertEqual(arg_obj.long, "--verbose")


class TestValueNameGeneration(unittest.TestCase):
    def test_set_value_name_question_mark(self):
        arg_obj = Arg(num_args="?")
        set_value_name(arg_obj, "input")
        self.assertEqual(arg_obj.value_name, "[INPUT]")

    def test_set_value_name_star(self):
        arg_obj = Arg(num_args="*")
        set_value_name(arg_obj, "files")
        self.assertEqual(arg_obj.value_name, "[<FILES>...]")

    def test_set_value_name_plus(self):
        arg_obj = Arg(num_args="+")
        set_value_name(arg_obj, "items")
        self.assertEqual(arg_obj.value_name, "<ITEMS>...")

    def test_set_value_name_integer(self):
        arg_obj = Arg(num_args=3)
        set_value_name(arg_obj, "coord")
        self.assertEqual(arg_obj.value_name, "<COORD> <COORD> <COORD>")

    def test_set_value_name_no_action_clears_value_name(self):
        from clap.core import ArgAction
        arg_obj = Arg(action=ArgAction.SetTrue)
        set_value_name(arg_obj, "flag")
        self.assertIsNone(arg_obj.value_name)


class TestKebabCaseConversion(unittest.TestCase):
    def test_pascal_case(self):
        self.assertEqual(to_kebab_case("PascalCase"), "pascal-case")
        self.assertEqual(to_kebab_case("HTTPSConnection"), "https-connection")
        self.assertEqual(to_kebab_case("XMLHttpRequest"), "xml-http-request")

    def test_camel_case(self):
        self.assertEqual(to_kebab_case("camelCase"), "camel-case")

    def test_snake_case(self):
        self.assertEqual(to_kebab_case("snake_case"), "snake-case")
        self.assertEqual(to_kebab_case("get_user_id"), "get-user-id")
        self.assertEqual(to_kebab_case("a_b_c"), "a-b-c")
        self.assertEqual(to_kebab_case("a_b__c_"), "a-b-c")

    def test_screaming_snake_case(self):
        self.assertEqual(to_kebab_case("SCREAMING_SNAKE_CASE"), "screaming-snake-case")
        self.assertEqual(to_kebab_case("_MAX__RETRY___COUNT__"), "max-retry-count")

    def test_mixed_cases(self):
        self.assertEqual(to_kebab_case("Option_Four"), "option-four")
        self.assertEqual(to_kebab_case("HAtom"), "h-atom")
        self.assertEqual(to_kebab_case("APIKey_Value"), "api-key-value")

    def test_edge_cases(self):
        self.assertEqual(to_kebab_case("A"), "a")
        self.assertEqual(to_kebab_case("AB"), "ab")
        self.assertEqual(to_kebab_case("ABC"), "abc")
        self.assertEqual(to_kebab_case("ABc"), "a-bc")
        self.assertEqual(to_kebab_case("AbC"), "ab-c")
        self.assertEqual(to_kebab_case("a"), "a")
        self.assertEqual(to_kebab_case("aB"), "a-b")
        self.assertEqual(to_kebab_case(""), "")
        self.assertEqual(to_kebab_case("option1"), "option1")
        self.assertEqual(to_kebab_case("Option1Two"), "option1-two")

    def test_already_kebab_case(self):
        self.assertEqual(to_kebab_case("kebab-case"), "kebab-case")
        self.assertEqual(to_kebab_case("HAtom"), "h-atom")
        self.assertEqual(to_kebab_case("test--case"), "test-case")
        self.assertEqual(to_kebab_case("---test---"), "test")


if __name__ == "__main__":
    unittest.main()
