# Operator-learning decisions

## 2026-10-06 — OL-D013: review mechanism v3 and predeclare direct empirical control

Owner asks to continue. evidence/G02_MECHANISM_V3_20261006.md records technical
completion, common-start integration resolution and remaining histogram/control
sensitivity. Source evidence and every accepted input remain unchanged.
Next bounded characterization: RECONSTRUCTION_EMPIRICAL_G02_V4.md with exact
empirical top-hat voxel integration, without histogram intermediate. Alternative
is diagnostic, not adopted population or manufactured target. Source arrays and
code/config hashes frozen first; all120 comparisons, raw invariants and failures
retained. No outcome-based exclusions, threshold relaxation or scientific pass.
G02 OPEN; later gates LOCKED; no FPE targets, training or DA. Self-review and
owner task authority, no independent assessor. Handoff immediately once running.

## 2026-10-06 — OL-D012: isolate G02 reconstruction mechanisms

Owner asks to continue G02 under the new integrity policy. Reviewed refinement_v2:
96 comparisons completed in11.781s;21 sealed files verified on prior check.
On finer comparison grid median histogram L1 .05483 (45→60), .11566 (60→90),
and full-burn-in integration difference .42664. These establish sensitivity,
not continuum truth or disqualification of fixed recorded occupation inputs.
All original evidence remains immutable; fresh diagnosticmechanism_v3 uses
common saved post-burn-in initial states and a labelled exact-box integration
control to separate discretized smoothing/lifting from histogram effects.
Source and config must be committed first; CPU-only132 comparisons, all attempt
counts/raw invariants retained. No accepted recipe, targets or model changed.
G02 OPEN, later gates LOCKED; characterization has no scientific pass authority.
Self-reviewed implementing agent; owner approval covers this bounded diagnostic,
not its outcomes. Stop/handoff once running with provisional ETA.

## 2026-10-06 — OL-D011: prohibit manufactured success across all stages

Owner explicitly requests durable controls and a gate audit following concerns
over earlier Gaussian choices. Establish SCIENTIFIC_INTEGRITY.md as cross-stage
authority and AGENTS.md as its task-entry pointer. Preserve accepted full
attractor-density scope, historical Gaussian/GMM fixtures and all old failures.
Audit all18 gates in INTEGRITY_GATE_AUDIT_20261006.md: legitimate variation,
all-attempt accounting, reference validity versus model failure, raw/final
interventions, target-independent evaluation and scoped generalization.

No Gaussian substitution or population change is authorized. Review finds
historical normalization/softplus and normalized shape metrics, requiring future
raw-constraint diagnostics; no new accusation of covert target repair is inferred.
This is a bounded policy/control audit, not exhaustive code/history certification.
Self-reviewed implementing agent under owner's direct instruction. No gate pass,
threshold change, historical evidence modification, solver/training change or
new run occurs. G02 OPEN, later gates LOCKED; no DA/production authority.

## 2026-10-06 — OL-D010: authorize second bounded characterization

Owner approved inexpensive finer-reference characterization and requests immediate
handoff once running. Freeze OL-G02_reconstruction_refinement_v2.json before
execution. Six fresh development seeds71029–71034, two RK4 steps, sampling
5000/10000/20000 and three histograms at fixed physical bandwidth, compared on
two conservative grids, produce96 diagnostics. Full spinup integration sensitivity
includes chaotic amplification. No bootstrap independence claims are made;
see https://stat.cmu.edu/~cshalizi/uADA/16/lectures/26.pdf.
Technical mass/positivity invariants remain; no scientific error budget or
qualification is invented. G02 OPEN, G03–G17 LOCKED. Draft qualification recipe
remains separate. No target generation, model training or historical overwrite.

## 2026-10-06 — OL-D009: archive G02 characterization; qualification remains OPEN

User requested analysis and continuation. Archive reviewed characterization
summaries and exact config/provenance/seal under evidence/G02_CHARACTERIZATION_20261006*.
The sealed run completed306 comparisons and technical invariants. Temporal
sampling contracts; histogram and regularization materially affect full density.
Scientific thresholds were not approved, so no scientific pass/fail is invented.
This supersedes the dispatch-pending current status under OL-D008, preserving
its historical authority and all raw evidence. Self-reviewed agent adjudication.

Draft v2 proposes fresh-seed sampling/integration/histogram controls. It has no
execution authority until the reconstruction budget/recipe is approved and
predeclared. G02 stays OPEN, G03–G17 LOCKED, production/DA unauthorized.
No solver/model/data changes, new target campaign or neural training occur.

## 2026-10-06 — OL-D008: permissions restored; authorize committed G02 dispatch

Owner refreshed the execution profile and requested another attempt. Git staging
succeeds and ./scripts/check reports90passed,1skipped, including MPI consistency.
Commit the existing frozen G02 characterization before dispatch and run it as a
persistent CPU-only local job. No threshold, input-family or historical evidence
changes. G02 remains OPEN: execution approval does not approve scientific results.
No FEM target campaign, neural training, posterior transfer or DA starts.

## 2026-10-06 — OL-D007: implement bounded G02 characterization; do not presume stability

Owner requested G02. Retain ATTRACTOR_DENSITY_V1 and implement the controlled
study in RECONSTRUCTION_STABILITY_G02_V1.md. Dense replay holds each physical
window fixed; random time-index reconstructions are independent conditional on
that discrete path, while block/ACF diagnostics explicitly retain dependence
limitations. Fixed physical smoothing separates histogram changes from bandwidth
changes as far as the existing vertex lifting allows. Different bandwidths are
different regularized laws, never hidden replacements of historical inputs.

Technical invariants and design are frozen in the characterization config.
No scientifically justified absolute reconstruction-error budget is currently
approved. Characterization completion must leave G02 OPEN. Review its results,
then predeclare a qualification recipe/budget and fresh evidence; no retrospective
conversion of these technical thresholds into a scientific pass.

At implementation this session's filesystem grants read-only .git access.
The predeclaration commit is required before dispatch, so no scientific run is
authorized to bypass that restriction. No FEM targets, training, DA experiments
or historical-data changes occur. G03 and all later gates remain LOCKED.

## 2026-10-05 — OL-D006: scoped G01 passes; G02 is next

v2 predeclared at9198921 passes all frozen checks on six initial/final archived
occupation-density pairs. See evidence/G01_REPRESENTATION_V2_20261005.md and
sealed JSON. All sample-to-vertex reconstructions and conservative pair casts
are bitwise identical; maximum initial physical L1 difference2.76e-14, export
mass discrepancy2.50e-13 and measured negative mass0. Preserve v1 failure.
Scoped technical adjudication by implementing agent under owner's G01 task
authorization; self-review, no independent assessor. Open G02 reconstruction
stability. Native replay, continuum accuracy, voxel resolution adequacy, actual
posterior relevance and scientific surrogate qualification remain unverified.
Retain owner-selected attractor population; no new target campaign/training.

## 2026-10-05 — OL-D005: G01 v1 fails; repair arithmetic and predeclare v2

v1 at predeclaration7bfe51a failed its strict bitwise reconstruction criterion
for all six laws. Other checks passed. Independent replay with the historical
vertex_density implementation reproduces archived vertices bitwise. The new
helper multiplied by precomputed cell volume instead of multiplying by whole
domain volume and then dividing by cell count; these real-arithmetic equivalents
differ in floating-point evaluation order (maximum nodal difference1.08e-19
for law0). Repair only the helper's evaluation order. Retain all v1 evidence,
retain every threshold unchanged, and predeclare v2 before rerunning. G01 remains
OPEN pending v2 technical adjudication; no model, target or population changes.

## 2026-10-05 — OL-D004: owner selects attractor-density scope and opens G01

Direct owner instruction: “Work on G01 I accept, keep the densities state space
distributions of an observed Lorenz attractor”. Accept the restricted family in
ACCEPTED_POPULATION_V1.md; do not infer acceptance of mixed/conditioned training.
G00 scoped population-definition review PASSED; G01 representation contract OPEN.
The G00 predeclared owner-review criterion is satisfied for this limited scope.
Its numerical results and thresholds are unchanged; application posterior
representativeness remains OPEN. OL-D003B's proposed mixed initial population is
superseded as the selected direction, without deleting its evidence or warnings.
No expensive dataset, scientific model, posterior-transfer or DA authorization.

## 2026-10-05 — OL-D003B: G00 evidence complete; population approval pending

The predeclared comparison at fe5607e completed in5.36 seconds. Technical checks
pass, 117 sealed artifacts rehash without mismatch. All evidence and limitations:
evidence/G00_ALIGNMENT_V2_20261005.md (tracked full report/provenance/seal).
Conditioning shifts exceed ensemble-replicate differences; nearest occupation
distances .771–1.949 and concentration/lobe changes support a mixed input
population proposal. Block resampling variation .493–.921 warns against treating
six occupation windows as assured independent/diverse laws.

Recommendation: occupation laws remain fixtures/stress inputs; use explicitly
defined unconditioned uncertainty and observation-conditioned full densities as
candidate application-directed families. The owner must approve their actual
roles and application scope after viewing evidence. Execution approval is not
retroactively presented as approval of results. G00 remains OPEN, G01–G17 LOCKED,
permissions unchanged. No arbitrary numerical coverage gate was added after run.

## 2026-10-05 — OL-D003A: predeclare small G00 alignment comparison

The user authorizes execution of G00. Freeze alignment_v2 rather than rewrite
the original v1 draft. Six archived occupation groups, block-resample diagnostics,
two small stochastic ensembles/group and truth-derived single-observation
conditioning investigate full-density population alignment. No FEM target or
neural training is dispatched. POPULATION_PROPOSAL_G00_V2.md records proposed
roles/exclusions; owner approval of the results remains required for promotion.
All comparisons are development evidence; no new held-out evaluation claim.

## 2026-10-05 — OL-D001: establish qualification before optimization

User explicitly authorizes a durable governance programme and new release.
Current stage is operator-learning qualification; eventual DA shapes the input
population but does not authorize assimilation experiments.
G00 distribution alignment is OPEN; all later gates LOCKED. Six-law completion
is engineering/restricted-learning evidence, not an alignment or qualification
pass. Preserve old pilot/GMM source and immutable runs; no new target campaign.

Mandatory linear/POD comparators follow from linearity of the fixed FPE in p.
FNO preference, occupation-law representativeness, learning-grid adequacy and
posterior transfer are unverified hypotheses.

Original test law was inspected on 2026-10-05. Any tuning driven by its revealed
failures uses development data; future serious generalization requires new
untouched evaluation. This supersedes future reuse as final evaluation without
changing the original split or historical score.

Phase A: this programme/OL-G00 draft establishes controls only. Its numerical
thresholds remain TO_BE_PREDECLARED_BEFORE_RUN; no scientific experiment is
claimed predeclared or passed. A retrospective pilot audit is separately labelled
non-gate evidence, with new hashes rather than edited old artifacts.

Review/approval basis: explicit user instruction in this task. Implementer is
the Git commit author; no independent scientific gate review is claimed.

## 2026-10-05 — OL-D002: adjudicate completed pilot as historical evidence

Read-only-source CPU audit at clean commit 7cb41a6 verifies six pair hashes and
reproduces principal statistical/boundary failures. Complete compact evidence,
original evaluation, hashes and limitations are in evidence/README.md and
evidence/PILOT_20261004T133438Z.json. New audit sealed SHA-256:
ed0f7de946b94c8d768846f0be2486093f3a514fefcf84f11e52d0fdf2c07340.
No historical payload was changed, no target generated and no retraining done.
Self-reviewed technical audit by the implementing agent; no independent assessor
or owner-approved scientific gate promotion is claimed.

Verdict: operational target-generation/CUDA-training feasibility and restricted
density-learning improvement demonstrated. Statistical fidelity and surrogate
qualification remain OPEN. Boundary and lobe failures, nearest-target performance,
inspected test access and unresolved final-epoch optimization prevent broader claims.
OL-C010 moves OPEN→EMPIRICAL under its limited reproducibility scope.
OL-G00 remains OPEN; G01–G17 LOCKED; next gate unchanged. v0.2.0 is a research
pre-release documenting this situation, with ignored payload limitations explicit.
