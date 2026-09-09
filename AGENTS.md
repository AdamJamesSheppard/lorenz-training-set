# Agent entry point

## Purpose

Research code for reliable Lorenz-63 Fokker--Planck forecasts, Bayesian data
assimilation, and conservative dataset generation with DOLFINx.

## Read first

- `docs/PROJECT_STATE.md`
- `docs/MATH_PROTOCOL.md`
- `docs/MATHEMATICAL_SPEC.md`
- `docs/ARCHITECTURE.md`
- `METHOD_SELECTION_REPORT.md` for the current numerical decision

Read deeper documentation only when it is relevant to the task.

## Standard commands

- Bootstrap/update environment: `./scripts/bootstrap`
- Compact context: `./scripts/context`
- Routine health: `./scripts/check`
- Scientific invariants: `./scripts/verify-math`
- Repository map: `./scripts/repo-map`
- Configured run: `./scripts/run-experiment experiments/<name>.yaml`

## Scientific rules

- Numerical evidence is not a proof or a production certification.
- State assumptions, domains, norms, discretization, and tolerances.
- Do not silently change boundary conditions, fluxes, polynomial degree,
  limiter, quadrature, observation model, or parameterization.
- Use the evidence labels in `docs/CLAIMS.md`.
- Cite assumption IDs from `docs/assumptions.yaml` when they matter.
- Do not claim novelty without a literature search.
- The current method status is `INSUFFICIENT_EVIDENCE`; do not generate a
  large training dataset unless the predeclared decision gates pass and the
  project state is explicitly updated.

## Modification rules

- Inspect `git status` and `git diff` before and after edits.
- Preserve raw data and immutable run records.
- Make the smallest change that satisfies the task.
- Add a regression test for numerical or software bug fixes when feasible.
- Run targeted checks during development and the relevant authoritative check
  before concluding.

## Output rule

For technical tasks report the result, evidence, validation run, and remaining
uncertainty.
