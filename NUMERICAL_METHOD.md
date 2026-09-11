# Numerical method and mathematical scope

> The current Q1/Q2 method-selection result is documented in
> [METHOD_SELECTION_REPORT.md](METHOD_SELECTION_REPORT.md). Q1-only statements
> below describe the original baseline and are retained for audit history.

## Equation and boundary truncation

For `dX=f(X)dt+B dW`, the code uses `D=BB^T/2` and solves

```text
partial_t p + div(J) = 0,        J = f p - D grad(p)
```

on a finite rectangular domain with `J.n=0`.  Constants are admissible DG test
functions, and all exterior total-flux terms are zero, giving discrete global
mass conservation before and after limiting.  Boundary shell mass and the
ratio of boundary-cell density to global maximum are recorded.  A low boundary
metric is necessary but not sufficient; `validation.domain_sensitivity()` also
compares a baseline and expanded box.

## DG operator

The native density can be discontinuous tensor-product degree one, two, or three on affine
hexahedra.  Advection is integrated by parts cellwise and uses the upwind trace
selected by the sign of the interior normal drift.  Diffusion uses symmetric
interior penalty terms for the complete constant tensor `D`, including its
off-diagonal entries.  The penalty defaults to 16.  Backward Euler gives a
time-independent nonsymmetric matrix which is assembled once.  Experimental
`theta=0.5` Crank--Nicolson support is retained only for controlled comparison:
the post-limiter solution is conservative and positive, but the cited paper
does not establish that fully coupled variant as its positivity-preserving
semi-implicit method.

The implementation is not a literal reproduction of Liu et al.'s full scheme.
Their analysis uses Lax--Friedrichs convection, NIPG diffusion, and explicit
convection/implicit diffusion; this code uses continuous-drift upwinding,
SIPG, and a fully implicit theta method.  The shared component is the
two-stage constrained-average/scaling postprocessor.  The distinction and all
hypotheses are catalogued in [POSITIVITY_AUDIT.md](POSITIVITY_AUDIT.md).

PETSc GMRES uses ILU in serial and block-Jacobi in MPI by default.  A solve is
accepted only if PETSc reports convergence and the independently recomputed
`||b-Ax||_2/||b||_2` passes the dataset quality threshold.

## Positivity post-processing

Let `w_K` be the unlimited DG cell averages and `|K|` the cell volumes.  Stage
one solves

```text
minimise    1/2 sum_K |K| (x_K-w_K)^2
subject to  x_K >= 0
            sum_K |K|x_K = sum_K |K|w_K.
```

The KKT solution is `x_K=max(0,w_K-lambda)`. A monotone bisection finds the
single multiplier `lambda`; the final floating-point repair removes residual
mass by proportionally contracting non-negative slacks, followed by a guarded
one-cell ulp correction. This preserves both the lower bound and the equality
constraint. The constant mode in every cell is shifted from `w_K` to `x_K`.

For Q1, Stage two uses

```text
theta_K = clamp(x_K/(x_K-min_vertex(p_K)), 0, 1)
p_K <- x_K + theta_K (p_K-x_K).
```

It preserves the corrected cell average and makes every local vertex value
non-negative.  A Q1 polynomial on an affine box is a convex combination of its
eight vertex coefficients, so it is non-negative everywhere in the cell.

For Q2/Q3, the same scaling formula uses the minimum Bernstein coefficient on
the configured tensor control subcells. Non-negative coefficients are a
sufficient whole-cell certificate. The experimental adaptive mode recursively
subdivides the tensor Bernstein form and skips scaling only when every leaf is
certified non-negative. A negative point evaluation is recorded as a witness;
a negative coefficient without such a witness remains unresolved and receives
the fixed conservative fallback. The code reports cell-average corrections,
scaling activations, three-way certificate counts and quadrature negative mass.

This follows the two-stage framework of Liu et al. (2025), equations (22)--(23)
and the Zhang--Shu scaling step.  The implementation solves the simple lower-
bounded projection directly rather than by their Douglas--Rachford iteration;
both solve the same strictly convex optimisation problem.

The theorem being used is deliberately narrow.  It does not say:

- that the unlimited implicit DG solution is positive;
- that positivity implies accuracy or low numerical diffusion;
- that arbitrary higher-degree polynomials are positive between checked
  quadrature points;
- that the same statement holds on curved/distorted hexahedra;
- or that an interpolated ML tensor is conservative.

## Bayesian analysis and dataset distribution

For a linear observation `y=Hx+eta`, `eta~N(0,R)`, the default now computes a
quadrature-accurate L2 projection of the likelihood-times-forecast product and
divides it by the finite-element evidence integral. The old nodal coefficient
product remains only as an explicitly selected validation baseline. Bayes normalisation is
semantically separate from PDE error correction.  The resulting full numerical
posterior—not moment-matched Gaussian data—is passed to the next forecast.

A Gaussian is used only to bootstrap each independent experiment.  Truth and
observations are then sampled, repeated forecast/analysis cycles are run, and
primary operator pairs are collected only after configurable burn-in.  The
manifest split unit is the independent trajectory.  Posterior covariance
eigenvalues, entropy, effective support, skewness, kurtosis, and boundary
metrics are recorded to compare startup and mature DA distributions.  The
current summary is exploratory; stationarity of the distribution over
posteriors is not assumed.

## Conservative tensor export

With one output voxel per DG cell, a voxel value is the native DG cell average
(the mean of the eight Q1 coefficients on these affine boxes).  Therefore

```text
sum_ijk voxel_density[i,j,k] * voxel_volume = integral p_h dx.
```

The equality is checked for every candidate sample.  This one-value export is
not shape preserving.  The default now uses two subvoxels per native axis.
For Q1, a subbox average equals the polynomial value at the subbox centre; the
eight subbox averages form a full-rank system for the eight coefficients.
Least-squares reconstruction with an exact cell-mean correction consequently
round-trips solver-generated Q1 states to floating-point error.  The positivity
limiter remains the final guard for tensors not produced by this solver.

## Remaining limitations

The current priority limitation is positivity correction compatible with the
accurate Q2 trajectory. On the controlled same mesh, unlimited Crank--Nicolson
passes the timestep density gate and reaches covariance error about `0.00371`,
but carries integrated negative mass about `8.28e-4`. Applying the current
adaptive global limiter removes negative mass while increasing the
full-versus-half density difference from `4.19e-5` to `0.01088`. A positive,
mass-conservative low-order full-SPD update and local pairwise flux correction
are therefore required before this path can advance.

The Q2 path now has fixed-subcell and adaptive-certificate experimental modes,
plus a diagnostic switch that evolves the unlimited algebraic trajectory.
None has production status. The corrected same-mesh comparison must reproduce
the earlier apparent Q2 improvement, and the two-timestep unlimited run must
separate temporal sensitivity from accumulated limiter-path dependence before
any local/operator-level positivity method is selected.

Dataset writing and the global cell-average projection currently gather to
rank zero.  Profiling confirms that the limiter dominates step time and that
global diagnostics stop scaling.  Forecast assembly and solves support MPI,
but the serial dataset writer, distributed optimisation/output, representative
mature-domain comparisons, and observation-specific burn-in studies remain
future work.  Native NumPy checkpoints are serial-only.  The observation
module implements configurable linear full or partial operators, not an
arbitrary nonlinear `h`.
