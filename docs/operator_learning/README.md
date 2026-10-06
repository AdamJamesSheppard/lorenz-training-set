# Operator-learning research programme

Read [the repository-wide scientific-integrity policy](../../SCIENTIFIC_INTEGRITY.md)
and [the gate-by-gate integrity audit](INTEGRITY_GATE_AUDIT_20261006.md) before
implementation/adjudication. Preserve legitimate variation; never manufacture
apparent success by silently changing populations, outputs or evaluation cases.

Scientific objective: qualify a computational forecast surrogate for full Lorenz
probability densities relevant to eventual Bayesian assimilation.
Eventual analysis must follow the [full-density Bayesian contract](../BAYESIAN_ASSIMILATION_CONTRACT.md).
Owner's [candidate approval with reservations](RECONSTRUCTION_CANDIDATE_APPROVAL_V2.md)
does not pass G02 or authorize posterior smoothing, training or assimilation.
Current stage: **OPERATOR_LEARNING_QUALIFICATION**; eventual application:
density-based Bayesian data assimilation. The original six-law pilot is an
engineering/restricted-learning milestone, not a qualification-gate pass.

## Read in this order

1. PROBLEM.md — scientific object, fixed physics and forbidden claims.
2. PROJECT_STATE.md — canonical current state; state.json is its checked encoding.
3. DISTRIBUTION_CONTRACT.md — probability semantics and generator permissions.
4. GATES.md — all 18 gates; gates.json is the checked structured catalogue.
5. DATA_CONTRACT.md — immutable data/run interfaces and leakage controls.
6. CLAIMS.md, assumptions.yaml, DECISIONS.md — evidence, dependencies and reasons.
7. GOVERNANCE.md, ARCHITECTURE.md, RISKS.md — authority, checks and boundaries.
8. FEM_GOVERNANCE_RECONSTRUCTION.md and evidence/ — history and audit pointers.

**NEXT_REQUIRED_GATE = OL-G02_RECONSTRUCTION_STABILITY.**
G00 passed within the owner-selected attractor-density scope. G01 passed scoped representation checks. G02 is OPEN; G03–G17 are LOCKED. Large target campaigns, qualified
surrogate replacement, posterior-transfer qualification and operator-assisted
DA are not authorized. Cheap explicitly labelled diagnostics on the original
six pairs are allowed; they do not unlock gates. Do not tune on the original
test law and continue claiming untouched evaluation.

G00 comparison has completed: [results and population recommendation](evidence/G00_ALIGNMENT_V2_20261005.md).
Owner accepted [the restricted attractor-density population](ACCEPTED_POPULATION_V1.md)
under OL-D004; the mixed proposal remains historical. Read the explicit
[representation contract](REPRESENTATION_CONTRACT_V1.md) for G01 details.
[G01 audit and limitations](evidence/G01_REPRESENTATION_V2_20261005.md) record the pass.
The next study concerns G02 reconstruction stability, retaining attractor densities.
Posterior-population relevance remains unverified.

G02 implementation and controlled study design:
[reconstruction stability v1](RECONSTRUCTION_STABILITY_G02_V1.md).
Characterization has completed: [adjudication and limits](evidence/G02_CHARACTERIZATION_20261006.md).
G02 remains OPEN. Review the [v2 qualification proposal](RECONSTRUCTION_QUALIFICATION_PROPOSAL_V2.md)
and approve a scientific error budget before executable predeclaration or dispatch.
No expensive target campaign or model training is included.

OL-D010 authorizes the separate bounded CPU-only refinement characterization:
experiments/operator_learning/OL-G02_reconstruction_refinement_v2.json.
It completed with unresolved histogram/burn-in sensitivity. OL-D012 authorizes
[mechanism characterization v3](RECONSTRUCTION_MECHANISM_G02_V3.md), using one
common post-burn-in start and a labelled exact-box diagnostic, without replacing
the accepted density recipe or creating scientific qualification thresholds.
Mechanism_v3 [review and provenance](evidence/G02_MECHANISM_V3_20261006.md) records
technical completion. OL-D013 authorizes [empirical-box control v4](RECONSTRUCTION_EMPIRICAL_G02_V4.md)
to measure histogram sensitivity against a bin-free diagnostic on identical samples.

## Standard commands (from repository root)

- `python scripts/check_operator_learning.py`: dependency-free canonical checks.
- `python -m pytest -q tests/operator_learning`: fast checks (NumPy needed).
- `./scripts/check`: existing whole-repository software checks.
- `./scripts/verify-math`: FEM scientific consistency/invariants; no OL promotion.
- `python scripts/prepare_operator_run.py CONFIG`: freeze a fully predeclared
  committed experiment into a fresh run; never launches solvers or training.
- `.venv/neural-pilot/bin/python scripts/audit_operator_pilot.py RUN OUTPUT`:
  read-only-source historical checkpoint audit, writing only a NEW output directory.

Evidence: new `runs/operator-learning/<experiment>/<UTC>/`; historical pilot:
`runs/neural-pilot/20261004T133438Z`. Large payloads stay ignored; commit compact
reports, hashes and conclusions. Missing local evidence is reported, not invented.
The FNO, linear, POD and convolutional candidates compete; none is preferred by title.
