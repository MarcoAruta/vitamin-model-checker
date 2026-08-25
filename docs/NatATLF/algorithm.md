# NatATLF - Algorithm Reference

Scope: denotations and code path for NatATLF in
`model_checker/algorithms/explicit/NatATLF/`.

## Model

- Type: `CGS`
- Same models as NatATL.

## Formula language

Parser: `parsers/formulas/NatATLF/parser.py`

Same surface family as NatATL:

```text
<{A}, k> F goal
```

## Semantic denotations

NatATLF uses NatATL-like syntax and delegates checking to the memoryless NatATL
solver path. Report shape matches NatATL memoryless (`Satisfiability`, `res`,
`initial_state`).

Implementation techniques (delegates to NatATL memoryless design): [algorithm_design.md](../algorithm_design.md).

## Theory vs implementation

| Aspect | Theory | Implementation |
|---|---|---|
| Relation to NatATL | Fixed-point / related flavor | Delegates to memoryless NatATL |
| Syntax | `<{A}, k>` | Shared with NatATL |

## Model-checking pipeline

```text
CGS.read_file -> NatATLFParser.parse -> NatATL memoryless path -> result
```

Entry: `NatATLF/NatATL.py`.

## Code map

| Path | Role |
|---|---|
| `NatATLF/NatATL.py` | Entry / delegation |

## Tests

Shared NatATL / NatATLF coverage under `model_checker/tests/`.
