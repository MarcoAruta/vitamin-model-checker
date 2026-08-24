"""Central syntax pattern definitions."""

import re

import pytest

from model_checker.parsers.syntax_patterns import (
    COMPARISON_OPERATORS,
    NATATL_CAPACITY_RE,
    OATL_COALITION_DEMONIC_TOKEN,
    PROPOSITION_FULL_RE,
    WALLET_CONSTRAINT_RE,
)


@pytest.mark.unit
def test_proposition_pattern_accepts_mixed_case():
    assert PROPOSITION_FULL_RE.match("Goal")
    assert PROPOSITION_FULL_RE.match("safe_1")
    assert not PROPOSITION_FULL_RE.match("1goal")


@pytest.mark.unit
def test_natatl_capacity_pattern_matches_canonical_form():
    match = NATATL_CAPACITY_RE.match("<{1,2}, 5>")
    assert match
    assert match.group(1) == "1,2"
    assert match.group(2) == "5"


@pytest.mark.unit
def test_comparison_operators_are_longest_first():
    assert COMPARISON_OPERATORS[0] == ">="
    assert COMPARISON_OPERATORS[1] == "<="
    assert "==" in COMPARISON_OPERATORS


@pytest.mark.unit
def test_wallet_constraint_pattern_matches_ops():
    match = WALLET_CONSTRAINT_RE.fullmatch("wallet(1, >= 5)")
    assert match
    assert match.group("agent") == "1"
    assert match.group("operator") == ">="
    assert match.group("value") == "5"


@pytest.mark.unit
def test_oatl_demonic_token_rejects_zero_bound():
    assert re.fullmatch(OATL_COALITION_DEMONIC_TOKEN, "<1><5>")
    assert not re.fullmatch(OATL_COALITION_DEMONIC_TOKEN, "<1><0>")
