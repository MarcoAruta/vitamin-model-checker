"""TCTL and TOL parsers accept mixed-case atomic propositions."""

import pytest

from model_checker.parsers.formula_parser_factory import FormulaParserFactory


@pytest.mark.unit
def test_tctl_parser_freeze_expression():
    parser = FormulaParserFactory.get_parser_instance("TCTL")
    ast = parser.parse("j.p")
    assert ast is not None
    from model_checker.parsers.formulas.TCTL import FreezeExpr

    assert isinstance(ast, FreezeExpr)
    assert ast.clock == "j"


@pytest.mark.unit
def test_tctl_parser_parenthesized_until():
    from model_checker.parsers.formulas.TCTL import (
        Binary,
        QuantifiedPath,
    )

    parser = FormulaParserFactory.get_parser_instance("TCTL")
    flat = parser.parse("E p U q")
    grouped = parser.parse("E (p U q)")
    assert flat is not None
    assert grouped is not None
    assert isinstance(flat, QuantifiedPath)
    assert isinstance(grouped, QuantifiedPath)
    assert flat.quantifier == grouped.quantifier == "E"
    assert isinstance(flat.formula, Binary)
    assert repr(flat.formula) == repr(grouped.formula)


@pytest.mark.unit
@pytest.mark.parametrize(
    "formula",
    [
        "E (p U q)",
        "A (Goal U safe_1)",
    ],
)
def test_tctl_parser_accepts_parenthesized_until(formula):
    parser = FormulaParserFactory.get_parser_instance("TCTL")
    assert parser.parse(formula) is not None


@pytest.mark.unit
@pytest.mark.parametrize(
    "formula",
    [
        "Goal",
        "EF Goal",
        "AG Goal",
        "Goal && safe_1",
        "x<=1",
    ],
)
def test_tctl_parser_accepts_mixed_case_propositions(formula):
    parser = FormulaParserFactory.get_parser_instance("TCTL")
    assert parser.parse(formula) is not None


@pytest.mark.unit
@pytest.mark.parametrize(
    "formula",
    [
        "Goal",
        "{J1}F Goal",
        "{J1}G Goal",
        "Goal && safe_1",
        "x<=1",
        "j.Goal",
    ],
)
def test_tol_parser_accepts_mixed_case_propositions(formula):
    parser = FormulaParserFactory.get_parser_instance("TOL")
    assert parser.parse(formula) is not None


@pytest.mark.unit
def test_tol_parser_freeze_expression():
    parser = FormulaParserFactory.get_parser_instance("TOL")
    ast = parser.parse("j.Goal")
    assert ast is not None
    from model_checker.parsers.formulas.TOL import FreezeExpr

    assert isinstance(ast, FreezeExpr)
    assert ast.clock == "j"


@pytest.mark.unit
@pytest.mark.parametrize(
    "formula",
    ["x>5", "x>=5", "x<5", "x<=5", "true", "false"],
)
def test_tctl_parser_clock_comparisons_and_booleans(formula):
    parser = FormulaParserFactory.get_parser_instance("TCTL")
    assert parser.parse(formula) is not None


@pytest.mark.unit
@pytest.mark.parametrize(
    "formula",
    ["x>5", "x>=5", "true", "false", "#", "@"],
)
def test_tol_parser_clock_comparisons_and_booleans(formula):
    parser = FormulaParserFactory.get_parser_instance("TOL")
    assert parser.parse(formula) is not None


@pytest.mark.unit
@pytest.mark.parametrize(
    ("wordy", "compact"),
    [
        ("forall G p", "AG p"),
        ("exist F p", "EF p"),
    ],
)
def test_tctl_parser_forall_exist_keywords(wordy, compact):
    parser = FormulaParserFactory.get_parser_instance("TCTL")
    wordy_ast = parser.parse(wordy)
    compact_ast = parser.parse(compact)
    assert wordy_ast is not None
    assert compact_ast is not None
    assert repr(wordy_ast) == repr(compact_ast)
