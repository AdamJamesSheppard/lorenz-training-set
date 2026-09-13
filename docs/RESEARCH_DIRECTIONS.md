# Research directions

Updated: 2026-09-13

This is a living portfolio, not a queue that must be executed in order. Agents
are welcome to add, remove, split, merge, or re-rank branches as the production
scope, literature, implementation evidence, or computational resources change.
Record why a branch moved; do not preserve a stale ranking for consistency.

## Current diagnosis

The corrected same-mesh evidence shows that Q2 improves covariance and
marginals over Q1. Unlimited Crank--Nicolson Q2 then passes the controlled
density and covariance timestep gates, but carries genuine negative mass.
Applying the current adaptive global correction removes negativity while
increasing the timestep density discrepancy from `4.19e-5` to `0.01088` and
the full-step covariance discrepancy from `0.00371` to `0.02192`. This causal
attribution is `NUMERICAL`, not a theorem. The central problem is now local
positivity enforcement that preserves substantially more of the accurate
unlimited trajectory.

The local-QP isolation and optimizer gates passed. The subsequent tight
full/half/quarter/eighth run is fully positive with covariance error near
`0.0075`; its final density difference falls from `5.418e-4` to `1.620e-4`,
giving observed order `1.741`. All 1,200 steps pass the predeclared positivity,
mass, optimizer and density gates. The candidate is now frozen for a
constant-ratio spatial study. That identity-noise hierarchy also passed, with
common-grid density differences `0.141394` and `0.0355845` and observed rate
`3.4026`. This rate remains numerical evidence rather than a formal-order proof.
The immediate gate is the predeclared full-SPD control and spatial hierarchy.

## Active branches

| Branch | Why it matters now | Switch/stop evidence |
|---|---|---|
| Local minimum-change Q2 projection | It passed the tight temporal/positivity study and identity-noise spatial hierarchy, so it is the leading admissible candidate. | Run the predeclared full-SPD control, then the conditional `20x24x24 -> 30x36x36 -> 45x54x54` full-SPD hierarchy; passing advances to mature-state tests. |
| Positive low-order full-SPD operator | Supplies the invariant-domain baseline required by defensible local convex/AFC correction. | Must preserve mass, positivity and no-flux boundaries for 3-D Lorenz drift plus full SPD diffusion before antidiffusive fluxes are introduced. |
| Adaptive Q2 Bernstein diagnosis | Separates a sufficient positivity certificate from witnessed negativity and unresolved near-zero cases. | Use as a diagnostic; reject it as a production decision procedure if unresolved cells dominate or correction remains intrusive. |
| Adaptive local-QP constraints | May remove unnecessary fixed-Bernstein restrictions while retaining the minimum-change architecture. | Hold while the frozen fixed-constraint candidate undergoes spatial and generalization tests; revive if those diagnostics attribute failure to excessive correction. |
| Local AFC/convex high-order DG | Limits conservative antidiffusive fluxes locally instead of scaling a completed polynomial globally. | Unlimited CN passed and global correction failed; begin from a validated positive low-order full-SPD update if the remaining post-step tests fail. |
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
