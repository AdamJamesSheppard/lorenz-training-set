# Project state

Updated: 2026-09-15

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
METHOD_STATUS = MATURE_STATE_STATISTICAL_AND_POSITIVITY_GATES_PASSED
MATURE_DENSITY_CONVERGENCE = OPEN
MATURE_GRADED_EFFICIENCY = SUPPORTED_NOT_CERTIFIED
PRODUCTION_DATASET_AUTHORIZED = false
NEXT_REQUIRED_GATE = MATURE_DENSITY_CONVERGENCE
```

- Method-selection classification: `MATURE_STATE_STATISTICAL_AND_POSITIVITY_GATES_PASSED`.
- Next required gate: `MATURE_DENSITY_CONVERGENCE`.
- Large neural-operator dataset generation: `NO`.
- Controlled baseline: Q1 DG, upwind advection, SIPG diffusion, backward
  Euler, quadrature-14 L2 initialization and projected Bayesian analysis,
  followed by the conservative two-stage positivity limiter.
- Strongest observed numerical trajectory: unlimited same-mesh Q2 with
  Crank--Nicolson. It passes the controlled timestep gates but is not an
  admissible density because it contains genuine negative mass.
- Leading admissible candidate: Q2 Crank--Nicolson with Stage-1 average repair
  and local QP. It passes the startup-state temporal/positivity, identity-noise
  spatial, full-SPD spatial, and mature-state positivity/statistical gates.
  Uniform-60 and its static graded reproduction both satisfy the original
  mature mean-correction limit of `0.001`. Production certification still
  requires mature full-density convergence and domain sensitivity.
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
- The first mature bimodal full-SPD hierarchy completes but fails its
  predeclared scientific decision. All invariant, covariance, marginal,
  joint-density, lobe-probability and convergence gates pass. Mean relative L1
  corrections decrease `0.003047 -> 0.002789 -> 0.001840`, but every value
  exceeds the fixed `0.001` gate. Common-grid differences decrease only
  `0.42059 -> 0.35373`, with observed rate `0.42695`.
- The later uniform `60x72x72` mature run passes the original `0.001` mean
  correction gate at `0.0008313`, together with every positivity, conservation,
  optimizer, covariance, marginal, joint-TV and lobe test. Its 8.40 million DG
  unknowns require about 69.4 minutes and 6.05 GiB peak memory per rank.
- Static `44x52x46` grading reproduces uniform-60 to common-grid `L1=0.001688`
  while reducing DG unknowns by `66.2%`, runtime by `53.0%`, and peak memory per
  rank by `61.7%`. It formally misses its separate `0.0008` correction target
  at `0.0008384`; this failure remains recorded. Matched-grid recomputation
  shows the automated marginal-degradation failure was a bin-resolution
  comparison artifact.
- The completed `58x68x56` fine graded run reduces mean correction from
  uniform-60's `8.31e-4` to `1.13e-4` and affected probability from `0.428`
  to `0.00418`, with zero negativity, optimizer failure or fallback. Its
  common-grid differences are `D_60,gf=0.108680` and `D_g,gf=0.107936`.
  Runtime is `76.4` minutes, `10.1%` above uniform-60, despite using `29.0%`
  fewer DG unknowns; mature-density convergence and solver efficiency remain
  open.
- The corrected MFEM physical-basis diagnostic passes on `4x5x5` for four
  deterministic Q2 fields. Maximum conservative-export discrepancies are
  `2.55e-16` for input representation, `4.95e-15` for the full operator,
  `2.43e-15` for raw CN and `7.81e-12` for the QP-corrected step. The active-QP
  field invokes all 100 cell optimizations without fallback. The earlier MFEM
  production probe is superseded because its Cartesian constructor produced
  the wrong x extent and its diffusion/CN signs did not match the incumbent.

## Active blockers

1. Mature positivity and low-dimensional statistics pass at uniform-60 and
   graded resolution, but full-density spatial convergence remains unresolved:
   the preceding `45 -> 60` common-grid difference is `0.20997`.
2. The operational repeated-analysis posterior family remains unvalidated near
   production resolution; the present mature law is one analytic conditioned
   bimodal test.
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
7. Finite-domain sensitivity remains unvalidated for the leading candidate.
8. A converged independent deterministic full-density reference remains absent.

## Near-term research portfolio

The living plan is in `docs/RESEARCH_DIRECTIONS.md` and
`experiments/method-selection-research.yaml`. Current high-value branches are:

1. The MFEM physical Q2/operator/raw-CN/local-QP gate now passes on the
   `30x36x36` production mesh. Implement and run the frozen uniform mature
   equivalence forecast before enabling nonconforming AMR.
2. Use the completed eleven-snapshot replay only after mass, cell-average,
   density, moment and correction comparisons against DOLFINx pass.
3. Run a fixed nonconforming octree mesh with `D_AMR,gf < 0.05`, mean correction
   below `8e-4`, all existing statistical/invariant gates and a material resource
   advantage over equivalent uniform resolution.
5. Do not spend another hierarchy on deeper Bernstein certification; witnessed
   polynomial negativity, rather than unresolved bounds, dominates every saved
   mature snapshot.
6. Develop a dynamically scaled whole-space Hermite solver as an independent
   high-order reference after the Q2 gate.
7. Investigate covariance-targeted goal-oriented/nonuniform resolution and a
   genuinely high-order independent deterministic reference.
7. Regenerate and test mature DA states only after the initialization,
   analysis, and positivity path used to produce them is acceptable.

`experiments/mature-state-decision.yaml` is executable and frozen for the first,
ambiguous bimodal mature-state hierarchy. Threshold changes must be justified
and versioned before the runs they assess.

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
