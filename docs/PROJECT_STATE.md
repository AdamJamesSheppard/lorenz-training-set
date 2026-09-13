# Project state

Updated: 2026-09-13

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

```ini
METHOD_STATUS = FULL_SPD_DIFFUSION_CERTIFIED
PRODUCTION_DATASET_AUTHORIZED = false
NEXT_REQUIRED_GATE = MATURE_STATE
```

- Method-selection classification: `FULL_SPD_DIFFUSION_CERTIFIED`.
- Next required gate: `MATURE_STATE`.
- Large neural-operator dataset generation: `NO`.
- Controlled baseline: Q1 DG, upwind advection, SIPG diffusion, backward
  Euler, quadrature-14 L2 initialization and projected Bayesian analysis,
  followed by the conservative two-stage positivity limiter.
- Strongest observed numerical trajectory: unlimited same-mesh Q2 with
  Crank--Nicolson. It passes the controlled timestep gates but is not an
  admissible density because it contains genuine negative mass.
- Leading admissible candidate: same-mesh Q2 Crank--Nicolson with Stage-1
  average repair and local QP. The tight four-level startup-state diagnostic
  passes every predeclared temporal, positivity, mass and identity-noise spatial
  gate. The subsequent non-diagonal full-SPD hierarchy also passes. Production
  certification still requires mature-state and domain tests.
- The corrected production-scale run reproduces the earlier Q2 accuracy and
  timestep results while satisfying cell-average and scaling-factor invariants.
  Adaptive Q2 passes its full-step branch gates but fails the half-step mass
  and cross-timestep density gates.
- The tight full/half/quarter/eighth diagnostic has density differences
  `5.238e-4`, `5.418e-4`, and `1.620e-4`. The final ratio gives observed order
  `1.741`; all 1,200 timesteps are whole-cell Bernstein-certified with zero
  measured negative mass, optimizer failure or fallback. Absolute mass errors
  are at most `1.87e-11`. This advanced the candidate to spatial refinement,
  while one fine-level order estimate does not prove asymptotic second order.
- The completed `20x24x24 -> 30x36x36 -> 45x54x54` identity-noise hierarchy
  has common-grid L1 differences `0.141394` and `0.0355845`, giving observed
  rate `3.4026`. All 960 steps are whole-cell certified with zero measured
  negative mass, optimizer failure or fallback. This is an observed common-grid
  rate rather than a proved formal order.

## Latest validated evidence

- Historical Q1 short-time same-initial-law covariance error: `0.0855765`;
  the matched controlled Q1 run gives `0.08719`.
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
- Applying the current adaptive global limiter to Crank--Nicolson increases the
  timestep density difference to `L1>=0.01088` and gives full-step mass error
  `1.27e-10`; that correction architecture is rejected for production Q2.
- With tighter KSP tolerances and an eighth-timestep level, repeated local-QP
  correction passes all predeclared dynamic gates. Covariance errors remain
  between `0.007488` and `0.007519`; the quarter/eighth density difference is
  `1.620e-4`, and the corresponding observed order is `1.741`.
- Identity-noise spatial refinement passes every predeclared gate. Covariance
  discrepancies decrease from `0.03033` to `0.005209` to `0.002340`; the
  finest value lies below the 200,000-path bootstrap p95 `0.006491`, so further
  covariance improvement is unresolved by that reference. The deterministic
  common-grid density differences remain the primary convergence evidence.
- The controlled `30x36x36` full-SPD run passes every predeclared gate:
  covariance discrepancy `0.004163`, maximum off-diagonal covariance error
  `0.003806`, mean correction `7.61e-5`, zero measured negative mass, zero
  optimizer failure/fallback and absolute mass error `3.86e-12`. This authorizes
  the already-predeclared full-SPD spatial hierarchy.
- The complete full-SPD hierarchy passes every predeclared gate. Common-grid L1
  differences decrease from `0.139500` to `0.0348401`, giving observed rate
  `3.4215`. Covariance discrepancies are `0.02879`, `0.004163`, and `0.002261`;
  off-diagonal covariance and correlation errors remain within their fixed
  limits. All 960 steps are certified with zero measured negative mass,
  optimizer failure or fallback.

## Active blockers

1. No corrected mature-posterior forecast is validated near production
   resolution.
2. The certified startup-state/full-SPD result has not been tested on mature,
   filamented or post-analysis densities.
3. The independent finite-volume hierarchy is not converged enough to define a
   full-density truth error.
4. The identity-noise spatial hierarchy passed, but its observed rate `3.4026`
   is not a theorem or proof of an asymptotic formal order.
5. In the terminal unlimited CN states, about 17,500 of 38,880 cells have
   negative averages. Their total negative average mass is only about
   `4.34e-6`, but a mass-preserving cell-local polynomial projection is
   mathematically infeasible in each such cell.
6. The reduced fixed-matrix OSQP backend passed a 2,413-problem SLSQP comparison
   and a 10x projection-speed gate. Optimizer cost and startup-state temporal
   positivity are no longer the active blockers.
7. Mature corrected states and finite-domain sensitivity remain unvalidated for
   the leading candidate.
8. A converged independent deterministic full-density reference remains absent.

## Near-term research portfolio

The living plan is in `docs/RESEARCH_DIRECTIONS.md` and
`experiments/method-selection-research.yaml`. Current high-value branches are:

1. Update `experiments/mature-state-decision.yaml` for the certified local-QP
   Q2--Crank--Nicolson full-SPD candidate and freeze its gates before execution.
2. Project one common later-time or post-analysis density conservatively onto
   every mesh, including Bayesian analysis when such posteriors are dataset
   inputs.
3. Record temporal/spatial density differences, covariance and marginal TVs,
   correction L1/L2, negative-average and projected probability mass, projected
   cell count, optimizer performance and conservation.
4. After a mature-state pass, run aligned-box domain-size sensitivity at
   approximately fixed physical resolution.
5. If one of these gates fails, diagnose adaptive constraints or an
   operator-level positive low-order/AFC correction against the frozen local-QP
   comparator.
6. Develop a dynamically scaled whole-space Hermite solver as an independent
   high-order reference after the Q2 gate.
7. Investigate covariance-targeted goal-oriented/nonuniform resolution and a
   genuinely high-order independent deterministic reference.
8. Regenerate and test mature DA states only after the initialization,
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
