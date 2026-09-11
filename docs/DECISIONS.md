# Decision log

Decisions here are dated and revisable. Add a new entry that marks an older
decision `superseded`, `narrowed`, or `confirmed` rather than rewriting history
to make the current direction look inevitable.

## 2026-09-11 - Run a terminal-state local-QP isolation study before in-loop AFC

Implement a cell-local mass-matrix projection of Q2 coefficients onto fixed
`2x2x2` control-subcell Bernstein inequalities while preserving each feasible
cell average. Adaptive subdivision may skip raw cells already certified
non-negative, but the QP constraint matrix remains fixed during each solve.
This makes the nearest-point comparison with scalar scaling a genuine convex
quadratic program.

The final unlimited Crank--Nicolson states already show a hard limit: 17,515
full-step and 17,572 half-step cells have negative averages, with total negative
average mass `4.341e-6` and `4.344e-6`. A pure cell-local mass-preserving
projection is infeasible there. The diagnostic therefore compares (i) pure
local QP with those cells explicitly retained and flagged, and (ii) the
incumbent conservative Stage-1 average repair followed by local QP. It does not
feed corrections into later steps. Only a favourable terminal result can
justify a later in-loop experiment; material average transfer or dynamic
failure moves the project to a positive low-order flux/AFC construction.

## 2026-09-11 - Advance Stage-1 plus local QP to an in-loop diagnostic

The clean terminal-state run `20260911T114957Z` fully certifies the hybrid at
both timestep levels and measures zero negative mass. Covariance errors are
`0.0058764` and `0.0058742`; the cross-timestep density difference is
`3.943e-5`. The QP correction objective is about 17% of matched scalar scaling,
and the terminal L1 correction falls from about `0.03937` to `0.01618`.

These results justify a dynamic test while leaving production classification
unchanged. Predeclare three timestep levels so repeated-projection effects and
an observed temporal order are visible. Scalar fallback after optimizer failure
must remain explicit. If the dynamic trajectory loses the terminal advantage,
stop post-step projection development and construct the positive low-order
full-SPD flux/AFC comparator.

The in-loop implementation passes a short whole-cell certification and mass
smoke test. A production-mesh profile with one numerical-library thread per MPI
rank takes `49.6 s` for three steps; local projection time grows from `14.7 s`
to `16.3 s` as projected cells grow from 4,451 to 8,882. A prior eight-step
profile without warm starts reached 11,305 projected cells and `27.3 s` of
projection time at step eight. The full three-level experiment remains
predeclared, but generic per-cell SLSQP is too costly for a responsible
brute-force run. Preserve the mathematical problem and replace the optimizer
with a verified specialized or batched implementation before executing it.

## 2026-09-11 - Retain Q2 as a challenger but withhold production selection

Status: superseded as numerical evidence by the invariant audit below; its run
artifacts remain immutable diagnostic history.

The controlled same-mesh experiment resolves the earlier degree confound.
Adaptive-certificate Q2 reduced corrected covariance error from `0.08719` for
Q1 to `0.02377`, improved every marginal TV, and met the forecast correction
gates. Fixed-subcell Q2 reached `0.03483`; adaptive certification therefore had
a material effect rather than merely relabelling cells.

The complete gate still failed. Halving the timestep changed the conservative
three-subcell density by `L1=0.01552`, which is already a lower bound on the
polynomial L1 difference and exceeds the `0.0025` gate. The half-step mass error
was `2.56e-10`, above `1e-10`, although covariance-error change passed at
`0.00159`. Do not certify Q2 or generate production data. Before committing to
AFC, compare truly unlimited Q2 at both timesteps; the raw states recorded in a
limited trajectory still inherit all previous corrections and cannot isolate
time discretisation from accumulated limiting.

## 2026-09-11 - Repair the limiter invariant and rerun the Q2 decision

An independent audit found that the final unconstrained roundoff correction in
Stage 1 could push extremely small active cell averages below zero. In the
first adaptive-Q2 step this produced a minimum average near `-1.92e-22` and a
negative Stage-2 scaling factor. The prior numerical gate decision is therefore
superseded pending a replacement run.

The Stage-1 residual repair now contracts non-negative slacks when mass must be
removed and applies a guarded one-cell ulp repair. Stage-2 scaling is explicitly
clamped to `[0,1]`. The reported `corrected_fraction` now counts the union of
cells changed by either stage; separate Stage-1 and Stage-2 fractions are also
recorded. The replacement comparison and the truly unlimited two-timestep
diagnostic were predeclared before evaluation.

## 2026-09-11 - Retain local QP as comparator and advance operator-level correction

The reduced fixed-matrix OSQP implementation passed all predeclared engineering
gates on 2,413 saved and randomized cell problems. It solved every problem,
agreed with successful SLSQP objectives to `3.76e-10` relative, and was `12.51`
times faster. The matched three-step production-mesh projection speedup was
`10.78`. This closes optimizer cost as the immediate blocker without changing
the cell objective or positivity constraints.

The resulting three-level in-loop run does not pass its complete scientific
decision. Every one of 560 steps is whole-cell certified, has zero measured
negative mass, and uses no fallback. Covariance errors remain near `0.0075`,
and adjacent density differences `5.24e-4` and `5.42e-4` both pass the absolute
`0.0025` gate. Because the second difference is slightly larger, observed
order is `-0.0488`, failing the predeclared positive-order requirement. Full
and quarter absolute mass errors also narrowly exceed `1e-10`; per-projection
mass changes remain below `8e-15`, so accumulated linear-solve drift is the
supported attribution for those mass misses.

Do not relax the gates or advance this post-step method to dataset
certification. Retain it as the strongest current non-negative comparator and
move the leading correction branch to a positive low-order full-SPD update with
local conservative flux/AFC correction. Dataset generation remains blocked.

## 2026-09-11 - Attribute only part of Q2 timestep sensitivity to limiting

The corrected replacement run reproduced the prior branch metrics to roundoff
with all recorded scaling factors in `[0,1]` and non-negative corrected cell
averages. Its cross-timestep density lower bound remains `0.01552` and the
half-step mass error remains `2.56e-10`, so Q2 remains uncertified.

The truly unlimited backward-Euler Q2 pair also fails the density timestep gate:
its conservative subcell lower bound is `0.00541` versus the `0.0025` limit.
Global positivity correction increases the corrected discrepancy by a factor
of about `2.87`, but the unlimited failure rules out correction as the sole
cause. Unlimited Q2 has lower covariance errors (`0.00727` and `0.00464`) while
carrying integrated negative mass of `7.23e-4` and `7.73e-4`. Proceed to a
predeclared unlimited Crank--Nicolson two-timestep diagnostic; close the present
uniform-mesh DG branch if second-order time integration also fails.

## 2026-09-11 - Retain Q2 after the Crank--Nicolson temporal diagnostic

Unlimited Crank--Nicolson Q2 passes the two predeclared timestep gates. Halving
`dt` changes the conservative subcell density by only `4.19e-5` and covariance
error by `4.74e-6`. Both trajectories have covariance error about `0.00371`,
below the common Monte Carlo bootstrap p95, but integrated negative mass remains
about `8.28e-4`. This supports retaining the uniform-mesh Q2 spatial branch and
shifts the main effort toward a positivity treatment compatible with the
second-order trajectory. First run the existing adaptive global limiter as a
controlled comparator; it is not presumed to preserve this improvement.

## 2026-09-11 - Reject global scaling for the Crank--Nicolson Q2 path

Adaptive global correction changes the successful unlimited Crank--Nicolson
timestep result from `L1>=4.19e-5` to `L1>=0.01088`, failing the `0.0025` gate.
The full-step corrected mass error is `1.27e-10`, also above its gate. Covariance,
marginal, negativity and limiter-impact metrics pass, but they do not override
the density and conservation failures. Global scaling remains an audit
comparator and is rejected as the production correction for this path.

Proceed to a local conservative correction only after defining a genuinely
positive low-order update for the full drift-diffusion operator. Published
convex-limiting results for hyperbolic systems and local DDG flux corrections
for gradient-flow Fokker--Planck equations motivate architectures; their proofs
do not directly cover this fully implicit SIPG, full-SPD Lorenz operator or
Crank--Nicolson step.

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
