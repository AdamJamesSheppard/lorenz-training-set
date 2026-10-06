# Project current state

Updated: 2026-10-06

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
NEXT_REQUIRED_GATE = OL-G02_RECONSTRUCTION_STABILITY
```

The six-law pilot `runs/neural-pilot/20261004T133438Z` completed target generation
and GPU training. It demonstrates engineering feasibility and restricted density
learning. Its statistical, marginal, lobe and boundary errors prevent surrogate
qualification. The original test law has been inspected; reuse for tuning makes
it development data. G00 passed within the owner-approved restricted attractor-density scope; posterior relevance remains unverified.

Only inexpensive labelled development diagnostics, review of completed G02 and
committed refinement characterization v2 under OL-D010 are authorized. No large new target campaign or operator-assisted DA.

2026-10-05: user authorized the bounded G00 alignment comparison, predeclared
in experiments/operator_learning/OL-G00_alignment_v2.json. This generates only
small Monte Carlo/conditioning examples, without FEM targets or neural training.
At dispatch, G00 remained OPEN pending evidence and scoped population approval.

The v2 comparison completed: technical checks pass and 117 sealed files verify.
Results: docs/operator_learning/evidence/G00_ALIGNMENT_V2_20261005.md.
Owner subsequently selected the restricted attractor-density family (OL-D004),
passing scoped G00 and opening G01. G01 v2 subsequently passed under OL-D006;
G02 reconstruction stability is next. The mixed proposal is not approved.
No expensive target-generation permission has changed.

G02 implementation: docs/operator_learning/RECONSTRUCTION_STABILITY_G02_V1.md;
OL-D007 records the characterization design; OL-D008 restored dispatch.
Characterization completed and was reviewed under OL-D009; portable evidence:
docs/operator_learning/evidence/G02_CHARACTERIZATION_20261006.md.
G02 remains OPEN: scientific reconstruction-error budget and v2 recipe approval
are pending. The v2 qualification proposal is a draft, without qualification
dispatch authority; separate characterization refinement_v2 is authorized under OL-D010.

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
