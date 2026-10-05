# Project current state

Updated: 2026-10-05

## Current programme authority

The active programme is **OPERATOR_LEARNING_QUALIFICATION**. Canonical status,
18 gates, probability semantics and authorization controls are in
[docs/operator_learning/README.md](operator_learning/README.md) and
[operator-learning state](operator_learning/PROJECT_STATE.md).

```ini
PROGRAMME = OPERATOR_LEARNING_QUALIFICATION
CURRENT_MODEL_SCIENTIFICALLY_QUALIFIED = false
PRODUCTION_DATASET_AUTHORIZED = false
OPERATOR_SURROGATE_AUTHORIZED_FOR_DA = false
OPERATOR_PRODUCTION_AUTHORIZED = false
NEXT_REQUIRED_GATE = OL-G00_PROBABILITY_DISTRIBUTION_ALIGNMENT
```

The six-law pilot `runs/neural-pilot/20261004T133438Z` completed target generation
and GPU training. It demonstrates engineering feasibility and restricted density
learning. Its statistical, marginal, lobe and boundary errors prevent surrogate
qualification. The original test law has been inspected; reuse for tuning makes
it development data. Distribution alignment remains unresolved.

Only inexpensive labelled development diagnostics and design of the alignment
study are authorized. No large new target campaign or operator-assisted DA.

2026-10-05: user authorized the bounded G00 alignment comparison, predeclared
in experiments/operator_learning/OL-G00_alignment_v2.json. This generates only
small Monte Carlo/conditioning examples, without FEM targets or neural training.
G00 remains OPEN pending evidence and scoped population approval.

## FEM evidence remains separate

`METHOD_SELECTION_REPORT.md` remains the FEM method-selection authority.
`METHOD_STATUS = MATURE_STATE_STATISTICAL_AND_POSITIVITY_GATES_PASSED`;
mature full-density continuum convergence remains open. Tested domain expansions
passed for their historical law/configuration. These results do not automatically
certify the new occupation-law population or authorize production.

The complete prior state document, including its chronology and stale dispatch
statements, is preserved verbatim in
[the dated snapshot](history/PROJECT_STATE_before_operator_learning_20261005.md).
Its historical FEM next gate is not the active operator-learning next gate.
