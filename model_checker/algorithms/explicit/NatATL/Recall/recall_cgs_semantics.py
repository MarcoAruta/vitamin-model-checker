"""Preflight validation of deterministic, total concurrent-game transitions.

The formal CGS transition function maps every combination of the agents'
locally enabled actions to *exactly one* successor at each state. The VITAMIN
transition matrix can otherwise encode a nondeterministic or partially defined
relation, which must not silently be treated as a standard NatATL CGS.

This checker is intentionally independent of strategy search. It does NOT
modify the input CGS, expand wildcards, or infer missing transitions.
"""

from __future__ import annotations

from itertools import product
from math import prod
from typing import Any

from model_checker.parsers.game_structures.cgs.cgs_actions import (
    parse_joint_action_cell,
)


def validate_recall_cgs_semantics(cgs: Any) -> dict[str, dict[tuple[str, ...], str]]:
    """Validate total deterministic t(q, a1, ..., an) over local action sets.

    Returns a read-only-by-convention snapshot of each state's joint-action
    transition function, without changing the original model.

    ValueError is raised for a malformed, nondeterministic, non-rectangular,
    or partially defined transition relation. Wildcard cells are unsupported
    by the current Recall pipeline and therefore rejected explicitly.
    """
    states = tuple(str(state) for state in cgs.states)
    n_agents = cgs.get_number_of_agents()
    if not states or len(set(states)) != len(states):
        raise ValueError("CGS must contain unique, nonempty states")
    if type(n_agents) is not int or n_agents < 1:
        raise ValueError("Invalid number of CGS agents")
    if len(cgs.graph) != len(states) or any(
        len(row) != len(states) for row in cgs.graph
    ):
        raise ValueError("Invalid CGS transition-matrix dimensions")

    transitions: dict[str, dict[tuple[str, ...], str]] = {}
    for row_index, state in enumerate(states):
        successors: dict[tuple[str, ...], str] = {}
        for col_index, raw_cell in enumerate(cgs.graph[row_index]):
            if raw_cell in (0, "0", "", None):
                continue
            if not isinstance(raw_cell, str):
                raise ValueError(f"Malformed CGS transition cell at {state!r}")
            if "*" in raw_cell:
                raise ValueError(
                    f"Wildcard joint actions unsupported by Recall at {state!r}"
                )
            # VITAMIN's generic parser may silently TRUNCATE surplus action
            # components. Strict NatATL checking must reject them instead.
            for raw_joint in raw_cell.split(","):
                raw_joint = raw_joint.strip()
                if not raw_joint:
                    raise ValueError(f"Empty joint-action entry at {state!r}")
                if "|" in raw_joint:
                    raw_components = raw_joint.split("|")
                    if len(raw_components) != n_agents:
                        raise ValueError(
                            f"Invalid joint-action arity at {state!r}: "
                            f"{raw_joint!r} has {len(raw_components)} components, "
                            f"expected {n_agents}"
                        )
                elif n_agents > 1 and len(raw_joint) != n_agents:
                    raise ValueError(
                        f"Invalid compact joint-action arity at {state!r}: "
                        f"{raw_joint!r} has {len(raw_joint)} characters, "
                        f"expected {n_agents}"
                    )

            destination = states[col_index]
            for joint in parse_joint_action_cell(
                raw_cell, n_agents, strict_arity=True
            ):
                profile = tuple(joint)
                if len(profile) != n_agents or any(not action for action in profile):
                    raise ValueError(f"Invalid joint action {profile!r} at {state!r}")
                old_target = successors.get(profile)
                if old_target is not None and old_target != destination:
                    raise ValueError(
                        f"Nondeterministic CGS at {state!r}: joint action "
                        f"{profile!r} leads to both {old_target!r} "
                        f"and {destination!r}"
                    )
                successors[profile] = destination

        if not successors:
            raise ValueError(f"Non-total CGS: no actions at state {state!r}")

        choices = tuple(
            frozenset(profile[i] for profile in successors)
            for i in range(n_agents)
        )
        required = prod(len(actions) for actions in choices)
        if len(successors) != required:
            missing = next(
                profile for profile in product(*(sorted(actions) for actions in choices))
                if profile not in successors
            )
            raise ValueError(
                f"Incomplete joint-action table at {state!r}: "
                f"{missing!r} is a legal combination of individually "
                f"available actions but has no successor"
            )
        transitions[state] = successors

    return transitions
