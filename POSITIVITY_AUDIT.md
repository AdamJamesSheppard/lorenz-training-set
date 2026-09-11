# Audit of the positivity construction

## Experimental local Q2 projection

`lorenz_fpe/local_projection.py` implements a minimum-change diagnostic and an
opt-in propagation candidate. For every Q2 cell with non-negative average, it minimizes the local
DG mass-matrix distance to the raw polynomial subject to non-negative
Bernstein coefficients on the fixed `2x2x2` control subcells and exact cell-mass
preservation. Adaptive subdivision only skips a raw cell already certified
non-negative. Accepted optimizer results are rechecked against every original
constraint row.

Negative cell averages are a declared infeasibility outcome because no
non-negative polynomial can have a negative integral. The optional hybrid
diagnostic first applies the incumbent global conservative average projection,
then replaces Stage-2 scalar scaling by the local QP. The same hybrid is wired
as an explicitly experimental Q2 propagation strategy for a predeclared
three-timestep test. The mass equality is eliminated in a fixed null-space
basis, after which OSQP reuses the same reduced Hessian and inequality matrix
for every cell. SLSQP remains available as an oracle. Accepted outputs undergo
the same full-constraint, average and scalar-objective-bound checks. The
completed dynamic run certified all 560 steps, but failed positive observed
timestep order and is not enabled during production propagation.

> This audit originally covered Q1. The experimental Q2/Q3 path now uses
> Bernstein coefficients on `2x2x2` control subcells. An experimental adaptive
> branch now uses recursive tensor-Bernstein subdivision to avoid some false
> alarms while retaining the fixed correction for witnessed-negative and
> unresolved cells. The current guarantee and its measured accuracy cost are
> in [METHOD_SELECTION_REPORT.md](METHOD_SELECTION_REPORT.md).

Primary source: Chen Liu, Jingwei Hu, William T. Taitano, and Xiangxiong
Zhang, “An optimization-based positivity-preserving limiter in semi-implicit
discontinuous Galerkin schemes solving Fokker--Planck equations,” *Computers &
Mathematics with Applications* 192 (2025), 54--71,
<https://doi.org/10.1016/j.camwa.2025.05.008>.

## Finding

The project implements the paper's **two-stage post-processing optimisation**,
but it does not reproduce the paper's complete DG/time discretisation.  Earlier
wording that could be read as claiming the whole scheme was the published
scheme was too strong.

| Item | Liu et al. | This project | Audit conclusion |
|---|---|---|---|
| Equation | Linearised Fokker--Planck convection--diffusion; spatially varying, uniformly SPD diffusion | Lorenz FPE; constant full tensor `D=BB^T/2` | Covered when `D` is positive definite; rank-deficient `B` gives semidefinite `D` and is outside the paper's uniform-coercivity hypothesis |
| Mesh | Uniform rectangular/square cells in dimension `d` | Uniform affine, axis-aligned hexahedra in 3-D | Compatible special case |
| Space | Broken polynomial degree `k>=1`, hierarchical modal basis; tensor Gauss point set | Basix discontinuous nodal Q1--Q3 on hexahedra | Different basis; the local polynomial spaces overlap but enforcement sets differ |
| Convection | Lax--Friedrichs flux, convection explicit in time | Upwind flux, convection implicit | For a continuous scalar linear drift, local LF with the exact face speed reduces to upwind spatially; time treatment differs |
| Diffusion | NIPG, implicit | SIPG, implicit | Not the same bilinear form; the paper's NIPG coercivity statement is not being claimed for this SIPG form |
| Time | First-order semi-implicit: explicit convection, implicit diffusion | Fully implicit backward Euler | Different scheme; both are first order |
| Stage 1 | Constrained `L2` projection of cell averages, normally solved by Douglas--Rachford | The identical lower-bounded convex problem solved directly through its scalar KKT multiplier | Same unique minimiser; no Douglas--Rachford iteration occurs in this code |
| Stage 2 | Zhang--Shu scaling about each corrected average, enforcing a lower tolerance at a selected quadrature set | Q1 vertices; fixed Q2/Q3 Bernstein subcells; or adaptive Bernstein certification with fixed fallback | Same scaling idea, stronger whole-cell sufficient condition locally |
| MPI | Douglas--Rachford described as parallelisable | Cell averages gather to rank zero, exact global projection, scatter back | Mathematically global and conservative, but not scalable like the proposed distributed iteration |

## Exact claims supported by this implementation

Stage 1 solves

```text
minimise    (1/2) sum_K |K| (x_K-w_K)^2
subject to  x_K >= 0
            sum_K |K|x_K = sum_K |K|w_K.
```

The KKT equations give `x_K=max(0,w_K-lambda)`.  Bisection to 100 iterations
finds the unique multiplier; a bound-preserving roundoff correction contracts
the non-negative active slacks when mass must be removed and then applies a
guarded one-cell ulp repair.  This enforces the mass equality without crossing
the lower bound. This is the same strictly convex optimisation problem as the
paper's equations (22)--(24), solved directly rather than by the optional
Douglas--Rachford algorithm.  The code records the mass before Stage 1, after
Stage 1, and after Stage 2.

Stage 2 applies

```text
theta_K = clamp(x_K/(x_K-min_vertex(p_K)), 0, 1)
p_K <- x_K + theta_K (p_K-x_K).
```

It leaves the cell average unchanged.  On the reference cube, a nodal Q1
polynomial is

```text
p(xi,eta,zeta) = sum_(i,j,k in {0,1}) p_ijk
                 l_i(xi) l_j(eta) l_k(zeta),
```

where every product basis function is non-negative on `[0,1]^3` and the basis
functions sum to one.  Consequently non-negative vertex coefficients imply
`p>=0` everywhere on the reference cell.  An affine axis-aligned cell map
preserves this conclusion.  This whole-cell Q1 guarantee is an independent
argument stronger than the paper's finite-quadrature-point statement; it does
not extend automatically to Q2, a modal coefficient check, or curved cells.

For Q2/Q3, the fixed branch converts each tensor polynomial to Bernstein form
on `2x2x2` control subcells. Non-negative coefficients certify non-negativity
because the basis is non-negative and partitions unity. The converse can fail.
The adaptive branch recursively applies exact de Casteljau subdivision. Each
cell is classified as `CERTIFIED_NONNEGATIVE` only when all terminal lower
bounds are non-negative, `WITNESSED_NEGATIVE` only after an actual point value
is negative beyond a scale-aware floating-point tolerance, and `UNRESOLVED`
when a bound still straddles zero at the depth limit. Both latter classes use
the existing fixed scaling, preserving its whole-cell sufficient guarantee.
Polynomials that touch zero may remain unresolved at every finite depth, so the
classifier is deliberately incomplete.

A direct tensor-product example explains the incompleteness without relying on
simplicial results. Let `p(x,y,z)=(x-c)^2`, with `c` irrational and in `(0,1)`.
At every dyadic subdivision depth, the unique interval `[a,b]` containing `c`
has a negative middle quadratic Bernstein coefficient proportional to
`(a-c)(b-c)`, while `p` is globally non-negative. Hence finite dyadic
subdivision never certifies that cell. The classifier correctly returns
`UNRESOLVED` at its configured depth and applies the sufficient fallback.

The 2026-09-11 audit also found that the former additive Stage-1 roundoff repair
could produce tiny negative active averages and consequently negative scaling
factors. That implementation and its numerical decision runs are superseded.
Regression tests now require projected averages to remain non-negative,
scaling factors to lie in `[0,1]`, and the before/after masses to agree to the
declared tolerance.

The default lower bound is exactly zero, rather than the paper's small positive
`epsilon`.  Floating-point results can consequently be around `-1e-20`; the
integrated negative mass and a scale-aware tolerance are checked separately.

## Claims not supported

- The raw SIPG/backward-Euler solution is not positivity preserving.
- The paper does not prove the complete scheme used here, because its diffusion
  form and time treatment differ.
- Positivity and conservation do not imply adequate resolution.
- The paper's accuracy discussion assumes a suitably accurate underlying DG
  solution and a feasible exact solution.  It is not a blanket proof that
  post-processing cannot degrade every observable in this Lorenz calculation.
- The paper's uniformly positive-definite diffusion assumption excludes
  singular `D`; positivity post-processing remains algebraically valid there,
  but the cited diffusion analysis does not apply.

The production decision must therefore be based on measured raw-to-limited
corrections, convergence, and independent stochastic comparisons.  Those
measurements are generated by `lorenz_fpe.validation.limiter_impact` and the
production-readiness workflow.
