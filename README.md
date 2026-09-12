# Positivity-limited Lorenz-63 Fokker--Planck solver

This is a living numerical-research repository. The current DOLFINx Q1 solver
is an evidence-preserving baseline, not a restriction on future work. New
agents and contributors are welcome to revise any version-controlled code,
documentation, experiment, or architecture when a better-supported direction
emerges; see `AGENTS.md` and `docs/RESEARCH_DIRECTIONS.md` for the maintenance
and comparison policy.

> **Current method-selection status (2026-09-12): `INSUFFICIENT_EVIDENCE`.**
> Do not generate a large training dataset. The authoritative corrected
> evidence is [METHOD_SELECTION_REPORT.md](METHOD_SELECTION_REPORT.md).
> Older readiness files and the sample dataset remain as audit history.
> Q1 is the controlled baseline. Unlimited Q2--Crank--Nicolson is the most
> accurate observed trajectory but contains genuine negative mass; adaptive
> global correction restores non-negativity while failing the density timestep
> gate. An offline Stage-1-plus-local-QP correction is substantially less
> intrusive in the terminal-state test. The completed in-loop three-timestep
> diagnostic remains positive and accurate, but fails its positive observed
> timestep-order gate and two absolute mass gates. A controlled tight-solve
> eighth-timestep diagnostic is predeclared before choosing between adaptive
> local-QP constraints and an operator-level full-SPD local-flux/AFC method.

This project implements the forecast step of a continuous-discrete Bayesian
filter for the stochastic Lorenz-63 model.  It uses modern DOLFINx 0.11, UFL,
PETSc, and MPI.  The numerical state remains a full DG probability density
through every forecast and Bayesian update; it is never replaced by a Gaussian.

## What is implemented

- `FokkerPlanckSolver`: experimental DG/Q1--Q3, conservative upwind advection, full-tensor
  SIPG diffusion, theta-method time integration, one reusable matrix, and independently
  recomputed PETSc residuals.
- `PositivityLimiter`: the two-stage optimisation/scaling method described by
  Liu, Hu, Taitano, and Zhang (2025).  It first finds the nearest non-negative
  cell-average field with exactly the same global mass, then scales the higher
  modes about each corrected average.
- `LocalProjectionFokkerPlanckSolver`: experimental Q2 Crank--Nicolson followed
  by conservative average repair and a cell-local mass-matrix QP. Its reduced
  OSQP backend reuses fixed matrices and retains SLSQP as a validation oracle.
- Reflecting total-flux boundary condition
  `(f p - D grad(p)).n = 0`.  This is explicitly a bounded-domain
  approximation to the whole-space SDE.
- Arbitrary native DG input, lossless native save/reload, analytic bootstrap
  densities, Gaussian mixtures for testing, and conservative structured
  reconstruction.
- Stochastic truth simulation, full/x/xz observation operators, projected
  Gaussian-likelihood analysis, repeated DA cycles, and direct use
  of one posterior as the next forecast input.
- Conservative voxel-average export, quality-gated manifests, and splits by
  complete independent trajectory.
- Analytic diffusion/advection-diffusion tests, non-Gaussian propagation,
  convergence tooling, domain sensitivity, and independent Monte Carlo checks.

## Environment and commands

The compiled FEniCSx/PETSc/MPI stack is pinned in `environment.yml`; exact
Linux package artifacts are recorded in `environment-linux-64.lock`. From this
directory, bootstrap or update the environment once:

```bash
./scripts/bootstrap
```

Use the repository-owned entry points for routine work:

```bash
./scripts/context
./scripts/check
./scripts/verify-math
./scripts/run-experiment experiments/smoke-forecast.yaml
```

For a direct forecast:

```bash
./scripts/run-in-env python solver.py --cells 30 36 36 --dt 0.000625 --t-final 0.25
```

MPI forecast:

```bash
./scripts/run-in-env mpirun -n 8 python solver.py --cells 30 36 36 --dt 0.000625 --t-final 0.25
```

The following is an **exploratory** DA command, not an approved production
dataset command.  The current accuracy closure is `INSUFFICIENT_EVIDENCE`, so do not scale
this up until a finer solver configuration passes the configuration-level
covariance and limiter gates:

```bash
./scripts/run-in-env python generate_dataset.py \
  --output dataset_root \
  --trajectories 20 --cycles 30 --burn-in 10 \
  --observation xz --obs-variance 4 \
  --obs-interval 0.05 --cells 30 36 36 --dt 0.000625
```

Run validation and tests:

```bash
./scripts/check
./scripts/run-in-env python validate.py --output validation_report.json
```

The coarse defaults are for development, not a claim of production accuracy.
See [METHOD_SELECTION_REPORT.md](METHOD_SELECTION_REPORT.md) for the current quantitative
error budget, cost model, and the criteria that must pass before generation.

## Dataset semantics

Each accepted sample is exactly

```text
(posterior.npy = p_k|k, forecast_interval) -> (forecast.npy = p_k+1|k)
```

The files are conservative subcell-average tensors with axes `(x,y,z)` and two
subcells per native cell axis by default.  For affine Q1 this supplies eight
independent averages per cell, so a solver-exported tensor reconstructs the
native polynomial to roundoff; one value per cell preserves mass but discards
the slopes.  Native DG checkpoints are stored alongside the tensors.
`training_samples` in the manifest
contains only post-burn-in cycles that pass mass, positivity, boundary,
projection, and linear-solver gates.  `all_cycle_records` retains burn-in and
failed records for auditability.  Splits name complete trajectory IDs; adjacent
cycles are never randomly divided across train, validation, and test.

Canonical tensors are stored as float64 so the FEM mass identity is retained.
Any float32 conversion for training should be treated as an explicit derived
dataset and have its own mass-error check.

The dataset generator varies truth initial states, process and observation
noise realisations, observation values, prior means, and prior covariance.
Observation operator and covariance are configuration variables.  Lorenz and
process-noise parameters are fixed unless explicitly supplied, keeping the
fixed-model and parameterised-operator research questions separate.

## Probability and numerical guarantees

After every completed timestep:

- the constrained optimisation preserves the unlimited DG solution's global
  mass to its solve tolerance;
- corrected cell averages are non-negative;
- the Q1 vertex Bernstein coefficients, or Q2/Q3 Bernstein coefficients on
  limiter control subcells, are non-negative;
- because each Bernstein basis is non-negative and sums to one, the complete
  limited polynomial is non-negative in every affine cell.

Tiny values around `-1e-20` in diagnostics are floating-point roundoff, not a
resolved negative lobe.  `negative_mass` is separately integrated.  The claim
does not apply to the unlimited backward-Euler solve, curved cells, or
arbitrary interpolation tensors. Higher-order control is sufficient but can
be substantially more restrictive than positivity itself. The limiter is a
conservative constrained optimisation, not pointwise clipping followed by
renormalisation.  No CFL restriction is required for the post-processing
property; accuracy and limiter activity still impose practical resolution
requirements.

See [NUMERICAL_METHOD.md](NUMERICAL_METHOD.md) for equations, assumptions, and
limitations.

## Archived validation snapshot (2026-09-08; superseded)

The following numbers predate the common-initial-law and projected-analysis
repairs. They explain the earlier decision but are not current evidence.

- The complete unit, invariant, checkpoint, no-Gaussianisation, and two-rank
  MPI suite passes in the `pde` environment.
- Analytic constant advection-diffusion coupled refinement from 6 to 8 to 10
  cells per axis reduces L1 error from `0.640` to `0.470` to `0.366`.
- Against 100,000 Euler--Maruyama paths at `t=0.05`, the
  `30x36x36`, `dt=0.000625` mean error is
  `(-0.00233,-0.00719,0.01361)`.  Normalized covariance error is `0.2193`,
  versus a bootstrap 95% Monte Carlo noise floor of `0.00874` (25.1 times
  larger).
- At fixed `dt=0.000625`, refinement from `20x24x24` to `30x36x36` reduces
  normalized covariance error from `0.6108` to `0.2193`.  A common-noise MC
  timestep check changes normalized covariance by only `0.00022`, identifying
  spatial discretisation and limiting—not SDE reference timestepping—as the
  dominant problem.
- On the finer run, limiting acts on all 80 steps; mean relative L1 correction
  is `0.00287`, the maximum is `0.00549`, and roughly 45% of raw cell averages
  are negative.  Mature coarse DA forecasts have 17--32% normalized covariance
  errors, 14--24 times their MC noise floors, with 4.7--6.6% mean limiter
  corrections.
- Re-auditing the sample dataset with the evidence-based limiter gate rejects
  all 24 cycles; `training_samples` is intentionally empty.

The archived classification was **`NOT_READY`**. Conservation, positivity, and
linear-solver accuracy are strong, but the forecast densities are still too
diffusive to serve as trusted neural-operator ground truth.

## Files

- `lorenz_fpe/core.py`: model, DG solver, limiter, diagnostics, observations,
  Bayesian update, truth simulator, native and structured density paths.
- `lorenz_fpe/dataset.py`: DA trajectories, burn-in, quality gates, manifests,
  trajectory splits, and mature-posterior summary.
- `lorenz_fpe/validation.py`: analytic, non-Gaussian, Monte Carlo, convergence,
  and domain tests.
- `solver.py`, `generate_dataset.py`, `validate.py`: command-line entry points.
- `tests/`: unit and end-to-end invariant tests.
- `POSITIVITY_AUDIT.md`: paper-to-code hypothesis and guarantee audit.
- `PRODUCTION_READINESS.md`: error budget, mature-DA evidence, scaling, cost,
  and the go/no-go decision.

## Primary numerical reference

Chen Liu, Jingwei Hu, William T. Taitano, and Xiangxiong Zhang,
“An optimization-based positivity-preserving limiter in semi-implicit
discontinuous Galerkin schemes solving Fokker--Planck equations,” *Computers &
Mathematics with Applications* 192 (2025), 54--71,
<https://doi.org/10.1016/j.camwa.2025.05.008>.
