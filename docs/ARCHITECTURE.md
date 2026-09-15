# Architecture

This is a living description of the current repository, not a prohibition on
new layouts or method families. Agents are welcome to refactor it and add
parallel implementations when that makes controlled comparisons clearer. Keep
the dependency direction, public entry points, tests, and this document aligned
with the code actually present.

## Scientific core

- `lorenz_fpe/core.py`: Lorenz model, DG solver, positivity limiter,
  diagnostics, observations, Bayesian update, truth simulation, and state I/O.
- `lorenz_fpe/finite_volume.py`: independent conservative finite-volume
  reference implementation.
- `lorenz_fpe/dataset.py`: sequential DA trajectories, quality gates,
  conservative export, manifests, and leakage-safe splits.
- `lorenz_fpe/validation.py`: analytic, Monte Carlo, convergence, domain, and
  independent-reference studies.
- `lorenz_fpe/local_projection.py`: experimental cell-local mass-matrix QP and
  an opt-in Q2 solver that feeds Stage-1-plus-QP states into propagation. The
  fixed equality is eliminated once; OSQP reuses the reduced matrices while
  SLSQP remains an oracle backend. The default solver remains unchanged.

Dependency direction is `entry points -> lorenz_fpe package`; the scientific
core currently does not import top-level entry-point scripts. If a broader
plugin/strategy architecture becomes useful, document and test the replacement
rather than preserving this shape for its own sake.

## Candidate implementations

New method families should normally live beside the incumbent rather than
being hidden behind unrelated conditionals in `core.py`. Shared model,
diagnostic, reference, and dataset contracts should be factored only when they
are genuinely method-independent. Candidate modules may include high-order
DG/AFC, adaptive certification, characteristic or semi-Lagrangian solvers,
complete-flux/FCDF approaches, and spectral/reference solvers.

Every candidate should expose enough common configuration and diagnostics for
same-law, same-domain, same-time, and accuracy/cost comparisons. Method-specific
diagnostics are encouraged; a common interface must not erase important
differences.

## Entry points

- `solver.py`: one forecast.
- `generate_dataset.py`: gated sequential DA dataset generation.
- `validate.py` and focused `*_study.py` files: validation studies.
- `same_mesh_q2_study.py`: common-law Monte Carlo preparation and auditable
  Q1/Q2 fixed/adaptive forecast branches, including raw coefficient archives
  and optional sparse cellwise indicator snapshots.
- `mature_time_aggregated_pipeline.py`: deterministic fine-trajectory replay,
  maximum-over-time indicator aggregation, bounded graded-axis construction and
  automatic dispatch of the third mature-density level.
- `local_projection_study.py`: compares terminal unlimited Q2 states with the
  incumbent correction, a strictly cell-local QP, and Stage-1 average repair
  followed by the local QP.
- `local_projection_optimizer_study.py`: replays saved and randomized Q2 cell
  problems through OSQP and the SLSQP oracle, checking feasibility, objective,
  coefficient agreement, and speed.
- `scripts/run-experiment`: immutable config-driven runs under `runs/`.

## Evidence and state

- `docs/`: current research state, definitions, claims, decisions, references.
- Root `*_REPORT.md` and JSON files: preserved historical and method-selection
  evidence.
- `experiments/`: versioned run specifications.
- `runs/<experiment-id>/<UTC timestamp>/`: immutable generated run records,
  ignored by Git; repeating a config creates a new instance.
- `results/`: generated compact summaries and invariant reports, ignored by Git.
- `sample_dataset/`: audit sample; arrays/checkpoints remain local while
  schemas, manifests, and diagnostics are versioned.

## Validation flow

`scripts/context` gives bounded orientation. `scripts/check` performs routine
health checks. `scripts/verify-math` runs focused scientific invariant tests and
writes a machine-readable summary. Expensive decision studies are run from an
experiment specification and are not hidden inside the routine check.
