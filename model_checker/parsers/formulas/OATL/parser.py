"""OATL parser (PLY-based).

Supported:
- OATL formulas with coalition and demonic bounds (`<1,2><5>F p`, `<1><3>G p`).
- Boolean connectives (&&, ||, !, ->) and temporal ops (U, G, X, F).

Rejects:
- Release (R) and Weak Until (W); use COTL when those operators are required.
- Missing demonic bounds after a coalition (e.g., `<1>F p`).
- Malformed coalitions or invalid agent indices relative to n_agent.
- Non-ASCII, null bytes, or disallowed special characters in propositions.

Returns:
- AST tuple on success, or None on invalid input.
"""

import re

from model_checker.parsers.syntax_patterns import (
    AGENT_LIST,
    OATL_COALITION_DEMONIC_TOKEN,
    POSITIVE_INT,
)

from ..parser_utils import (
    BOOLEAN_AST_OPERATORS,
    PROPOSITION_TOKEN_PATTERN,
    run_common_prechecks,
    validate_ast,
    validate_coalition_bound_token,
    validate_release_weak_rejected,
)
from ..shared_parser import BaseLogicParser

_OATL_MODAL_OPS = r"F|G|X|U|UNTIL|NEXT|EVENTUALLY|GLOBALLY"
_OATL_COALITION_OPERATOR_PATTERN = re.compile(
    rf"^{OATL_COALITION_DEMONIC_TOKEN}({_OATL_MODAL_OPS})$",
    re.IGNORECASE,
)
_OATL_VALID_OPERATORS = (
    frozenset(
        {
            "U",
            "X",
            "F",
            "G",
            "UNTIL",
            "NEXT",
            "EVENTUALLY",
            "GLOBALLY",
        }
    )
    | BOOLEAN_AST_OPERATORS
)
_MISSING_BOUND_TEMPORAL_RE = re.compile(rf"<{AGENT_LIST}>\s*[FGXURW]")
_COALITION_BOUND_PROBE_RE = re.compile(
    rf"<{AGENT_LIST}><(?P<bound>\d+)>\s*(?P<op>[FGXURW])"
)
_OATL_BOUND_PRESENT_RE = re.compile(OATL_COALITION_DEMONIC_TOKEN)


class OATLParser(BaseLogicParser):
    """Parser for OATL formulas (coalition and demonic bounds, temporal ops).

    Use parse(formula) to get an AST tuple or None on invalid input.
    Set n_agent before parsing for coalition validation.
    """

    def __init__(self):
        """Initialize the OATL lexer and parser (PLY)."""
        super().__init__()
        self.tokens.extend(
            [
                "COALITION_DEMONIC",
                "PROP",
                "UNTIL",
                "GLOBALLY",
                "NEXT",
                "EVENTUALLY",
            ]
        )
        self.max_coalition = 0
        self.build()

    # === Tokens ===
    t_PROP = PROPOSITION_TOKEN_PATTERN
    t_COALITION_DEMONIC = OATL_COALITION_DEMONIC_TOKEN

    # === Grammar ===
    def p_expression_ternary(self, p):
        """expression : COALITION_DEMONIC expression UNTIL expression"""
        validate_coalition_bound_token(
            p[1], self.max_coalition, bound_pattern=POSITIVE_INT
        )
        p[0] = (p[1] + p[3], p[2], p[4])

    def p_expression_unary(self, p):
        """expression : COALITION_DEMONIC GLOBALLY expression
        | COALITION_DEMONIC NEXT expression
        | COALITION_DEMONIC EVENTUALLY expression"""
        validate_coalition_bound_token(
            p[1], self.max_coalition, bound_pattern=POSITIVE_INT
        )
        p[0] = (p[1] + p[2], p[3])

    # === Validation ===
    def parse(self, formula, n_agent=0, **kwargs):
        self.max_coalition = n_agent
        return super().parse(formula, **kwargs)

    def _coalition_bound_pre_validation(self, formula) -> tuple[bool, str | None]:
        coalition_temporal_match = _COALITION_BOUND_PROBE_RE.search(formula)
        if coalition_temporal_match:
            bound_raw = coalition_temporal_match.group("bound")
            if int(bound_raw) == 0:
                return (
                    False,
                    "Bound must be a positive integer (>=1) for temporal operators",
                )
            if len(bound_raw) > 1 and bound_raw.startswith("0"):
                return (
                    False,
                    "Bound cannot have leading zeros (e.g., use <1><5>, not <1><05>)",
                )

        if _MISSING_BOUND_TEMPORAL_RE.search(
            formula
        ) and not _OATL_BOUND_PRESENT_RE.search(formula):
            return (
                False,
                "Temporal operators require a bound in the form <coalition><k> with k>=1 (e.g., <1><5>F p)",
            )
        return True, None

    def _pre_validation(self, formula) -> tuple[bool, str | None]:
        valid, err = run_common_prechecks(
            formula,
            allow_hash_at=False,
            coalition_required=True,
            extra_invalid_regexes=(),
        )
        if not valid:
            return False, err

        valid, err = validate_release_weak_rejected(formula, "OATL")
        if not valid:
            return False, err

        return self._coalition_bound_pre_validation(formula)

    def _post_validation(self, formula, result):
        if result is None:
            return False
        return validate_ast(
            result,
            _OATL_VALID_OPERATORS,
            coalition_pattern=_OATL_COALITION_OPERATOR_PATTERN,
        )
