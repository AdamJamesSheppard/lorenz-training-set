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

Research used for gate decisions is indexed in the
[cross-stage research audit](../research_audit/README.md), including preserved
G01 failure, G02 open characterizations and prospective-only later-gate sources.
Use the [searchable provenance graph](../research_audit/GRAPH.md) to trace both
successful and unsuccessful outcomes through their research and evidence.

**NEXT_REQUIRED_GATE = OL-G03_INPUT_DIVERSITY.**
G00 passed within the owner-selected attractor-density scope. G01 passed archived
representation checks; G02 passed scoped finite-control reconstruction under
OL-D021. G03 is OPEN; G04–G17 are LOCKED. Large target campaigns, qualified
surrogate replacement, posterior-transfer qualification and operator-assisted
DA are not authorized. Cheap explicitly labelled diagnostics on the original
six pairs are allowed; they do not unlock gates. Do not tune on the original
test law and continue claiming untouched evaluation.

G00 comparison has completed: [results and population recommendation](evidence/G00_ALIGNMENT_V2_20261005.md).
Owner accepted [the restricted attractor-density population](ACCEPTED_POPULATION_V1.md)
under OL-D004; the mixed proposal remains historical. Read the explicit
[representation contract](REPRESENTATION_CONTRACT_V1.md) for G01 details.
[G01 audit and limitations](evidence/G01_REPRESENTATION_V2_20261005.md) record the pass.
The next study concerns G03 diversity, retaining attractor densities without
assuming that different seeds supply different laws.
Posterior-population relevance remains unverified.

G03 starts with [bounded within/between-law characterization](INPUT_DIVERSITY_G03_V1.md).
All six G02 windows and four sampling phases are retained. Distinct finite-law
evidence does not establish universal initial-condition or population coverage.
Commit predeclaration before dispatch; OL-D023 records restored Git write access.

G03 v1 completed and is [reviewed without coverage promotion](evidence/G03_CHARACTERIZATION_V1_20261006.md)
under OL-D024. A [hierarchical coverage proposal](INPUT_COVERAGE_G03_V2_PROPOSAL.md)
is implemented and tested; OL-D026 restores access and authorizes committed
dispatch. Runner: scripts/run_input_coverage.py; config:
experiments/operator_learning/OL-G03_input_coverage_characterization_v2.json.
Dispatch requires a verified persistent launch. G03 remains OPEN. OL-D025 records the
cumulative-job ETA/handoff rule in root AGENTS.md.

OL-D027 prepares [window-local integration controls](WINDOW_LOCAL_CONTROL_G03_V3.md)
for every saved v2 law; original accumulated-control evidence stays unchanged.
OL-D028 restores access and authorizes committed persistent dispatch; G03 stays OPEN.

G02 implementation and controlled study design:
[reconstruction stability v1](RECONSTRUCTION_STABILITY_G02_V1.md).
Characterization has completed: [adjudication and limits](evidence/G02_CHARACTERIZATION_20261006.md).
Owner approved TV≤.01 against the declared finite control;
[qualification v5](RECONSTRUCTION_QUALIFICATION_V5.md) passed the frozen20k recipe
on all six fresh windows. [Adjudication and limits](evidence/G02_QUALIFICATION_V5_20261006.md).
Earlier v3 proposals and pending-budget decisions remain preserved history.
No expensive target campaign or model training is included.

Latest continuation: [grid-independent finite-control bound review](evidence/G02_BOUND_REVIEW_20261006.md).
Sampling phase bounds and aligned finite integration controls are now measured;
The approved budget stayed unchanged in v5; OL-D021 verifies and adjudicates the
fresh evidence. Changed FE transfer, reference applicability and grid fidelity
remain separate unresolved checks, not implied by the G02 pass.

OL-D010 authorizes the separate bounded CPU-only refinement characterization:
experiments/operator_learning/OL-G02_reconstruction_refinement_v2.json.
It completed with unresolved histogram/burn-in sensitivity. OL-D012 authorizes
[mechanism characterization v3](RECONSTRUCTION_MECHANISM_G02_V3.md), using one
common post-burn-in start and a labelled exact-box diagnostic, without replacing
the accepted density recipe or creating scientific qualification thresholds.
Mechanism_v3 [review and provenance](evidence/G02_MECHANISM_V3_20261006.md) records
technical completion. OL-D013 authorizes [empirical-box control v4](RECONSTRUCTION_EMPIRICAL_G02_V4.md)
to measure histogram sensitivity against a bin-free diagnostic on identical samples.
It completed; [verified v4 review](evidence/G02_EMPIRICAL_V4_20261006.md) records
all attempts and limitations. OL-D015 adds an analytic paired-kernel bound and
the historical v3 draft; OL-D020 later approved the budget and OL-D021 adjudicates v5.

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
