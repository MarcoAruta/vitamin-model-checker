"""TOL model checking."""

from typing import Any

from model_checker.algorithms.explicit.shared.result_formatters import (
    format_model_checking_result,
    verify_initial_state,
)
from model_checker.algorithms.explicit.TOL.solver import solve_tree
from model_checker.engine.execution import create_model_checking_entry
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.parsers.game_structures.timed_cgs.formula_clocks import (
    collect_formula_clocks,
    extend_timed_cgs_clocks,
    max_constants_from_formula,
)
from model_checker.parsers.game_structures.timed_cgs.zone_graph import ZoneGraph
from model_checker.utils.error_handler import create_error_response


def _core_tol_checking(tcgs, formula: str) -> dict[str, Any]:
    parser = FormulaParserFactory.get_parser_instance("TOL")
    ast = parser.parse(formula.strip())
    if ast is None:
        err = parser.errors[0] if parser.errors else "Syntax Error"
        return create_error_response("syntax", err)

    formula_clocks = collect_formula_clocks(ast, set(tcgs.clocks))
    extend_timed_cgs_clocks(tcgs, formula_clocks)

    formula_max = max_constants_from_formula(ast, tcgs.clocks_dict)
    zone_graph = ZoneGraph(tcgs, extra_max_constants=formula_max)
    solve_tree(tcgs, zone_graph, ast)

    init_state = str(tcgs.initial_state)
    is_satisfied = verify_initial_state(init_state, ast.satisfying_states)
    return format_model_checking_result(ast.satisfying_states, init_state, is_satisfied)


model_checking = create_model_checking_entry("TOL", _core_tol_checking)
