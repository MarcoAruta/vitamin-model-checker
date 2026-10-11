"""
Matrix-based pruning for NatATL Memoryless verification.

Applies condition-action strategies to restrict the CGS transition matrix,
then runs CTL model checking on the pruned model. A memoryless strategy
restricts transitions based on the current state, so the matrix can be
pruned directly without tree expansion.
"""

import copy
import logging
from typing import Any
import ast

from model_checker.algorithms.explicit.CTL.CTL import model_checking
from model_checker.algorithms.explicit.NatATL.Memoryless.matrix_utils import (
    modify_matrix,
)
from model_checker.parsers.game_structures.cgs import CGS
from model_checker.utils.literals import parse_state_set_literal

logger = logging.getLogger(__name__)



def process_transition_matrix_data_fixed(
    cgs: CGS,
    model_path: str,
    agents: list[int],
    *strategies: dict[str, Any],
) -> list[list]:
    """Apply explicit natural memoryless strategies to a CGS."""

    if len(strategies) != len(agents):
        raise ValueError(
            "One individual strategy is required per coalition agent"
        )

    graph = [row[:] for row in cgs.graph]
    state_to_index = cgs.state_to_index
    all_states = {str(s) for s in cgs.states}

    for strategy_index, strategy in enumerate(strategies, start=1):
        rules = strategy["condition_action_pairs"]

        # A natural strategy must explicitly end with (T, action).
        if not rules or rules[-1][0].strip() != "T":
            raise ValueError(
                f"Agent {agents[strategy_index - 1]}: "
                "missing explicit (T, action) fallback"
            )

        covered_states = set()

        for condition, action in rules:

            # T is logical truth, not an atomic proposition.
            if condition.strip() == "T":
                state_set = set(all_states)

            else:
                if not hasattr(cgs, "_condition_cache"):
                    cgs._condition_cache = {}

                cache_key = (condition, model_path)

                if cache_key not in cgs._condition_cache:
                    cgs._condition_cache[cache_key] = model_checking(
                        condition,
                        model_path,
                        preloaded_model=cgs,
                    )

                states_result = cgs._condition_cache[cache_key]
                res_str = states_result.get("res", "")

                if not res_str.startswith("Result: "):
                    raise ValueError(
                        f"Invalid condition {condition!r}: "
                        f"{states_result}"
                    )

                state_set = parse_state_set_literal(
                    res_str.split(": ", 1)[1]
                )

            # Ordered first-match semantics.
            applicable_states = state_set - covered_states

            if not applicable_states:
                continue

            graph = modify_matrix(
                graph,
                applicable_states,
                action,
                strategy_index,
                agents,
                num_agents=cgs.get_number_of_agents(),
                state_to_index=state_to_index,
                in_place=True,
            )

            # Reject choices that leave a state without successors.
            for state in applicable_states:
                row = graph[state_to_index[state]]

                if not any(
                    cell not in (0, "0", None)
                    for cell in row
                ):
                    raise ValueError(
                        f"Action {action!r} is not enabled "
                        f"for agent {agents[strategy_index - 1]} "
                        f"in state {state}"
                    )

            covered_states.update(applicable_states)

        # No implicit idle transitions are inserted.
        if covered_states != all_states:
            raise ValueError(
                "Incomplete strategy: states not covered "
                f"{all_states - covered_states}"
            )

    return graph


def pruning(
    cgs: CGS, model_path: str, agents: list[int], formula: str, current_agents: list
) -> bool:
    """Prune the model to a strategy profile and run CTL on the result.

    Returns True when the initial state satisfies the formula on the pruned model.
    """
    # Isolate pruned model from the shared CGS used across strategy candidates.
    cgs1 = copy.deepcopy(cgs)
    cgs1.graph = process_transition_matrix_data_fixed(
        cgs, model_path, agents, *current_agents
    )

    # Use in-memory CTL model checking
    result = model_checking(formula, model_path, preloaded_model=cgs1)


    # Reject backend errors instead of interpreting them as False.
    if not isinstance(result, dict) or result.get("error"):
        raise ValueError(f"CTL verification failed: {result}")

    res = result.get("res")

    if not isinstance(res, str) or not res.startswith("Result: "):
        raise ValueError(f"Malformed CTL result: {result}")

    # Extract the satisfying states returned by CTL.
    serialized_states = res[len("Result: "):].strip()

    if serialized_states in ("set()", "{}", "()"):
        satisfying_states = set()
    else:
        try:
            parsed = ast.literal_eval(serialized_states)
        except (ValueError, SyntaxError) as exc:
            raise ValueError(
                f"Invalid CTL state set: {res}"
            ) from exc

        if not isinstance(parsed, (set, tuple, list)):
            raise ValueError(f"Invalid CTL state set: {res}")

        satisfying_states = {
            str(state) for state in parsed
        }

    # Truth must hold at the actual initial state.
    initial = str(cgs1.initial_state)
    satisfied = initial in satisfying_states

    expected = f"Initial state {initial}: {satisfied}"

    if result.get("initial_state") != expected:
        raise ValueError(
            "Inconsistent CTL initial-state result: "
            f"expected {expected!r}, "
            f"got {result.get('initial_state')!r}"
        )

    if (
        "satisfied" in result
        and result["satisfied"] is not satisfied
    ):
        raise ValueError("Inconsistent CTL satisfaction flag")

    return satisfied
