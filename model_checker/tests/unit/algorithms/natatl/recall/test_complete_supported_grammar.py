"""Sound negative exhaustion for the explicitly supported NatATL Recall grammar.

Run from the VITAMIN repository root:
    python test_recall_complete_supported_grammar.py

These are independent semantic examples, NOT a mechanized proof of the
structural completeness theorem (see NATATL_RECALL_COMPLETENESS.md).
"""
from itertools import product

from model_checker.algorithms.explicit.NatATL.Recall.recall_compositional import (
    check_compositional_recall_ast,
)
from model_checker.algorithms.explicit.NatATL.Recall.recall_full_regex_generation import (
    history_guards_full_exact_cost,
    regex_exact_raw_size,
)
from model_checker.algorithms.explicit.NatATL.Recall.recall_lazy_generation import (
    regex_complexity,
)
from model_checker.algorithms.explicit.NatATL.Recall.history_automaton import HistoryRegex
from model_checker.algorithms.explicit.NatATL.Recall.recall_solver import solve_bounded_recall


class TwoAgentAdversarialCGS:
    """The goal is reachable but an opponent can prevent it forever."""
    states = ["s0", "goal", "trap"]
    initial_state = "s0"
    atomic_propositions = ["goal"]
    matrix_prop = [[0], [1], [0]]
    graph = [
        ["IDLE|BLOCK,IDLE|ALLOW", "MOVE|ALLOW", "MOVE|BLOCK"],
        [0, "IDLE|BLOCK,IDLE|ALLOW,MOVE|BLOCK,MOVE|ALLOW", 0],
        [0, 0, "IDLE|BLOCK,IDLE|ALLOW,MOVE|BLOCK,MOVE|ALLOW"],
    ]
    def get_number_of_agents(self):
        return 2


class TwoAgentForcedGoalCGS:
    """Both opponent responses to IDLE lead to a goal after two steps."""
    states = ["s0", "left", "right", "goal", "trap"]
    initial_state = "s0"
    atomic_propositions = ["goal"]
    matrix_prop = [[0], [0], [0], [1], [0]]
    graph = [
        [0, "IDLE|BLOCK", "IDLE|ALLOW", 0, "MOVE|BLOCK,MOVE|ALLOW"],
        [0, 0, 0, "IDLE|BLOCK,IDLE|ALLOW", "MOVE|BLOCK,MOVE|ALLOW"],
        [0, 0, 0, "IDLE|BLOCK,IDLE|ALLOW", "MOVE|BLOCK,MOVE|ALLOW"],
        [0, 0, 0, "IDLE|BLOCK,IDLE|ALLOW,MOVE|BLOCK,MOVE|ALLOW", 0],
        [0, 0, 0, 0, "IDLE|BLOCK,IDLE|ALLOW,MOVE|BLOCK,MOVE|ALLOW"],
    ]
    def get_number_of_agents(self):
        return 2



def test_complete_supported_recall_grammar():
    adversarial = TwoAgentAdversarialCGS()
    negative = solve_bounded_recall(
        adversarial, [1], 3, "F", {"goal"}, generator="extended",
        certify_restricted_exhaustion=True,
    )
    assert negative["Satisfiability"] is False, negative
    assert negative["Negative Certificate"] == "EXHAUSTIVE_BOUNDED_RECALL_ENUMERATION"
    assert negative["Candidates Examined"] > 1, negative
    print("PASS: k>minimum, reachable-but-unforceable goal gives exhaustive False")

    # Same bounded solver WITHOUT supported-grammar completeness is conservative.
    old = solve_bounded_recall(
        adversarial, [1], 3, "F", {"goal"}, generator="extended"
    )
    assert old["Satisfiability"] is None, old
    print("PASS: existing conservative direct solver interface is unchanged")

    nested = ("!", ("<{1},3>F", "goal"))
    response = check_compositional_recall_ast(
        adversarial, nested, generator="extended", complete_supported_grammar=True
    )
    assert response["Satisfiability"] is True, response
    assert response["Supported Grammar Complete"] is True, response
    print("PASS: exhaustive negative can safely be negated in a nested formula")

    for modal in (
        ("<{1},3>X", "goal"),
        ("<{1},3>G", "goal"),
        ("<{1},3>F", "goal"),
        ("<{1},3>U", "true", "goal"),
        ("<{1},3>W", "goal", "goal"),
    ):
        decided = check_compositional_recall_ast(
            adversarial, modal, generator="extended",
            complete_supported_grammar=True,
        )
        assert decided["Satisfiability"] is False, (modal, decided)
    weak_true = check_compositional_recall_ast(
        adversarial, ("<{1},3>W", "true", "goal"),
        generator="extended", complete_supported_grammar=True
    )
    assert weak_true["Satisfiability"] is True, weak_true
    print("PASS: exhaustive X/G/F/U/W agree with universal temporal semantics")

    forced = TwoAgentForcedGoalCGS()
    win = check_compositional_recall_ast(
        forced, ("<{1},1>F", "goal"), generator="extended",
        complete_supported_grammar=True,
    )
    assert win["Satisfiability"] is True, win
    loss = check_compositional_recall_ast(
        forced, ("<{1},1>X", "goal"), generator="extended",
        complete_supported_grammar=True,
    )
    assert loss["Satisfiability"] is False, loss
    print("PASS: bound is strategy COST, not path depth")

    # Nested strategic subformula results are exact state sets in complete mode.
    inner = ("<{1},3>F", "goal")
    outer = ("<{1},1>G", ("!", inner))
    exact = check_compositional_recall_ast(
        adversarial, outer, generator="extended", complete_supported_grammar=True
    )
    assert exact["Satisfiability"] in (True, False)
    assert all(v != "INCONCLUSIVE" for v in exact["State Verdicts"].values()), exact
    print("PASS: nested modalities have no unknown states in supported-complete mode")

    try:
        check_compositional_recall_ast(
            adversarial, inner, generator="canonical", complete_supported_grammar=True
        )
    except ValueError as exc:
        assert "generator='extended'" in str(exc), exc
    else:
        raise AssertionError("Incorrectly certified canonical generation")
    print("PASS: incomplete canonical generator cannot claim completeness")

    # Cross-check finite bounded normal-form coverage (an independent test, not
    # the induction proof): for each raw AST up to size 4, an enumerated guard
    # has no higher cost and agrees on all words of length <= 3.
    labels = (frozenset(), frozenset({"p"}))
    words = [w for length in range(4) for w in product(labels, repeat=length)]
    all_guards = [g for k in range(1, 5)
                  for g in history_guards_full_exact_cost(k, ["p"])]
    semantic_representatives = {}
    for guard in all_guards:
        machine = HistoryRegex(guard, ["p"])
        sig = tuple(machine.matches(word) for word in words)
        semantic_representatives.setdefault(sig, regex_complexity(guard))
    for raw_cost in range(1, 5):
        for raw in regex_exact_raw_size(raw_cost, ["p"]):
            actual_cost = regex_complexity(raw)
            sig = tuple(HistoryRegex(raw, ["p"]).matches(word) for word in words)
            assert sig in semantic_representatives, (raw, actual_cost)
            assert semantic_representatives[sig] <= actual_cost, (raw, actual_cost)
    print("PASS: raw regular ASTs up to size 4 covered at nonincreasing cost")
    print("ALL SUPPORTED RECALL COMPLETENESS REGRESSIONS PASSED!")


if __name__ == "__main__":
    test_complete_supported_recall_grammar()
