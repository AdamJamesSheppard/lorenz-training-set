# Research directions

Updated: 2026-09-11

This is a living portfolio, not a queue that must be executed in order. Agents
are welcome to add, remove, split, merge, or re-rank branches as the production
scope, literature, implementation evidence, or computational resources change.
Record why a branch moved; do not preserve a stale ranking for consistency.

## Current diagnosis

The corrected same-mesh evidence shows that adaptive Q2 improves covariance and
marginals over Q1, while both corrected and unlimited backward-Euler Q2 remain
density-sensitive to timestep. Global positivity correction magnifies that
sensitivity and is intrusive; the unlimited failure shows temporal/spatial DG
error also matters. This attribution is `NUMERICAL`, not proved. Unlimited Q2
has strong moment accuracy but unacceptable negative mass.

## Active branches

| Branch | Why it matters now | Switch/stop evidence |
|---|---|---|
| Corrected Q2 Crank--Nicolson comparator | Tests whether the existing sufficient global limiter preserves the successful unlimited temporal result. | Retain only under the timestep, limiter-impact, mass and positivity gates; use its result to define the local-correction target. |
| Adaptive Q2 Bernstein diagnosis | Separates a sufficient positivity certificate from witnessed negativity and unresolved near-zero cases. | Use as a diagnostic; reject it as a production decision procedure if unresolved cells dominate or correction remains intrusive. |
| Local AFC/convex high-order DG | Limits conservative antidiffusive fluxes locally instead of scaling a completed polynomial globally. | Unlimited CN passed; design against the corrected-CN comparator and require full-SPD Lorenz boundary applicability. |
| Positive full-tensor finite volume | Provides an operator-level positivity fallback with substantially different numerical principles. | Prioritize if corrected/AFC Q2 fails; require genuine 3-D convection-diffusion, no-flux and high-Peclet validation. |
| FCDF or directional complete flux | Directly targets drift-diffusion flux and high-Peclet numerical diffusion. | Keep as an identity/diagonal `B` special-case branch; present FCDF proof is directional and its 2026 evidence is lower-dimensional. |
| Characteristic/semi-Lagrangian methods | Could reduce upwind transport diffusion substantially. | Require a defensible 3-D diffusion, positivity, conservation, and reflecting-boundary treatment. |
| Goal-oriented/nonuniform resolution | Mean and raw second moments are linear functionals, so covariance-oriented refinement may beat uniform grids. | Reconsider if current DOLFINx topology or estimator cost prevents a controlled implementation. |
| Dynamically scaled Hermite reference | Supplies a whole-space, high-order method independent of DG/FV and avoids reflecting truncation. | Validate by coefficient decay and moment refinement; use as a reference even if positivity prevents production use. |
| Monte Carlo plus density reconstruction | Strong independent moment reference and possible production challenger. | Compare full-density reconstruction, tails, bandwidth bias, repeatability, and cost - not moments alone. |

## Comparison principles

- Compare identical initial laws, physical parameters, domains, forecast
  intervals, and requested observables.
- Compare equal physical mesh as well as equal degrees of freedom, wall time,
  and memory; each answers a different question.
- Triangulate with Monte Carlo and a genuinely independent deterministic
  reference where possible.
- Separate initialization, analysis, propagation, space, time, boundary,
  limiter, export, and reference uncertainty.
- Do not call a discrepancy below the reference noise floor a measured solver
  error; increase reference resolution or report that it is unresolved.
- Mature post-burn-in DA states are the decisive deployment distribution, but
  regenerate them after changes to the analysis or positivity path.

## Review triggers

Review this file whenever:

- a candidate passes or fails a controlled gate;
- the intended scope of `B` is clarified;
- a literature audit changes applicability;
- a new DOLFINx or external solver capability changes feasibility;
- hardware or cost constraints change;
- mature-state evidence contradicts startup-state rankings; or
- a new idea offers a credible way to reduce the dominant error.

When reviewing, also update `docs/PROJECT_STATE.md`, `docs/CLAIMS.md`,
`docs/DECISIONS.md`, and `docs/assumptions.yaml` as needed.
