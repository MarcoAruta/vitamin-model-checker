"""Formula tree solver for ICTL."""

from typing import TYPE_CHECKING, Any

from model_checker.algorithms.explicit.ICTL.operators import (
    handle_af,
    handle_ag,
    handle_and,
    handle_ar,
    handle_au,
    handle_ax,
    handle_ef,
    handle_eg,
    handle_er,
    handle_eu,
    handle_ex,
    handle_implies,
    handle_not,
    handle_or,
)
from model_checker.parsers.formula_parser_factory import FormulaParserFactory

if TYPE_CHECKING:
    from model_checker.algorithms.explicit.ICTL.checker import ICTLModelChecker
    from model_checker.utils.formula_tree import FormulaTreeNode


def _unary_handler(
    parser: Any, checker: "ICTLModelChecker", node: "FormulaTreeNode"
) -> Any | None:
    val = node.value
    if parser.verify("NOT", val):
        return handle_not
    if parser.verify("FORALL", val) and parser.verify("NEXT", val):
        return handle_ax
    if parser.verify("EXIST", val) and parser.verify("NEXT", val):
        return handle_ex
    if parser.verify("EXIST", val) and parser.verify("GLOBALLY", val):
        return handle_eg
    if parser.verify("FORALL", val) and parser.verify("GLOBALLY", val):
        return handle_ag
    if parser.verify("EXIST", val) and parser.verify("EVENTUALLY", val):
        return handle_ef
    if parser.verify("FORALL", val) and parser.verify("EVENTUALLY", val):
        return handle_af
    return None


def _binary_handler(
    parser: Any, checker: "ICTLModelChecker", node: "FormulaTreeNode"
) -> Any | None:
    val = node.value
    if parser.verify("OR", val):
        return handle_or
    if parser.verify("AND", val):
        return handle_and
    if parser.verify("IMPLIES", val):
        return handle_implies
    if parser.verify("EXIST", val) and parser.verify("UNTIL", val):
        return handle_eu
    if parser.verify("FORALL", val) and parser.verify("UNTIL", val):
        return handle_au
    if parser.verify("EXIST", val) and parser.verify("RELEASE", val):
        return handle_er
    if parser.verify("FORALL", val) and parser.verify("RELEASE", val):
        return handle_ar
    return None


def solve_tree(
    checker: "ICTLModelChecker",
    node: "FormulaTreeNode",
    parser: Any | None = None,
) -> None:
    """Evaluate the formula tree bottom-up."""
    if parser is None:
        parser = FormulaParserFactory.get_parser_instance("ICTL")

    if node.left is not None:
        solve_tree(checker, node.left, parser)
    if node.right is not None:
        solve_tree(checker, node.right, parser)

    if node.right is None:
        if node.left is None:
            return
        handler = _unary_handler(parser, checker, node)
        if handler is None:
            raise ValueError(f"Unsupported ICTL unary operator: {node.value!r}")
        handler(checker, node)
        return

    if node.left is not None and node.right is not None:
        handler = _binary_handler(parser, checker, node)
        if handler is None:
            raise ValueError(f"Unsupported ICTL binary operator: {node.value!r}")
        handler(checker, node)
