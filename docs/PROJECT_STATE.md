# Project state

Updated: 2026-09-10

## Objective

Determine which conservative, sufficiently positive and accurate numerical
method should generate stochastic Lorenz-63 Fokker--Planck forecast targets for
neural-operator training. Develop and compare DOLFINx and non-DOLFINx candidates
as justified, then use only a certified configuration to generate training
pairs.

This file is a current snapshot, not a frozen roadmap. Update it whenever new
evidence changes the best comparator, active blockers, candidate ranking, or
next experiment.

## Current decision

- Method-selection classification: `INSUFFICIENT_EVIDENCE`.
- Large neural-operator dataset generation: `NO`.
- Strongest tested interim comparator: Q1 DG, upwind advection, SIPG diffusion,
  backward Euler, quadrature-14 L2 initialization and projected Bayesian
  analysis, followed by the conservative two-stage positivity limiter.
- This is neither a certified production method nor a requirement that future
  work remain on the Q1/DG path.
- The most informative next experiment is a same-physical-mesh, same-timestep
  Q1/Q2 comparison from one positive represented law, with raw Q2 negativity
  classified before correction. Adaptive Bernstein subdivision is a diagnostic
  and sufficient certificate in this experiment, not a selected production
  limiter.

## Latest validated evidence

- Best short-time same-initial-law covariance error: `0.0855765`.
- Monte Carlo bootstrap p95 noise: `0.00628239`; error/noise ratio: `13.62`.
- Manufactured total-flux boundary test: approximately second-order L1
  convergence and maximum mass error `3.12e-12`.
- Q2 L2 projection preserves covariance to about `2.84e-10` before limiting,
  but the tested Q2 positivity treatment is too intrusive to justify adoption.

## Active blockers

1. No corrected mature-posterior forecast is validated near production
   resolution.
2. Spatial transport error and positivity enforcement dominate the remaining
   covariance discrepancy.
3. The independent finite-volume hierarchy is not converged enough to define a
   full-density truth error.
4. The existing equal-DOF Q1/Q2 comparison also changed physical cell size and
   timestep, so it cannot isolate polynomial-degree accuracy.

## Near-term research portfolio

The living plan is in `docs/RESEARCH_DIRECTIONS.md` and
`experiments/method-selection-research.yaml`. Current high-value branches are:

1. Run the predeclared same-mesh Q2 falsification experiment in
   `METHOD_SELECTION_REPORT.md`: Q1 and Q2 on `30x36x36`, `dt=0.000625`, from
   the same positive Q1 law embedded exactly in Q2. Classify every raw Q2 cell
   as certified non-negative, witnessed negative, or unresolved before applying
   any correction.
2. If raw Q2 is accurate but corrected Q2 fails limiter gates, develop a local
   algebraic/convex flux correction rather than another global polynomial
   scaling variant.
3. If raw Q2 fails, close that branch and prototype a full-SPD positive
   finite-volume/flux method. Directional FCDF and complete-flux methods remain
   a separate diagonal-noise branch rather than the general production target.
4. Develop a dynamically scaled whole-space Hermite solver as an independent
   high-order reference after the Q2 gate.
5. Investigate covariance-targeted goal-oriented/nonuniform resolution and a
   genuinely high-order independent deterministic reference.
6. Regenerate and test mature DA states only after the initialization,
   analysis, and positivity path used to produce them is acceptable.

`experiments/mature-state-decision.yaml` remains a later certification stage,
but it now permits any candidate that survives the earlier controlled method
comparison. Threshold changes must be justified and versioned before the runs
they assess.

## Production diffusion scope

The production method must ultimately support a constant general
`B in R^(3x3)`, hence a full SPD `D=BB^T/2` and mixed derivatives. Identity
`B` remains the controlled test case. Directional diagonal-only methods may be
kept as special-case challengers but cannot certify the general production role.

## Canonical evidence

- Human-readable decision: `METHOD_SELECTION_REPORT.md`
- Machine-readable decision: `method_selection_report.json`
- Method definition: `NUMERICAL_METHOD.md`
- Positivity scope: `POSITIVITY_AUDIT.md`
