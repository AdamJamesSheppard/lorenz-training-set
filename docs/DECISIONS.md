# Decision log

## 2026-09-09 - Dataset generation remains blocked

Classification is `INSUFFICIENT_EVIDENCE`; do not scale up dataset generation.
The short-time covariance discrepancy remains substantially above Monte Carlo
sampling uncertainty, and mature-state validation is missing.

## 2026-09-09 - Preserve Q1 as the interim baseline

Use Q1 upwind/SIPG, backward Euler, quadrature-14 L2 initialization, projected
Bayesian analysis, and the conservative limiter for further controlled tests.
This is a comparison baseline, not a production endorsement.

## 2026-09-09 - Do not reject higher order on the existing Q2 result

The current Q2 result tests a particular fixed-subcell Bernstein certificate
and scaling strategy. That positivity treatment can erase the moment advantage
of the unlimited Q2 projection; it does not establish that Q2 itself is worse.

## 2026-09-09 - Use micromamba rather than uv for the numerical runtime

DOLFINx, PETSc, MPI, and their compiled ABI-compatible dependencies are already
provided by the conda-forge `pde` environment. `environment.yml` pins the direct
runtime and verification tools, while `environment-linux-64.lock` records exact
artifacts for this platform. This adapts the guides' deterministic-environment
requirement to the compiled FEniCSx stack.

