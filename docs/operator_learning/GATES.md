# Operator-learning scientific gates

Canonical schema: gates.json. This exact readable rendering is checked.
Each downstream gate is blocked until its prerequisite passes. Historical development
studies do not pass gates. Unspecified thresholds remain non-executable.
Each pass unlocks only the next gated study; DA/production need explicit approval.

## OL-G00_PROBABILITY_DISTRIBUTION_ALIGNMENT

- **id**: OL-G00_PROBABILITY_DISTRIBUTION_ALIGNMENT
- **question**: Are these the right probability distributions for the intended forecast problem?
- **scientific_motivation**: Define eventual posterior-input population; classify occupation laws as proxy/fixture/representative only with evidence.
- **prerequisites**: []
- **frozen_experiment_definition**: OL-G00_alignment_v2: small occupation/ensemble/single-observation comparison, committed before execution; original v1 draft preserved.
- **evidence_required**: Population contract and coverage/gap report; owner-reviewed law-family roles; no large FPE dataset needed.
- **metrics**: Generator semantics, conditioning, lobe imbalance, concentration, multimodality, transitions, tails; compare small occupation/stochastic ensemble/posterior-shaped collections.
- **predeclared_thresholds**: {"mass_error_max": 1e-10, "mass_rationale": "Reuse existing pilot numerical mass tolerance for representation sanity only; no population-coverage inference", "negative_mass_max": 0, "box_exit_count_max": 0, "technical_completion": "All required families and all frozen comparisons recorded with finite nonnegative normalized densities and complete metadata", "scientific_pass": "Owner approves a named intended population, explicit generator roles and exclusions after reviewing the frozen evidence. No numerical coverage threshold inferred from results.", "separation_diagnostic": "Report whether within-law replicate L1 is smaller than law-conditioning L1. This comparison is heuristic, not an acceptance threshold or confidence interval."}
- **pass_condition**: Owner-approved population contract, generator roles, explicit application-coverage limitations and reviewed evidence; any numerical comparison thresholds frozen before collecting its results.
- **failure_condition**: Any required criterion fails or evidence is missing; missing evidence remains OPEN rather than a fabricated FAIL/PASS.
- **what_passing_unlocks**: OL-G01_REPRESENTATION_CONTRACT design/qualification only; no automatic production or DA authorization.
- **what_failure_requires**: Preserve failed experiment; diagnose and predeclare a new version without outcome-driven relaxation.
- **claims_permitted_after_pass**: Only scoped probability distribution alignment evidence for the frozen population/config.
- **claims_still_forbidden_after_pass**: Unrestricted generalization, continuum accuracy without reference bounds, DA performance and production replacement.
- **relevant_assumptions**: ["OL-A02", "OL-A04", "OL-A07"]
- **experiment_config**: experiments/operator_learning/OL-G00_alignment_v2.json
- **evidence_run**: runs/operator-learning/OL-G00_alignment_v2/20261005T195958291168Z
- **decision_status**: PASSED
- **adjudication**: {"status": "PASSED_SCOPED_ATTRACTOR_POPULATION", "approver": "Adam James Sheppard; explicit instruction to accept attractor-derived densities and work on G01, 2026-10-05", "reviewer": "Implementing agent; self-review, no independent assessor", "date": "2026-10-05", "config_sha256": "2302ba319cae92f5452cd3a66cf0364d4627e20c6ae5c23be227d6cd4e02e6ee", "evidence_sha256": "ada2c3d1101dfea2ee4bf56fbea97a01306a24e3449aade50e06e10c34c1c9fc", "predeclaration_commit": "fe5607e0b4159605ca59c1a1d173f47f2119330b", "decision_record": "docs/operator_learning/DECISIONS.md OL-D004; docs/operator_learning/ACCEPTED_POPULATION_V1.md", "limitations": "Restricted regularized deterministic occupation-density forecast study. Mixed population not accepted; actual DA/posterior representativeness remains open. No production or dataset authorization."}

## OL-G01_REPRESENTATION_CONTRACT

- **id**: OL-G01_REPRESENTATION_CONTRACT
- **question**: Is every law-to-tensor transformation explicit and correct?
- **scientific_motivation**: μ→p→p_h→P_Vp_h→u must not silently change semantics.
- **prerequisites**: ["OL-G00_PROBABILITY_DISTRIBUTION_ALIGNMENT"]
- **frozen_experiment_definition**: REPRESENTATION_CONTRACT_V1.md and committed OL-G01_representation_v2.json; v1 failure preserved, same thresholds
- **evidence_required**: Conservative transfer fixtures and complete per-family representation records.
- **metrics**: Units, axes, mass, projection/lifting/scaling and normalization.
- **predeclared_thresholds**: {"mass_error_max": 1e-10, "negative_mass_max": 1e-13, "projection_export_l1_max": 1e-10, "float32_eps_multiplier": 4, "pair_cast_bitwise_equal": true, "reconstruction_bitwise_equal": true, "rationale": "Existing mass invariant; numerical negativity roundoff; aligned Q1/Q2 identity; machine-derived float32 budget. No continuum/resolution accuracy claim."}
- **pass_condition**: All frozen scientific and provenance criteria pass; named reviewer and approver record scope and limitations.
- **failure_condition**: Any required criterion fails or evidence is missing; missing evidence remains OPEN rather than a fabricated FAIL/PASS.
- **what_passing_unlocks**: OL-G02_RECONSTRUCTION_STABILITY design/qualification only; no automatic production or DA authorization.
- **what_failure_requires**: Preserve failed experiment; diagnose and predeclare a new version without outcome-driven relaxation.
- **claims_permitted_after_pass**: Only scoped representation contract evidence for the frozen population/config.
- **claims_still_forbidden_after_pass**: Unrestricted generalization, continuum accuracy without reference bounds, DA performance and production replacement.
- **relevant_assumptions**: ["OL-A01"]
- **experiment_config**: experiments/operator_learning/OL-G01_representation_v2.json
- **evidence_run**: null
- **decision_status**: OPEN
- **adjudication**: null

## OL-G02_RECONSTRUCTION_STABILITY

- **id**: OL-G02_RECONSTRUCTION_STABILITY
- **question**: Is empirical reconstruction stable?
- **scientific_motivation**: Separate finite-sample, temporal dependence and regularization uncertainty.
- **prerequisites**: ["OL-G01_REPRESENTATION_CONTRACT"]
- **frozen_experiment_definition**: Commit a versioned, non-DRAFT config and its hash before execution; current programme catalogue is not an executable predeclaration.
- **evidence_required**: Convergence and dependence-aware uncertainty reports; document N/A with proof of no reconstruction stage.
- **metrics**: Sample-count/bandwidth/grid/window sensitivity, observable autocorrelation/ESS, independent replicates.
- **predeclared_thresholds**: TO_BE_PREDECLARED_BEFORE_RUN
- **pass_condition**: All frozen scientific and provenance criteria pass; named reviewer and approver record scope and limitations.
- **failure_condition**: Any required criterion fails or evidence is missing; missing evidence remains OPEN rather than a fabricated FAIL/PASS.
- **what_passing_unlocks**: OL-G03_INPUT_DIVERSITY design/qualification only; no automatic production or DA authorization.
- **what_failure_requires**: Preserve failed experiment; diagnose and predeclare a new version without outcome-driven relaxation.
- **claims_permitted_after_pass**: Only scoped reconstruction stability evidence for the frozen population/config.
- **claims_still_forbidden_after_pass**: Unrestricted generalization, continuum accuracy without reference bounds, DA performance and production replacement.
- **relevant_assumptions**: ["OL-A01"]
- **experiment_config**: TO_BE_PREDECLARED_BEFORE_RUN
- **evidence_run**: null
- **decision_status**: LOCKED
- **adjudication**: null

## OL-G03_INPUT_DIVERSITY

- **id**: OL-G03_INPUT_DIVERSITY
- **question**: Do examples represent genuinely distinct laws?
- **scientific_motivation**: Repeated estimates of one invariant measure need not supply operator coverage.
- **prerequisites**: ["OL-G02_RECONSTRUCTION_STABILITY"]
- **frozen_experiment_definition**: Commit a versioned, non-DRAFT config and its hash before execution; current programme catalogue is not an executable predeclaration.
- **evidence_required**: Defined law families and hierarchical replicate comparison.
- **metrics**: Within-law versus between-law L1/TV; lobe/moment/shape diversity.
- **predeclared_thresholds**: TO_BE_PREDECLARED_BEFORE_RUN
- **pass_condition**: All frozen scientific and provenance criteria pass; named reviewer and approver record scope and limitations.
- **failure_condition**: Any required criterion fails or evidence is missing; missing evidence remains OPEN rather than a fabricated FAIL/PASS.
- **what_passing_unlocks**: OL-G04_REFERENCE_TARGET_APPLICABILITY design/qualification only; no automatic production or DA authorization.
- **what_failure_requires**: Preserve failed experiment; diagnose and predeclare a new version without outcome-driven relaxation.
- **claims_permitted_after_pass**: Only scoped input diversity evidence for the frozen population/config.
- **claims_still_forbidden_after_pass**: Unrestricted generalization, continuum accuracy without reference bounds, DA performance and production replacement.
- **relevant_assumptions**: ["OL-A01"]
- **experiment_config**: TO_BE_PREDECLARED_BEFORE_RUN
- **evidence_run**: null
- **decision_status**: LOCKED
- **adjudication**: null

## OL-G04_REFERENCE_TARGET_APPLICABILITY

- **id**: OL-G04_REFERENCE_TARGET_APPLICABILITY
- **question**: Is the reference accurate for the newly accepted population?
- **scientific_motivation**: GMM/startup certification cannot automatically transfer.
- **prerequisites**: ["OL-G03_INPUT_DIVERSITY"]
- **frozen_experiment_definition**: Commit a versioned, non-DRAFT config and its hash before execution; current programme catalogue is not an executable predeclaration.
- **evidence_required**: Controlled new-law reference studies; preserve raw/corrected diagnostics.
- **metrics**: Per-family h/dt/domain sensitivity, correction and reference error budget.
- **predeclared_thresholds**: TO_BE_PREDECLARED_BEFORE_RUN
- **pass_condition**: All frozen scientific and provenance criteria pass; named reviewer and approver record scope and limitations.
- **failure_condition**: Any required criterion fails or evidence is missing; missing evidence remains OPEN rather than a fabricated FAIL/PASS.
- **what_passing_unlocks**: OL-G05_EXPORT_FIDELITY design/qualification only; no automatic production or DA authorization.
- **what_failure_requires**: Preserve failed experiment; diagnose and predeclare a new version without outcome-driven relaxation.
- **claims_permitted_after_pass**: Only scoped reference target applicability evidence for the frozen population/config.
- **claims_still_forbidden_after_pass**: Unrestricted generalization, continuum accuracy without reference bounds, DA performance and production replacement.
- **relevant_assumptions**: ["OL-A01"]
- **experiment_config**: TO_BE_PREDECLARED_BEFORE_RUN
- **evidence_run**: null
- **decision_status**: LOCKED
- **adjudication**: null

## OL-G05_EXPORT_FIDELITY

- **id**: OL-G05_EXPORT_FIDELITY
- **question**: Does the learning representation preserve sufficient information?
- **scientific_motivation**: Conservative export and float32 do not imply shape fidelity.
- **prerequisites**: ["OL-G04_REFERENCE_TARGET_APPLICABILITY"]
- **frozen_experiment_definition**: Commit a versioned, non-DRAFT config and its hash before execution; current programme catalogue is not an executable predeclaration.
- **evidence_required**: Export/dtype error budget compared with required surrogate accuracy.
- **metrics**: FE→180×216×216→60×72×72, grid hierarchy, dtype L1/TV/moment error.
- **predeclared_thresholds**: TO_BE_PREDECLARED_BEFORE_RUN
- **pass_condition**: All frozen scientific and provenance criteria pass; named reviewer and approver record scope and limitations.
- **failure_condition**: Any required criterion fails or evidence is missing; missing evidence remains OPEN rather than a fabricated FAIL/PASS.
- **what_passing_unlocks**: OL-G06_DATA_PROVENANCE design/qualification only; no automatic production or DA authorization.
- **what_failure_requires**: Preserve failed experiment; diagnose and predeclare a new version without outcome-driven relaxation.
- **claims_permitted_after_pass**: Only scoped export fidelity evidence for the frozen population/config.
- **claims_still_forbidden_after_pass**: Unrestricted generalization, continuum accuracy without reference bounds, DA performance and production replacement.
- **relevant_assumptions**: ["OL-A01"]
- **experiment_config**: TO_BE_PREDECLARED_BEFORE_RUN
- **evidence_run**: null
- **decision_status**: LOCKED
- **adjudication**: null

## OL-G06_DATA_PROVENANCE

- **id**: OL-G06_DATA_PROVENANCE
- **question**: Are provenance, splits and evaluation independent?
- **scientific_motivation**: Prevent related-law leakage and inspected-test reuse.
- **prerequisites**: ["OL-G05_EXPORT_FIDELITY"]
- **frozen_experiment_definition**: Commit a versioned, non-DRAFT config and its hash before execution; current programme catalogue is not an executable predeclaration.
- **evidence_required**: Sealed manifest and new untouched final evaluation population.
- **metrics**: Hashes, group identity, seed streams, split overlap, evaluation access log.
- **predeclared_thresholds**: TO_BE_PREDECLARED_BEFORE_RUN
- **pass_condition**: All frozen scientific and provenance criteria pass; named reviewer and approver record scope and limitations.
- **failure_condition**: Any required criterion fails or evidence is missing; missing evidence remains OPEN rather than a fabricated FAIL/PASS.
- **what_passing_unlocks**: OL-G07_OPERATOR_STRUCTURE design/qualification only; no automatic production or DA authorization.
- **what_failure_requires**: Preserve failed experiment; diagnose and predeclare a new version without outcome-driven relaxation.
- **claims_permitted_after_pass**: Only scoped data provenance evidence for the frozen population/config.
- **claims_still_forbidden_after_pass**: Unrestricted generalization, continuum accuracy without reference bounds, DA performance and production replacement.
- **relevant_assumptions**: ["OL-A01"]
- **experiment_config**: TO_BE_PREDECLARED_BEFORE_RUN
- **evidence_run**: null
- **decision_status**: LOCKED
- **adjudication**: null

## OL-G07_OPERATOR_STRUCTURE

- **id**: OL-G07_OPERATOR_STRUCTURE
- **question**: How nonlinear is the corrected numerical forecast?
- **scientific_motivation**: Continuum fixed FPE is linear; correction can change this.
- **prerequisites**: ["OL-G06_DATA_PROVENANCE"]
- **frozen_experiment_definition**: Commit a versioned, non-DRAFT config and its hash before execution; current programme catalogue is not an executable predeclaration.
- **evidence_required**: Same physical-law representation and independently propagated mixtures.
- **metrics**: Δlin=||S_h(αp+(1−α)q)−αS_hp−(1−α)S_hq||L1; correlate with corrections.
- **predeclared_thresholds**: TO_BE_PREDECLARED_BEFORE_RUN
- **pass_condition**: All frozen scientific and provenance criteria pass; named reviewer and approver record scope and limitations.
- **failure_condition**: Any required criterion fails or evidence is missing; missing evidence remains OPEN rather than a fabricated FAIL/PASS.
- **what_passing_unlocks**: OL-G08_BASELINE_QUALIFICATION design/qualification only; no automatic production or DA authorization.
- **what_failure_requires**: Preserve failed experiment; diagnose and predeclare a new version without outcome-driven relaxation.
- **claims_permitted_after_pass**: Only scoped operator structure evidence for the frozen population/config.
- **claims_still_forbidden_after_pass**: Unrestricted generalization, continuum accuracy without reference bounds, DA performance and production replacement.
- **relevant_assumptions**: ["OL-A01", "OL-A09"]
- **experiment_config**: TO_BE_PREDECLARED_BEFORE_RUN
- **evidence_run**: null
- **decision_status**: LOCKED
- **adjudication**: null

## OL-G08_BASELINE_QUALIFICATION

- **id**: OL-G08_BASELINE_QUALIFICATION
- **question**: Which strong baselines qualify for comparison?
- **scientific_motivation**: No preferred FNO or persistence-only selection.
- **prerequisites**: ["OL-G07_OPERATOR_STRUCTURE"]
- **frozen_experiment_definition**: Commit a versioned, non-DRAFT config and its hash before execution; current programme catalogue is not an executable predeclaration.
- **evidence_required**: Baseline implementations/tests and fair frozen split/hyperparameter procedures.
- **metrics**: Persistence, nearest-target, learned linear, POD/PCA linear, modest CNN, FNO; matched budgets.
- **predeclared_thresholds**: TO_BE_PREDECLARED_BEFORE_RUN
- **pass_condition**: All frozen scientific and provenance criteria pass; named reviewer and approver record scope and limitations.
- **failure_condition**: Any required criterion fails or evidence is missing; missing evidence remains OPEN rather than a fabricated FAIL/PASS.
- **what_passing_unlocks**: OL-G09_FIT_FEASIBILITY design/qualification only; no automatic production or DA authorization.
- **what_failure_requires**: Preserve failed experiment; diagnose and predeclare a new version without outcome-driven relaxation.
- **claims_permitted_after_pass**: Only scoped baseline qualification evidence for the frozen population/config.
- **claims_still_forbidden_after_pass**: Unrestricted generalization, continuum accuracy without reference bounds, DA performance and production replacement.
- **relevant_assumptions**: ["OL-A01"]
- **experiment_config**: TO_BE_PREDECLARED_BEFORE_RUN
- **evidence_run**: null
- **decision_status**: LOCKED
- **adjudication**: null

## OL-G09_FIT_FEASIBILITY

- **id**: OL-G09_FIT_FEASIBILITY
- **question**: Can candidates fit controlled training subsets?
- **scientific_motivation**: Poor fit cannot be interpreted purely as generalization failure.
- **prerequisites**: ["OL-G08_BASELINE_QUALIFICATION"]
- **frozen_experiment_definition**: Commit a versioned, non-DRAFT config and its hash before execution; current programme catalogue is not an executable predeclaration.
- **evidence_required**: Controlled memorization/fit studies and optimization uncertainty.
- **metrics**: Training error, capacity/epoch/rate learning curves, scientific metrics.
- **predeclared_thresholds**: TO_BE_PREDECLARED_BEFORE_RUN
- **pass_condition**: All frozen scientific and provenance criteria pass; named reviewer and approver record scope and limitations.
- **failure_condition**: Any required criterion fails or evidence is missing; missing evidence remains OPEN rather than a fabricated FAIL/PASS.
- **what_passing_unlocks**: OL-G10_GENERALIZATION design/qualification only; no automatic production or DA authorization.
- **what_failure_requires**: Preserve failed experiment; diagnose and predeclare a new version without outcome-driven relaxation.
- **claims_permitted_after_pass**: Only scoped fit feasibility evidence for the frozen population/config.
- **claims_still_forbidden_after_pass**: Unrestricted generalization, continuum accuracy without reference bounds, DA performance and production replacement.
- **relevant_assumptions**: ["OL-A01"]
- **experiment_config**: TO_BE_PREDECLARED_BEFORE_RUN
- **evidence_run**: null
- **decision_status**: LOCKED
- **adjudication**: null

## OL-G10_GENERALIZATION

- **id**: OL-G10_GENERALIZATION
- **question**: Do candidates generalize within the accepted population?
- **scientific_motivation**: One held-out law cannot support tail-performance claims.
- **prerequisites**: ["OL-G09_FIT_FEASIBILITY"]
- **frozen_experiment_definition**: Commit a versioned, non-DRAFT config and its hash before execution; current programme catalogue is not an executable predeclaration.
- **evidence_required**: Independent law population; selection only on development; strong baselines.
- **metrics**: Median/p90/p95/worst L1/TV,L2,means,covariance,marginals,lobes,boundary with counts/uncertainty.
- **predeclared_thresholds**: TO_BE_PREDECLARED_BEFORE_RUN
- **pass_condition**: All frozen scientific and provenance criteria pass; named reviewer and approver record scope and limitations.
- **failure_condition**: Any required criterion fails or evidence is missing; missing evidence remains OPEN rather than a fabricated FAIL/PASS.
- **what_passing_unlocks**: OL-G11_STRUCTURAL_GENERALIZATION design/qualification only; no automatic production or DA authorization.
- **what_failure_requires**: Preserve failed experiment; diagnose and predeclare a new version without outcome-driven relaxation.
- **claims_permitted_after_pass**: Only scoped generalization evidence for the frozen population/config.
- **claims_still_forbidden_after_pass**: Unrestricted generalization, continuum accuracy without reference bounds, DA performance and production replacement.
- **relevant_assumptions**: ["OL-A01"]
- **experiment_config**: TO_BE_PREDECLARED_BEFORE_RUN
- **evidence_run**: null
- **decision_status**: LOCKED
- **adjudication**: null

## OL-G11_STRUCTURAL_GENERALIZATION

- **id**: OL-G11_STRUCTURAL_GENERALIZATION
- **question**: Do candidates generalize to held-out structures/families?
- **scientific_motivation**: Measure structure learning beyond nearby samples.
- **prerequisites**: ["OL-G10_GENERALIZATION"]
- **frozen_experiment_definition**: Commit a versioned, non-DRAFT config and its hash before execution; current programme catalogue is not an executable predeclaration.
- **evidence_required**: Entire family/group holdouts, no test-driven retraining.
- **metrics**: Same metrics by withheld family and training distance.
- **predeclared_thresholds**: TO_BE_PREDECLARED_BEFORE_RUN
- **pass_condition**: All frozen scientific and provenance criteria pass; named reviewer and approver record scope and limitations.
- **failure_condition**: Any required criterion fails or evidence is missing; missing evidence remains OPEN rather than a fabricated FAIL/PASS.
- **what_passing_unlocks**: OL-G12_PROBABILITY_STRUCTURE design/qualification only; no automatic production or DA authorization.
- **what_failure_requires**: Preserve failed experiment; diagnose and predeclare a new version without outcome-driven relaxation.
- **claims_permitted_after_pass**: Only scoped structural generalization evidence for the frozen population/config.
- **claims_still_forbidden_after_pass**: Unrestricted generalization, continuum accuracy without reference bounds, DA performance and production replacement.
- **relevant_assumptions**: ["OL-A01"]
- **experiment_config**: TO_BE_PREDECLARED_BEFORE_RUN
- **evidence_run**: null
- **decision_status**: LOCKED
- **adjudication**: null

## OL-G12_PROBABILITY_STRUCTURE

- **id**: OL-G12_PROBABILITY_STRUCTURE
- **question**: Are probability shape and statistics scientifically adequate?
- **scientific_motivation**: Positive mass-one output may still be useless.
- **prerequisites**: ["OL-G11_STRUCTURAL_GENERALIZATION"]
- **frozen_experiment_definition**: Commit a versioned, non-DRAFT config and its hash before execution; current programme catalogue is not an executable predeclaration.
- **evidence_required**: Fixed physical regions; output-background and loss ablations.
- **metrics**: Mass, negativity, L1/TV, marginals, mean/covariance, lobes, tails, fixed boundary region.
- **predeclared_thresholds**: TO_BE_PREDECLARED_BEFORE_RUN
- **pass_condition**: All frozen scientific and provenance criteria pass; named reviewer and approver record scope and limitations.
- **failure_condition**: Any required criterion fails or evidence is missing; missing evidence remains OPEN rather than a fabricated FAIL/PASS.
- **what_passing_unlocks**: OL-G13_SEMIGROUP design/qualification only; no automatic production or DA authorization.
- **what_failure_requires**: Preserve failed experiment; diagnose and predeclare a new version without outcome-driven relaxation.
- **claims_permitted_after_pass**: Only scoped probability structure evidence for the frozen population/config.
- **claims_still_forbidden_after_pass**: Unrestricted generalization, continuum accuracy without reference bounds, DA performance and production replacement.
- **relevant_assumptions**: ["OL-A01"]
- **experiment_config**: TO_BE_PREDECLARED_BEFORE_RUN
- **evidence_run**: null
- **decision_status**: LOCKED
- **adjudication**: null

## OL-G13_SEMIGROUP

- **id**: OL-G13_SEMIGROUP
- **question**: Does composed forecast agree with independent 2T reference?
- **scientific_motivation**: Self-consistency alone is insufficient.
- **prerequisites**: ["OL-G12_PROBABILITY_STRUCTURE"]
- **frozen_experiment_definition**: Commit a versioned, non-DRAFT config and its hash before execution; current programme catalogue is not an executable predeclaration.
- **evidence_required**: Independent 2T targets and identical initial-law representation.
- **metrics**: ||ŜT(ŜTp)−S2Tp|| and one-shot 2T reference/approximation where available.
- **predeclared_thresholds**: TO_BE_PREDECLARED_BEFORE_RUN
- **pass_condition**: All frozen scientific and provenance criteria pass; named reviewer and approver record scope and limitations.
- **failure_condition**: Any required criterion fails or evidence is missing; missing evidence remains OPEN rather than a fabricated FAIL/PASS.
- **what_passing_unlocks**: OL-G14_ROLLOUT design/qualification only; no automatic production or DA authorization.
- **what_failure_requires**: Preserve failed experiment; diagnose and predeclare a new version without outcome-driven relaxation.
- **claims_permitted_after_pass**: Only scoped semigroup evidence for the frozen population/config.
- **claims_still_forbidden_after_pass**: Unrestricted generalization, continuum accuracy without reference bounds, DA performance and production replacement.
- **relevant_assumptions**: ["OL-A01"]
- **experiment_config**: TO_BE_PREDECLARED_BEFORE_RUN
- **evidence_run**: null
- **decision_status**: LOCKED
- **adjudication**: null

## OL-G14_ROLLOUT

- **id**: OL-G14_ROLLOUT
- **question**: Are repeated forecasts stable without observations?
- **scientific_motivation**: One-step accuracy cannot certify accumulation.
- **prerequisites**: ["OL-G13_SEMIGROUP"]
- **frozen_experiment_definition**: Commit a versioned, non-DRAFT config and its hash before execution; current programme catalogue is not an executable predeclaration.
- **evidence_required**: Independent long forecast references and rollout diagnostics.
- **metrics**: Horizon-wise density/statistical/constraint/boundary errors and failures.
- **predeclared_thresholds**: TO_BE_PREDECLARED_BEFORE_RUN
- **pass_condition**: All frozen scientific and provenance criteria pass; named reviewer and approver record scope and limitations.
- **failure_condition**: Any required criterion fails or evidence is missing; missing evidence remains OPEN rather than a fabricated FAIL/PASS.
- **what_passing_unlocks**: OL-G15_ACCURACY_COST design/qualification only; no automatic production or DA authorization.
- **what_failure_requires**: Preserve failed experiment; diagnose and predeclare a new version without outcome-driven relaxation.
- **claims_permitted_after_pass**: Only scoped rollout evidence for the frozen population/config.
- **claims_still_forbidden_after_pass**: Unrestricted generalization, continuum accuracy without reference bounds, DA performance and production replacement.
- **relevant_assumptions**: ["OL-A01"]
- **experiment_config**: TO_BE_PREDECLARED_BEFORE_RUN
- **evidence_run**: null
- **decision_status**: LOCKED
- **adjudication**: null

## OL-G15_ACCURACY_COST

- **id**: OL-G15_ACCURACY_COST
- **question**: Which candidate meets the accuracy/cost frontier?
- **scientific_motivation**: Training timer is not solver-replacement speedup.
- **prerequisites**: ["OL-G14_ROLLOUT"]
- **frozen_experiment_definition**: Commit a versioned, non-DRAFT config and its hash before execution; current programme catalogue is not an executable predeclaration.
- **evidence_required**: Matched hardware/workload benchmarks incl FEM, linear and nonlinear models.
- **metrics**: Warm/cold/batch latency with synchronization, throughput, memory, export/setup cost; error Pareto.
- **predeclared_thresholds**: TO_BE_PREDECLARED_BEFORE_RUN
- **pass_condition**: All frozen scientific and provenance criteria pass; named reviewer and approver record scope and limitations.
- **failure_condition**: Any required criterion fails or evidence is missing; missing evidence remains OPEN rather than a fabricated FAIL/PASS.
- **what_passing_unlocks**: OL-G16_POSTERIOR_TRANSFER design/qualification only; no automatic production or DA authorization.
- **what_failure_requires**: Preserve failed experiment; diagnose and predeclare a new version without outcome-driven relaxation.
- **claims_permitted_after_pass**: Only scoped accuracy cost evidence for the frozen population/config.
- **claims_still_forbidden_after_pass**: Unrestricted generalization, continuum accuracy without reference bounds, DA performance and production replacement.
- **relevant_assumptions**: ["OL-A01"]
- **experiment_config**: TO_BE_PREDECLARED_BEFORE_RUN
- **evidence_run**: null
- **decision_status**: LOCKED
- **adjudication**: null

## OL-G16_POSTERIOR_TRANSFER

- **id**: OL-G16_POSTERIOR_TRANSFER
- **question**: Does a qualified forecast transfer to actual posterior laws?
- **scientific_motivation**: Proxy success cannot stand in for posterior coverage.
- **prerequisites**: ["OL-G15_ACCURACY_COST"]
- **frozen_experiment_definition**: Commit a versioned, non-DRAFT config and its hash before execution; current programme catalogue is not an executable predeclaration.
- **evidence_required**: New posterior family records and frozen forecast-only targets; no full DA claim.
- **metrics**: Forecast metrics on full FE posteriors from defined prior/likelihood; no state refit.
- **predeclared_thresholds**: TO_BE_PREDECLARED_BEFORE_RUN
- **pass_condition**: All frozen scientific and provenance criteria pass; named reviewer and approver record scope and limitations.
- **failure_condition**: Any required criterion fails or evidence is missing; missing evidence remains OPEN rather than a fabricated FAIL/PASS.
- **what_passing_unlocks**: OL-G17_SEQUENTIAL_INTERFACE design/qualification only; no automatic production or DA authorization.
- **what_failure_requires**: Preserve failed experiment; diagnose and predeclare a new version without outcome-driven relaxation.
- **claims_permitted_after_pass**: Only scoped posterior transfer evidence for the frozen population/config.
- **claims_still_forbidden_after_pass**: Unrestricted generalization, continuum accuracy without reference bounds, DA performance and production replacement.
- **relevant_assumptions**: ["OL-A01"]
- **experiment_config**: TO_BE_PREDECLARED_BEFORE_RUN
- **evidence_run**: null
- **decision_status**: LOCKED
- **adjudication**: null

## OL-G17_SEQUENTIAL_INTERFACE

- **id**: OL-G17_SEQUENTIAL_INTERFACE
- **question**: Is the repeated posterior-to-forecast interface sound?
- **scientific_motivation**: Authorize integration only after complete forecast qualification.
- **prerequisites**: ["OL-G16_POSTERIOR_TRANSFER"]
- **frozen_experiment_definition**: Commit a versioned, non-DRAFT config and its hash before execution; current programme catalogue is not an executable predeclaration.
- **evidence_required**: Full-density interface tests; separate DA programme predeclaration before DA execution.
- **metrics**: Conservation, representation transfer, repeated-call statistics and failure/fallback handling.
- **predeclared_thresholds**: TO_BE_PREDECLARED_BEFORE_RUN
- **pass_condition**: All frozen scientific and provenance criteria pass; named reviewer and approver record scope and limitations.
- **failure_condition**: Any required criterion fails or evidence is missing; missing evidence remains OPEN rather than a fabricated FAIL/PASS.
- **what_passing_unlocks**: Eligibility to PROPOSE a separately predeclared operator-assisted DA programme; requires explicit approval.
- **what_failure_requires**: Preserve failed experiment; diagnose and predeclare a new version without outcome-driven relaxation.
- **claims_permitted_after_pass**: Only scoped sequential interface evidence for the frozen population/config.
- **claims_still_forbidden_after_pass**: Unrestricted generalization, continuum accuracy without reference bounds, DA performance and production replacement.
- **relevant_assumptions**: ["OL-A01"]
- **experiment_config**: TO_BE_PREDECLARED_BEFORE_RUN
- **evidence_run**: null
- **decision_status**: LOCKED
- **adjudication**: null
