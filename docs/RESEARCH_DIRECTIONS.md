# Research directions

Updated: 2026-09-09

This is a living portfolio, not a queue that must be executed in order. Agents
are welcome to add, remove, split, merge, or re-rank branches as the production
scope, literature, implementation evidence, or computational resources change.
Record why a branch moved; do not preserve a stale ranking for consistency.

## Current diagnosis

The corrected evidence suggests that the dominant unresolved problem is the
combination of convection-dominated spatial transport and positivity
enforcement. This is `NUMERICAL`, not proved: controlled error decomposition may
revise it. Initialization and projected Bayesian analysis have improved, while
the current Q1 covariance discrepancy remains much larger than the Monte Carlo
noise floor.

## Active branches

| Branch | Why it matters now | Switch/stop evidence |
|---|---|---|
| Adaptive Q2 Bernstein diagnosis | Separates a conservative positivity certificate from genuine polynomial negativity. | Stop if deep subdivision still finds material negativity or cannot yield a rigorous/useful decision. |
| Q2 constrained/local positivity | May preserve Q2's near-exact pre-limiter first and second moments. | Switch if feasibility, stability, cost, or mature-state correction remains unacceptable. |
| Local AFC/convex high-order DG | Limits antidiffusive fluxes locally instead of scaling a completed polynomial globally. | Require Lorenz drift-diffusion and boundary applicability; reject unsupported theorem transfer. |
| FCDF or complete-flux/Scharfetter--Gummel | Directly targets drift-diffusion flux and high-Peclet numerical diffusion. | Prioritize for identity/diagonal `B`; de-prioritize if full-tensor diffusion or 3-D no-flux assumptions cannot be supported. |
| Characteristic/semi-Lagrangian methods | Could reduce upwind transport diffusion substantially. | Require a defensible 3-D diffusion, positivity, conservation, and reflecting-boundary treatment. |
| Goal-oriented/nonuniform resolution | Mean and raw second moments are linear functionals, so covariance-oriented refinement may beat uniform grids. | Reconsider if current DOLFINx topology or estimator cost prevents a controlled implementation. |
| High-order spectral/deterministic reference | Needed because the first-order FV hierarchy is not a converged truth solution. | Use as a reference even if positivity prevents production use; reject if domain/boundary mismatch dominates. |
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

