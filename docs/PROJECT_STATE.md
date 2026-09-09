# Project state

Updated: 2026-09-09

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

## Near-term research portfolio

The living plan is in `docs/RESEARCH_DIRECTIONS.md` and
`experiments/method-selection-research.yaml`. Current high-value branches are:

1. Diagnose whether Q2 is reacting to genuine negativity or a conservative
   fixed-subcell Bernstein certificate; test adaptive subdivision first.
2. Compare minimally intrusive Q2 positivity approaches, including constrained
   projection and local algebraic/convex flux limiting, while preserving the
   strong pre-limiter moment result.
3. Compare Q1 and repaired Q2 on equal physical meshes as well as equal degrees
   of freedom, time, and memory.
4. Add a structurally suitable transport challenger: FCDF/directional or
   Scharfetter--Gummel/complete-flux methods are especially relevant if `B`
   remains diagonal; full anisotropic `B` shifts priority toward DG/AFC and
   full-tensor flux methods.
5. Investigate covariance-targeted goal-oriented/nonuniform resolution and a
   genuinely high-order independent deterministic reference.
6. Regenerate and test mature DA states only after the initialization,
   analysis, and positivity path used to produce them is acceptable.

`experiments/mature-state-decision.yaml` remains a later certification stage,
but it now permits any candidate that survives the earlier controlled method
comparison. Threshold changes must be justified and versioned before the runs
they assess.

## Important unresolved choice

The intended production scope of `B` is not yet fixed: identity/diagonal noise
and arbitrary full `3 x 3` noise favour different challengers. Do not silently
assume one scope when selecting a method; establish it from the task or record
the branch-specific assumption.

## Canonical evidence

- Human-readable decision: `METHOD_SELECTION_REPORT.md`
- Machine-readable decision: `method_selection_report.json`
- Method definition: `NUMERICAL_METHOD.md`
- Positivity scope: `POSITIVITY_AUDIT.md`
