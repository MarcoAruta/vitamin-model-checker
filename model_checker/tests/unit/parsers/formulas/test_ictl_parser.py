"""Unit tests for ICTL formula lexer and parser."""

import pytest

from model_checker.parsers.formula_parser_factory import FormulaParserFactory


@pytest.mark.unit
class TestIctlParser:
    def test_parses_classic_lowercase_atoms(self):
        parser = FormulaParserFactory.get_parser_instance("ICTL")
        assert parser.parse("EX e") == ("EX", "e")
        assert parser.parse("AG (p -> EF q)") == ("AG", ("->", "p", ("EF", "q")))

    def test_parses_mixed_case_atoms(self):
        parser = FormulaParserFactory.get_parser_instance("ICTL")
        assert parser.parse("AG Goal") == ("AG", "Goal")
        assert parser.parse("EF safe_1") == ("EF", "safe_1")

    def test_rejects_operator_like_atom_tokens(self):
        parser = FormulaParserFactory.get_parser_instance("ICTL")
        assert parser.parse("AG EX") is None

    def test_rejects_leading_digits_in_atoms(self):
        parser = FormulaParserFactory.get_parser_instance("ICTL")
        assert parser.parse("AG 1goal") is None
