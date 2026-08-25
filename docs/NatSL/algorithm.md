# NatSL - Algorithm Reference

Scope: denotations and code path for NatSL in
`model_checker/algorithms/explicit/NatSL/`.

## Model

- Type: `CGS`
- Formulas reduce to NatATL-style goals for checking.

## Formula language

Parser: `parsers/formulas/NatSL/parser.py`

```text
E{k}x : (x, a) F p
Ax Ay : (x, 1)(y, 2) F win
E{k}x : (x, a) !F p
```

Current temporal fragment after bindings: `F p` or `!F p` only.

## Semantic denotations

Two execution modes:

| Mode | Path | Meaning |
|---|---|---|
| Sequential | `NatSL/Sequential/` | Existential strategies first, then universal checks |
| Alternated | `NatSL/Alternated/` | Alternate existential / universal exploration |

`!F` reduction maps to a negated NatATL eventually form (see knowledge base
note on possible divergence from an explicit avoid formula).

Implementation techniques (recall pruning / condition cache via NatATL): [algorithm_design.md](../algorithm_design.md).

## Theory vs implementation

| Aspect | Theory | Implementation |
|---|---|---|
| Temporal fragment | Often richer | Only `F` / `!F` |
| Reduction | RED(SL) -> NatATL | Automatic |
| Semantics modes | Sequential / alternated | Separate packages |

## Model-checking pipeline

```text
CGS.read_file -> NatSLParser.parse -> reduce to NatATL-shaped goal
  -> Sequential or Alternated checker -> result
```

## Code map

| Path | Role |
|---|---|
| `NatSL/Sequential/` | Sequential semantics |
| `NatSL/Alternated/` | Alternated semantics |
| `NatSL/shared_recall.py` | Shared helpers |

## Tests

NatSL parser and algorithm tests under `model_checker/tests/`.
