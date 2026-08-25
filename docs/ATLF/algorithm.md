# ATLF - Algorithm Reference

Scope: denotations and code path for ATLF in
`model_checker/algorithms/explicit/ATLF/`.

## Model

- Type: `CGS`
- Same game structure as ATL; evaluation uses the ATLF fixed-point engine.

## Formula language

Parser: `parsers/formulas/ATLF/parser.py`

```text
phi ::= p | !phi | phi && psi | phi || psi | phi -> psi
      | <A> X phi | <A> F phi | <A> G phi | <A>(phi U psi)
```

Coalition form matches ATL: `<1>`, `<1,2>`.

## Semantic denotations

Coalition modalities evaluated with ATLF fixed-point / real-valued helpers under
`ATLF/` (see `operators.py`, `preimage.py`, `real_value_utils.py`).

Implementation techniques (per-operator transition cache): [algorithm_design.md](../algorithm_design.md).

## Theory vs implementation

| Aspect | Theory | Implementation |
|---|---|---|
| Valuation | Often real-valued / fixed-point ATL | ATLF engine over CGS |
| Syntax | ATL-like coalitions | Same surface family as ATL |

## Model-checking pipeline

```text
CGS.read_file -> ATLFParser.parse -> build_tree -> solve_tree -> result
```

Entry: `ATLF/ATLF.py`.

## Code map

| Path | Role |
|---|---|
| `ATLF/ATLF.py` | Entry |
| `ATLF/solver.py` | Dispatch |
| `ATLF/operators.py` | Operators |
| `ATLF/preimage.py` | Pre-image |
| `ATLF/real_value_utils.py` | Real-valued helpers |

## Tests

ATLF coverage under `model_checker/tests/` (parser and algorithm suites).
