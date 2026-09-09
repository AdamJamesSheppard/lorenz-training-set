# Decision log

Decisions here are dated and revisable. Add a new entry that marks an older
decision `superseded`, `narrowed`, or `confirmed` rather than rewriting history
to make the current direction look inevitable.

## 2026-09-09 - Keep the scaffold and method selection deliberately open

All version-controlled code and living documents may be edited when evidence
or a task makes them stale. Q1 DG remains a controlled comparator, not the
project's mandated destination. Future work should maintain competing method
hypotheses and may introduce repaired Q2/AFC, adaptive certification,
complete-flux/FCDF, characteristic, goal-oriented, spectral, Monte Carlo, or
hybrid approaches. Scientific integrity, raw-data preservation, and provenance
remain durable safeguards; implementation restrictions and rankings do not.

## 2026-09-09 - Dataset generation remains blocked

Classification is `INSUFFICIENT_EVIDENCE`; do not scale up dataset generation.
The short-time covariance discrepancy remains substantially above Monte Carlo
sampling uncertainty, and mature-state validation is missing.

## 2026-09-09 - Preserve Q1 as the interim comparator

Use Q1 upwind/SIPG, backward Euler, quadrature-14 L2 initialization, projected
Bayesian analysis, and the conservative limiter for further controlled tests.
This is a comparison baseline, not a production endorsement.

Status: active for comparison, explicitly non-exclusive.

## 2026-09-09 - Do not reject higher order on the existing Q2 result

The current Q2 result tests a particular fixed-subcell Bernstein certificate
and scaling strategy. That positivity treatment can erase the moment advantage
of the unlimited Q2 projection; it does not establish that Q2 itself is worse.

The next Q2 branch should first distinguish failed positivity certification
from genuine negativity, then compare less intrusive corrections on equal
physical meshes.

## 2026-09-09 - Challenger priority depends on the production noise model

If production `B` is identity or diagonal, directional FCDF and
Scharfetter--Gummel/complete-flux candidates become especially relevant. If
arbitrary full `B` is required, repaired high-order DG/AFC and full-tensor flux
methods receive higher priority. This scope is unresolved and must remain
branch-specific until established.

## 2026-09-09 - Use micromamba rather than uv for the numerical runtime

DOLFINx, PETSc, MPI, and their compiled ABI-compatible dependencies are already
provided by the conda-forge `pde` environment. `environment.yml` pins the direct
runtime and verification tools, while `environment-linux-64.lock` records exact
artifacts for this platform. This adapts the guides' deterministic-environment
requirement to the compiled FEniCSx stack.
