# Operator-learning research programme

Scientific objective: qualify a computational forecast surrogate for full Lorenz
probability densities relevant to eventual Bayesian assimilation.
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

**NEXT_REQUIRED_GATE = OL-G00_PROBABILITY_DISTRIBUTION_ALIGNMENT.**
Alignment remains OPEN. G01–G17 are LOCKED. Large target campaigns, qualified
surrogate replacement, posterior-transfer qualification and operator-assisted
DA are not authorized. Cheap explicitly labelled diagnostics on the original
six pairs are allowed; they do not unlock gates. Do not tune on the original
test law and continue claiming untouched evaluation.

G00 comparison has completed: [results and population recommendation](evidence/G00_ALIGNMENT_V2_20261005.md).
Technical evidence is complete; owner approval of the restricted population and
generator roles remains pending. Passing numerical sanity checks did not promote G00.

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
