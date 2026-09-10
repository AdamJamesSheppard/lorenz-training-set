# Decision log

Decisions here are dated and revisable. Add a new entry that marks an older
decision `superseded`, `narrowed`, or `confirmed` rather than rewriting history
to make the current direction look inevitable.

## 2026-09-10 - Implement the predeclared Q2 diagnostic without relaxing positivity

The same-mesh experiment now has fixed and adaptive Bernstein branches. The
adaptive branch skips scaling only for cells certified non-negative after exact
de Casteljau subdivision; witnessed-negative and depth-limited unresolved cells
retain the fixed `2x2x2` conservative scaling. Raw Q2 coefficients before every
correction, final per-cell classifications, correction norms, negative-mass
quadrature estimates, time and memory are retained in immutable runs. This is
an experimental comparator and does not change the production classification.

## 2026-09-10 - Gate the next implementation on a same-mesh Q2 falsification

The existing Q1/Q2 comparison is insufficient to rank polynomial degree because
it held total DOFs fixed while Q2 used 1.5-times-wider cells in every direction
and twice the timestep. Before implementing a new solver family, compare Q1 and
Q2 on the same `30x36x36` mesh and `dt=0.000625`, starting from the same positive
represented Q1 law embedded exactly in Q2. Audit raw Q2 polynomials before
correction and separate cell-average from high-order changes.

Adaptive Bernstein subdivision is authorized for this diagnostic as a rigorous
sufficient certificate. It is not selected as a complete production positivity
test because negative coefficients are inconclusive and non-negative polynomials
with zeros may remain uncertified under arbitrary subdivision.

If raw Q2 is accurate but correction fails, the next architecture is local
conservative flux correction/AFC. If raw Q2 fails, close that branch and test a
positive full-tensor finite-volume/flux method. Detailed gates are predeclared in
`METHOD_SELECTION_REPORT.md`.

## 2026-09-10 - Require general full-SPD production diffusion

The production target must ultimately support a constant general `3 x 3` noise
matrix and therefore mixed derivatives in full SPD `D=BB^T/2`. This supersedes
the unresolved production-scope part of the 2026-09-09 challenger-priority
decision. Identity noise remains the controlled experiment. Directional FCDF,
Chang--Cooper and complete-flux variants remain valid special-case challengers,
but diagonal-only theory cannot certify the general production role.

## 2026-09-10 - Assign solver roles separately

No production reference solver is certified. Q1 remains the baseline. A
dynamically scaled whole-space Hermite-Galerkin method is the preferred future
independent deterministic reference because it changes both discretization and
boundary treatment; it must be validated by spectral and moment convergence and
is not presumed positive.

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
