# Project state

Updated: 2026-09-11

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
- The corrected production-scale run reproduces the earlier Q2 accuracy and
  timestep results while satisfying cell-average and scaling-factor invariants.
  Adaptive Q2 passes its full-step branch gates but fails the half-step mass
  and cross-timestep density gates.

## Latest validated evidence

- Best short-time same-initial-law covariance error: `0.0855765`.
- Monte Carlo bootstrap p95 noise: `0.00628239`; error/noise ratio: `13.62`.
- Manufactured total-flux boundary test: approximately second-order L1
  convergence and maximum mass error `3.12e-12`.
- Q2 L2 projection preserves covariance to about `2.84e-10` before limiting,
  but the tested Q2 positivity treatment is too intrusive to justify adoption.
- The corrected controlled run confirms a reduction in corrected startup
  covariance error from Q1's `0.08719` to adaptive Q2's `0.02377`. Halving the
  timestep changes the corrected density by at least `L1=0.01552` and produces
  mass error `2.56e-10`; both exceed their predeclared limits.
- Truly unlimited backward-Euler Q2 is more accurate in covariance
  (`0.00727` full step, `0.00464` half step) but has integrated negative mass
  around `7e-4`. Its cross-timestep density difference is already at least
  `L1=0.00541`, so positivity correction magnifies rather than solely causes
  the timestep failure.
- Unlimited Crank--Nicolson Q2 passes the density timestep gate with
  `L1>=4.19e-5` and covariance-change gate with `4.74e-6`; its covariance error
  is about `0.00371`, but integrated negative mass remains about `8.28e-4`.

## Active blockers

1. No corrected mature-posterior forecast is validated near production
   resolution.
2. Spatial transport error and positivity enforcement dominate the remaining
   covariance discrepancy.
3. The independent finite-volume hierarchy is not converged enough to define a
   full-density truth error.
4. Crank--Nicolson resolves the controlled unlimited temporal gate, while a
   compatible positive and conservative correction remains unvalidated.

## Near-term research portfolio

The living plan is in `docs/RESEARCH_DIRECTIONS.md` and
`experiments/method-selection-research.yaml`. Current high-value branches are:

1. Evaluate the existing adaptive global limiter with Crank--Nicolson as a
   controlled comparator under the same two-timestep and limiter gates.
2. Pair the successful unlimited Crank--Nicolson path with a local
   algebraic/convex positivity treatment and re-evaluate whole-trajectory
   invariants; global polynomial scaling remains a comparator.
3. If corrected Crank--Nicolson or the local correction fails, prototype a
   full-SPD positive finite-volume/flux method.
   Directional FCDF and complete-flux methods remain a separate diagonal-noise
   branch rather than the general production target.
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
