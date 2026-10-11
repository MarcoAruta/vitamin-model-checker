
"""Compositional NatATL memoryless backend with state-set semantics."""

from collections.abc import Callable

from model_checker.algorithms.explicit.NatATL.strategy_complexity import (
    individual_complexity,
)

from model_checker.algorithms.explicit.NatATL.Memoryless.lazy_generation import (
    collective_strategies,
)
from model_checker.algorithms.explicit.NatATL.Memoryless.pruning import (
    process_transition_matrix_data_fixed,
)
from model_checker.parsers.game_structures.cgs.cgs_actions import (
    parse_joint_action_cell,
)


def universal_temporal_states(
    successors: dict[str, set[str]],
    op: str,
    left: set[str],
    right: set[str] | None = None,
) -> set[str]:
    """Evaluate universal temporal operators over a finite total graph."""

    states = set(successors)

    if not states or any(
        not targets or not targets <= states
        for targets in successors.values()
    ):
        raise ValueError(
            "Temporal evaluation requires a total transition relation"
        )

    if not left <= states or (
        right is not None and not right <= states
    ):
        raise ValueError("Temporal operand references unknown states")

    def ax(target: set[str]) -> set[str]:
        return {
            state
            for state, targets in successors.items()
            if targets <= target
        }

    if op == "X":
        if right is not None:
            raise ValueError("X expects one operand")
        return ax(left)

    if op not in {"F", "G", "U", "W"}:
        raise ValueError(f"Unsupported temporal operator: {op}")

    if (op in {"U", "W"}) != (right is not None):
        raise ValueError(f"Incorrect operands for {op}")

    if op == "F":
        target, invariant, least = left, states, True
    elif op == "G":
        target, invariant, least = set(), left, False
    else:
        target, invariant, least = right, left, op == "U"

    # F and U use least fixpoints.
    # G and W use greatest fixpoints.
    current = set() if least else set(states)

    while True:
        updated = target | (invariant & ax(current))

        if updated == current:
            return updated

        current = updated


def make_modal_backend(cgs, model_path: str) -> Callable:
    """Construct the strategic state-set evaluator for a loaded CGS."""

    names = [str(state) for state in cgs.states]
    states = set(names)
    n_agents = cgs.get_number_of_agents()

    if len(cgs.graph) != len(names) or any(
        len(row) != len(names) for row in cgs.graph
    ):
        raise ValueError("Invalid CGS transition matrix dimensions")

    if any(
        isinstance(cell, str) and "*" in cell
        for row in cgs.graph
        for cell in row
    ):
        raise ValueError(
            "NatATL strict pruning does not support wildcard actions"
        )

    if any(
        not any(cell not in (0, "0", None, "") for cell in row)
        for row in cgs.graph
    ):
        raise ValueError("The original CGS must be total")

    def available_actions(
        coalition: list[int],
    ) -> dict[int, list[str]]:
        """Read joint actions using the full number of CGS agents."""

        result = {agent: set() for agent in coalition}

        for row in cgs.graph:
            for cell in row:
                if not isinstance(cell, str):
                    continue

                for joint in parse_joint_action_cell(cell, n_agents):
                    for agent in coalition:
                        result[agent].add(joint[agent - 1])

        return {
            agent: sorted(actions)
            for agent, actions in result.items()
        }

    def backend(
        agents: tuple[int, ...],
        k: int,
        op: str,
        left: set[str],
        right: set[str] | None,
    ) -> set[str]:

        if (
            k < 0
            or len(set(agents)) != len(agents)
            or any(a < 1 or a > n_agents for a in agents)
        ):
            raise ValueError("Invalid coalition or complexity bound")

        coalition = list(agents)
        actions_by_agent = available_actions(coalition)

        winners: set[str] = set()
        backend.witnesses = {}

        for candidate in collective_strategies(
            agents=coalition,
            actions_by_agent=actions_by_agent,
            propositions=[str(p) for p in cgs.atomic_propositions],
            bound=k,
        ):
            try:
                graph = process_transition_matrix_data_fixed(
                    cgs,
                    model_path,
                    coalition,
                    *candidate,
                )

            except ValueError as exc:
                if "not enabled" in str(exc).lower():
                    continue
                raise

            successors = {
                state: {
                    names[j]
                    for j, cell in enumerate(graph[i])
                    if cell not in (0, "0", None, "")
                }
                for i, state in enumerate(names)
            }

            # A candidate that introduces a deadlock is inadmissible.
            if any(not targets for targets in successors.values()):
                continue

            winning_states = universal_temporal_states(
                successors,
                op,
                left,
                right,
            )

            # Record the first winning profile for each state.
            # Enumeration is ordered by collective complexity.
            for state in winning_states - winners:
                backend.witnesses[state] = candidate

            winners.update(winning_states)

            # No need to examine more profiles if all states win.
            if winners == states:
                break

        return winners

    backend.witnesses = {}
    return backend



def check_memoryless_formula(
    formula: str,
    model_path: str,
) -> dict:
    """Compositional NatATL memoryless verification."""

    from model_checker.algorithms.explicit.NatATL.compositional import (
        MODAL,
        satisfying_states,
    )
    from model_checker.algorithms.explicit.NatATL.natatl_ast import (
        parse_natatl_formula,
    )
    from model_checker.algorithms.explicit.shared.atom_utils import (
        states_where_prop_holds,
    )
    from model_checker.parsers.game_structures.cgs import CGS

    cgs = CGS()
    cgs.read_file(model_path)

    ast = parse_natatl_formula(
        formula,
        cgs.get_number_of_agents(),
    )

    universe = {str(state) for state in cgs.states}

    valuation = {
        str(prop): states_where_prop_holds(cgs, str(prop))
        for prop in cgs.atomic_propositions
    }

    modal_backend = make_modal_backend(cgs, model_path)

    result_states = satisfying_states(
        ast,
        universe,
        valuation,
        modal_backend,
    )

    initial = str(cgs.initial_state)
    satisfied = initial in result_states

    result = {
        "Satisfiability": satisfied,
        "Satisfying States": sorted(result_states),
        "res": f"Result: {tuple(sorted(result_states))}",
        "initial_state": (
            f"Initial state {initial}: {satisfied}"
        ),
    }

    # A top-level strategic modality has a witness
    # for its existential strategy quantifier.
    if (
        isinstance(ast, tuple)
        and ast
        and isinstance(ast[0], str)
        and (match := MODAL.fullmatch(ast[0]))
    ):
        bound = int(match.group("bound"))

        result["Complexity Bound"] = bound
        result["Requested Complexity Bound"] = bound

        if satisfied:
            witness = modal_backend.witnesses.get(initial)

            if witness is None:
                raise AssertionError(
                    "Missing witness for satisfied modality"
                )

            cost = sum(
                individual_complexity(
                    strategy["condition_action_pairs"]
                )
                for strategy in witness
            )

            if cost > bound:
                raise AssertionError(
                    "Witness exceeds complexity bound"
                )

            result["Winning Strategy per agent"] = witness
            result["Witness Complexity"] = cost
            result["Complexity Bound"] = cost

    return result
