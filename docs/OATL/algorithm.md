# OATL - Algorithm Reference

Scope: denotations and code path for OATL in
`model_checker/algorithms/explicit/OATL/`.

## Model

- Type: `costCGS`
- Requires action / transition cost data (`get_cost_for_action`).

## Formula language

Parser: `parsers/formulas/OATL/parser.py`

```text
phi ::= ... | <A><k> X phi | <A><k> F phi | <A><k> G phi | <A><k>(phi U psi)
```

Bound `k` is mandatory and positive. `R` and `W` are rejected at parse time.

## Semantic denotations

`<A><k> phi` means coalition `A` can enforce `phi` while every chosen transition
has cost at most `k` (per-step affordability, not path-sum).

Pre-image filtering lives in `OATL/preimage.py` and shared
`oatl_index_preimage` helpers. An ATL prefilter may run before full OATL solve.

Implementation techniques (cost caches + reset, `pre_by_index`, bit-vector, ATL prefilter): [algorithm_design.md](../algorithm_design.md).

## Theory vs implementation

| Aspect | Theory | Implementation |
|---|---|---|
| Bound | Cost budget | Per-step transition cost `<= k` |
| R / W | Often present | Rejected; use dual forms or COTL |
| Engine | Cost ATL | OATL filter + fixpoints (not COTL) |

## Model-checking pipeline

```text
costCGS.read_file -> OATLParser.parse -> build_tree
  -> (optional ATL prefilter) -> solve_tree -> result
```

Entry: `OATL/OATL.py`.

## Code map

| Path | Role |
|---|---|
| `OATL/OATL.py` | Entry |
| `OATL/solver.py` | Dispatch |
| `OATL/operators.py` | Operators |
| `OATL/preimage.py` | Cost-filtered pre-image |

## Tests

OATL fixtures under costCGS tests and algorithm integration suites.
