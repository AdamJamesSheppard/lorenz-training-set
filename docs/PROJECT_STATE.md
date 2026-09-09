# Project state

Updated: 2026-09-09

## Objective

Develop and validate a conservative, positivity-preserving numerical forecast
operator for the stochastic Lorenz-63 Fokker--Planck equation, then use only a
certified configuration to generate neural-operator training pairs.

## Current decision

- Method-selection classification: `INSUFFICIENT_EVIDENCE`.
- Large neural-operator dataset generation: `NO`.
- Strongest tested interim baseline: Q1 DG, upwind advection, SIPG diffusion,
  backward Euler, quadrature-14 L2 initialization and projected Bayesian
  analysis, followed by the conservative two-stage positivity limiter.
- This is an interim baseline, not a certified production method.

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

## Next decision experiment

Use the experiment specification in `experiments/mature-state-decision.yaml`.
Retain Q1 only if covariance, limiter, temporal, boundary, and converged-reference
gates all pass. Do not weaken the gates after seeing the outcome.

## Canonical evidence

- Human-readable decision: `METHOD_SELECTION_REPORT.md`
- Machine-readable decision: `method_selection_report.json`
- Method definition: `NUMERICAL_METHOD.md`
- Positivity scope: `POSITIVITY_AUDIT.md`

