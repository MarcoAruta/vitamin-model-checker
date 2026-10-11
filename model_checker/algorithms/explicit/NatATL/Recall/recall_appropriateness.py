"""Global appropriateness checks for NatATL recall guarded-action rules.

A pair (r, action) is appropriate only if 'action' is enabled at the last
state of EVERY finite CGS history matching regex r (Section 6.1 of
Jamroga--Malvone--Murano, Natural Strategic Ability).

This validator explores a finite CGS x regex-monitor product from *every*
CGS state, without applying the strategy being validated. Consequently it
also checks histories that a particular proposed strategy cannot reach.
No finite unfolding bound is used.

A checked strategy must end in the explicit (T*, IDLE) fallback.
"""

from collections import deque
from collections.abc import Sequence
from typing import Any

from model_checker.algorithms.explicit.NatATL.Recall.history_automaton import (
    HistoryRegex,
)
from model_checker.parsers.game_structures.cgs.cgs_actions import (
    normalize_action_token,
    parse_joint_action_cell,
)


class InappropriateRecallRule(ValueError):
    """An action is unavailable after a history recognized by its guard."""


def _read_cgs(cgs: Any):
    names = tuple(str(s) for s in cgs.states)
    propositions = tuple(str(p) for p in cgs.atomic_propositions)
    n_agents = cgs.get_number_of_agents()

    if not names or len(set(names)) != len(names) or n_agents < 1:
        raise ValueError("Invalid CGS states or number of agents")
    if len(cgs.graph) != len(names) or any(
        len(row) != len(names) for row in cgs.graph
    ):
        raise ValueError("Invalid CGS transition matrix dimensions")
    if len(cgs.matrix_prop) != len(names) or any(
        len(row) != len(propositions) for row in cgs.matrix_prop
    ):
        raise ValueError("Invalid CGS proposition matrix dimensions")

    labels = {
        name: frozenset(
            propositions[j]
            for j, flag in enumerate(cgs.matrix_prop[i])
            if int(flag) == 1
        )
        for i, name in enumerate(names)
    }
    successor_states = {}
    enabled = {}
    for i, state in enumerate(names):
        targets = set()
        enabled_here = {agent: set() for agent in range(1, n_agents + 1)}
        for j, cell in enumerate(cgs.graph[i]):
            if cell in (0, "0", "", None):
                continue
            if not isinstance(cell, str):
                raise ValueError(f"Malformed transition cell at {state}")
            if "*" in cell:
                raise ValueError("Wildcard joint actions are not supported")
            for joint in parse_joint_action_cell(cell, n_agents):
                targets.add(names[j])
                for agent in range(1, n_agents + 1):
                    enabled_here[agent].add(joint[agent - 1])
        if not targets:
            raise ValueError(f"Non-total CGS: no transition from {state}")
        successor_states[state] = frozenset(targets)
        enabled[state] = enabled_here

    return names, propositions, n_agents, labels, successor_states, enabled


def _check_rule(
    *,
    states: tuple[str, ...],
    propositions: tuple[str, ...],
    labels: dict,
    successors: dict,
    enabled: dict,
    agent: int,
    pattern: str,
    action: str,
) -> None:
    monitor = HistoryRegex(pattern, propositions)

    # All legal histories may start at any model state. The current state's
    # labelling is consumed immediately, just as in build_recall_product().
    pending = deque()
    seen = set()
    for state in states:
        memory = monitor.step(monitor.initial, labels[state])
        key = (state, memory)
        if key not in seen:
            seen.add(key)
            pending.append((state, memory, (state,)))

    while pending:
        state, memory, history = pending.popleft()
        if monitor.is_accepting(memory) and action not in enabled[state][agent]:
            raise InappropriateRecallRule(
                f"Inappropriate recall rule for agent {agent}: "
                f"({pattern!r}, {action!r}) matches history {history!r}, "
                f"but {action!r} is not enabled in state {state!r}"
            )
        for target in successors[state]:
            new_memory = monitor.step(memory, labels[target])
            key = (target, new_memory)
            if key not in seen:
                seen.add(key)
                pending.append((target, new_memory, history + (target,)))


def validate_recall_profile(
    cgs: Any,
    agents: Sequence[int],
    strategies: Sequence[dict],
) -> None:
    """Raise ValueError if any recall rule is globally inappropriate.

    Important: this checks all matching histories of the unpruned CGS,
    not merely those reachable under the supplied profile.
    """
    states, props, count, labels, successors, enabled = _read_cgs(cgs)
    if len(agents) != len(strategies) or not agents:
        raise ValueError("Expected one strategy for each coalition member")
    if len(set(agents)) != len(agents) or any(
        not isinstance(a, int) or a < 1 or a > count for a in agents
    ):
        raise ValueError("Invalid or repeated coalition agent")

    for agent, strategy in zip(agents, strategies):
        if not isinstance(strategy, dict):
            raise ValueError("Malformed recall strategy")
        rules = strategy.get("condition_action_pairs")
        if not isinstance(rules, (list, tuple)) or not rules:
            raise ValueError("Empty recall rule list")
        for item in rules:
            if not isinstance(item, (list, tuple)) or len(item) != 2:
                raise ValueError("Malformed recall guarded-action pair")
        if rules[-1][0].strip() != "T*" or (
            normalize_action_token(rules[-1][1]) != "IDLE"
        ):
            raise ValueError("Recall requires final (T*, IDLE) fallback")

        for pattern, action in rules:
            _check_rule(
                states=states,
                propositions=props,
                labels=labels,
                successors=successors,
                enabled=enabled,
                agent=agent,
                pattern=pattern,
                action=normalize_action_token(action),
            )
