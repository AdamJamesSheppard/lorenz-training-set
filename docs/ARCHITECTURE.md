# Architecture

## Scientific core

- `lorenz_fpe/core.py`: Lorenz model, DG solver, positivity limiter,
  diagnostics, observations, Bayesian update, truth simulation, and state I/O.
- `lorenz_fpe/finite_volume.py`: independent conservative finite-volume
  reference implementation.
- `lorenz_fpe/dataset.py`: sequential DA trajectories, quality gates,
  conservative export, manifests, and leakage-safe splits.
- `lorenz_fpe/validation.py`: analytic, Monte Carlo, convergence, domain, and
  independent-reference studies.

Dependency direction is `entry points -> lorenz_fpe package`; the scientific
core must not import top-level entry-point scripts.

## Entry points

- `solver.py`: one forecast.
- `generate_dataset.py`: gated sequential DA dataset generation.
- `validate.py` and focused `*_study.py` files: validation studies.
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
