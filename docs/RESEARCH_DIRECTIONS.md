# Research directions

Updated: 2026-09-15

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
`3.4026`. The subsequent non-diagonal full-SPD hierarchy also passes, with L1
differences `0.139500` and `0.0348401` and observed rate `3.4215`. These rates
remain numerical evidence rather than formal-order proofs. The first bimodal
hierarchy failed only its fixed mean-correction gate: corrections decrease
`0.003047 -> 0.002789 -> 0.001840` but remain above `0.001`; its observed
common-grid rate is only `0.42695`.
The follow-up same-polynomial audit rejects depth-4 certificate conservatism as
the dominant cause: depth 8 rescues at most `0.0788%` of non-certified cells and
reduces L1 correction by at most `2.89%`. Almost all rejected cells have direct
negative witnesses.
Uniform-60 subsequently passes the original correction gate, and static grading
reproduces that density efficiently. A finer `58x68x56` graded level lowers mean
correction to `1.13e-4` and affected probability to `0.00418`, while moving by
`L1=0.108680` from uniform-60. The large density movement together with sharply
smaller intervention supports localized under-resolution as the leading
diagnosis. Its 76.4-minute runtime is 10.1% above uniform-60, so cell count alone
does not establish computational efficiency. An eleven-snapshot replay showed
that tensor-product bands cannot represent the sparse marked regions within
the frozen cell ceiling. A conforming `30x36x36` MFEM port now matches DOLFINx
over the full 320-step mature forecast to common-grid `L1=5.26e-11`. The active
branch is a fixed, replay-driven nonconforming-hex AMR test. This cross-framework
result does not close mature full-density convergence or domain sensitivity.

## Active branches

| Branch | Why it matters now | Switch/stop evidence |
|---|---|---|
| Local minimum-change Q2 projection | It passed temporal/positivity, identity-noise spatial and non-diagonal full-SPD spatial gates, but the first mature bimodal hierarchy failed the mean-correction gate. | Diagnose resolution versus correction architecture using the frozen failed comparator; passing a separately predeclared mature gate advances to domain sensitivity. |
| Positive low-order full-SPD operator | Supplies the invariant-domain baseline required by defensible local convex/AFC correction. | Must preserve mass, positivity and no-flux boundaries for 3-D Lorenz drift plus full SPD diffusion before antidiffusive fluxes are introduced. |
| Adaptive Q2 Bernstein diagnosis | Separates a sufficient positivity certificate from witnessed negativity and unresolved near-zero cases. | Use as a diagnostic; reject it as a production decision procedure if unresolved cells dominate or correction remains intrusive. |
| Adaptive local-QP constraints | May remove unnecessary fixed-Bernstein restrictions while retaining the minimum-change architecture. | Deprioritize: depth 8 barely changes the mature correction because witnessed negativity dominates. |
| Local AFC/convex high-order DG | Limits conservative antidiffusive fluxes locally instead of correcting a completed polynomial. | Promote: build a validated positive low-order full-SPD update and compare against the frozen mature local-QP failure. |
| Positive full-tensor finite volume | Provides an operator-level positivity fallback with substantially different numerical principles. | Prioritize if corrected/AFC Q2 fails; require genuine 3-D convection-diffusion, no-flux and high-Peclet validation. |
| FCDF or directional complete flux | Directly targets drift-diffusion flux and high-Peclet numerical diffusion. | Keep as an identity/diagonal `B` special-case branch; present FCDF proof is directional and its 2026 evidence is lower-dimensional. |
| Characteristic/semi-Lagrangian methods | Could reduce upwind transport diffusion substantially. | Require a defensible 3-D diffusion, positivity, conservation, and reflecting-boundary treatment. |
| Time-aggregated static nonconforming-hex AMR | The fine graded result shows resolution-controlled mature-density change and nearly dormant QP correction; tensor-product grading could not represent the sparse replay indicator efficiently. MFEM has passed the conforming uniform equivalence gate. | Require `D_AMR,gf<0.05`, positivity/statistical gates and a material resource advantage; keep convergence open if contraction fails. |
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
