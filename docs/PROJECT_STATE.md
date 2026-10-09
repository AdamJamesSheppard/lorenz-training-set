# Project current state

Updated: 2026-10-06

## Current programme authority

Mandatory across all stages: [REQ-RT-001 research traceability](../RESEARCH_TRACEABILITY.md).
Method/source/outcome records are required before scientific qualification;
historical audit gaps remain explicit and do not rewrite old evidence.

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
NEXT_REQUIRED_GATE = OL-G04_REFERENCE_TARGET_APPLICABILITY
```

The six-law pilot `runs/neural-pilot/20261004T133438Z` completed target generation
and GPU training. It demonstrates engineering feasibility and restricted density
learning. Its statistical, marginal, lobe and boundary errors prevent surrogate
qualification. The original test law has been inspected; reuse for tuning makes
it development data. G00 passed within the owner-approved restricted attractor-density scope; posterior relevance remains unverified.

OL-D014 records approval with reservations of a bin-free reconstruction candidate.
Owner subsequently approved finite-control reconstruction TV≤.01 (OL-D020).
G02 qualification_v5 now PASSED within the finite-control scope (OL-D021).
G03 input diversity PASSED within its fresh finite-control scope (OL-D032);
changed bin-free FE transfer and reference/export
checks remain necessary before expensive targets. No target campaign or DA.
OL-D024 reviews completed G03 v1: resolved finite-law variation, no coverage
promotion. OL-D025 implements/tests hierarchical coverage v2; OL-D026 restores
access and authorizes committed dispatch. V2 completed; OL-D027 prepares
window-local controls with unchanged laws. OL-D028 restores committed v3
dispatch. V3 completed; OL-D029 records36 supported local-control bounds and
retained G03 OPEN at that historical stage pending prospective criteria/scope.
OL-D030 approves law-diversity scope; training adequacy remains OPEN for later
evaluation. OL-D031 prospectively froze fresh24-law qualification v4. OL-D032
reviews completed evidence:24/24 laws and all276 pairs supported, no failures,
zero negative mass. G03 scoped PASSED; G04 reference applicability OPEN.
No target campaign, training, surrogate qualification, production or DA authorized.
See operator-learning state.
Eventual analysis follows [the full-density Bayesian contract](BAYESIAN_ASSIMILATION_CONTRACT.md).

2026-10-05: user authorized the bounded G00 alignment comparison, predeclared
in experiments/operator_learning/OL-G00_alignment_v2.json. This generates only
small Monte Carlo/conditioning examples, without FEM targets or neural training.
At dispatch, G00 remained OPEN pending evidence and scoped population approval.

The v2 comparison completed: technical checks pass and 117 sealed files verify.
Results: docs/operator_learning/evidence/G00_ALIGNMENT_V2_20261005.md.
Owner subsequently selected the restricted attractor-density family (OL-D004),
passing scoped G00 and opening G01. G01 v2 subsequently passed under OL-D006;
G02 later passed scoped v5; G03 input diversity is next. The mixed proposal is not approved.
No expensive target-generation permission has changed.

G02 implementation: docs/operator_learning/RECONSTRUCTION_STABILITY_G02_V1.md;
OL-D007 records the characterization design; OL-D008 restored dispatch.
Characterization completed and was reviewed under OL-D009; portable evidence:
docs/operator_learning/evidence/G02_CHARACTERIZATION_20261006.md.
Earlier characterizations left G02 OPEN pending budget and qualification. Those
historical decisions remain preserved; OL-D021 adjudicates the fresh v5 pass.
Candidate approval under OL-D014 retains its original reservations.
The historical v3 proposal remains a draft; qualification_v5 is now frozen under
OL-D020. OL-D015 verifies empirical_v4 and adds an analytic paired-box
bound; see operator_learning/evidence/G02_EMPIRICAL_V4_20261006.md.
Mechanism_v3 completed; its reviewed evidence is in
operator_learning/evidence/G02_MECHANISM_V3_20261006.md. Empirical_v4 is authorized
under OL-D013 as a diagnostic only; OL-D014 subsequently approves the candidate
with reservations for qualification, preserving historical accepted inputs.

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
