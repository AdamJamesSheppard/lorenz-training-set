# Mathematical specification

## Model

For the stochastic Lorenz-63 state

`dX_t = f(X_t) dt + B dW_t`,

the density satisfies

`partial_t p = -div(f p) + div(D grad(p))`, with `D = 0.5 B B^T`.

Default parameters are `sigma=10`, `rho=28`, `beta=8/3`, and `B=I`. Thus
`div(f) = -sigma - 1 - beta = -41/3`. Omitting this compressibility changes the
PDE.

## Computational domain and boundary

- Default box: `[-30,30] x [-40,40] x [-10,70]`.
- Boundary condition: zero total probability flux,
  `(f p - D grad(p)) . n = 0`.
- This is a bounded-domain approximation to the whole-space SDE. It does not
  impose zero advective and diffusive flux separately.

## Discretization

- Affine hexahedral mesh; discontinuous tensor-product Q1 is the baseline.
- Conservative upwind numerical flux for advection.
- Symmetric interior-penalty Galerkin diffusion for the full tensor `D`.
- Backward Euler (`theta=1`) is the validated baseline. Crank--Nicolson is
  experimental and still followed by positivity post-processing.
- Analytic densities and likelihood products use quadrature-controlled L2
  projection; the current adopted quadrature degree is 14.

## Positivity and conservation

Each timestep applies:

1. a global weighted projection of cell averages onto the non-negative,
   equal-mass set; and
2. scaling of higher modes about corrected cell averages until the relevant
   Bernstein coefficients are non-negative.

On the current affine Q1 cells, vertex/Bernstein positivity is a whole-cell
guarantee. For Q2/Q3, positivity on fixed control subcells is sufficient but
not necessary and can over-limit the solution. Exact implementation claims and
excluded claims are in `POSITIVITY_AUDIT.md`.

## Executable invariants

- Probability mass error below the test-specific tolerance.
- Density minimum no lower than the justified floating-point tolerance.
- Symmetric positive-semidefinite diffusion tensor.
- True PETSc relative residual below the configured solver threshold.
- Conservative native/structured round trip.
- Total-flux boundary convergence for the manufactured solution.
- Moment and distribution comparisons against exact-native-law Monte Carlo
  and an independent finite-volume hierarchy where applicable.

Passing these checks is numerical evidence for tested configurations, not an
analytical proof or a production certification.

## Dataset semantics

An accepted pair is

`(posterior.npy = p_k|k, forecast interval) -> (forecast.npy = p_{k+1}|k)`.

Arrays are float64 conservative subcell averages with axes `(x,y,z)`. Splits
are by complete independent trajectory. Burn-in and failed cycles remain in
the audit trail but are excluded from `training_samples`.

