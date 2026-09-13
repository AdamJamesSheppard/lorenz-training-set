# Numerical-method selection for stochastic Lorenz-63 forecasts

## Decision

**Classification: `FULL_SPD_DIFFUSION_CERTIFIED`.** The local-QP
Q2--Crank--Nicolson candidate has passed its startup-state temporal, positivity,
identity-noise spatial and non-diagonal full-SPD spatial gates. Mature-state and
domain certification remain mandatory before generating a large neural-operator
training set.

The controlled same-mesh and two-timestep experiments have been completed.
They overturn the old equal-DOF ranking: corrected Q1 is now the controlled
baseline, while Q2 is materially more accurate on the same physical mesh and
timestep. The strongest numerical trajectory observed is unlimited Q2 with
Crank--Nicolson (`E_cov=0.0037111`), and the most accurate tested non-negative
in-loop trajectory is Stage-1 average repair plus the local QP (`E_cov` about
`0.0075`). Neither is production-certified.

| Controlled trajectory (`30x36x36`) | `E_cov` at `dt=0.000625` | Status |
|---|---:|---|
| Q1, backward Euler, global limiter | `0.0871923` | controlled baseline |
| Q2, backward Euler, adaptive global limiter | `0.0237745` | non-negative; density timestep gate fails |
| Q2, unlimited backward Euler | `0.00726675` | negative and density timestep gate fails |
| Q2, unlimited Crank--Nicolson | `0.00371110` | temporal gates pass; negative mass makes it inadmissible |
| Q2, Crank--Nicolson, adaptive global limiter | `0.0219156` | non-negative; density timestep gate fails |
| Q2, Crank--Nicolson, Stage-1 plus local QP | `0.0075085` | temporal, identity-noise spatial and full-SPD spatial gates pass; mature-state pending |

The common 200,000-path Monte Carlo covariance bootstrap p95 is
`0.00628239`. The unlimited Crank--Nicolson discrepancy lies below this measured
sampling scale, which makes the discrepancy unresolved by this reference; it
does not establish the true PDE discretization error.

The decisive comparison is the unlimited-versus-corrected Crank--Nicolson
pair. Halving `dt` changes the unlimited conservative subcell density by only
`L1>=4.19e-5`, but the same comparison after adaptive global correction gives
`L1>=0.010884`. The unlimited trajectory carries integrated negative mass
`8.28e-4` and minimum quadrature value about `-1.35e-5`, so it cannot be used
as a probability-density generator. Global correction removes that negativity
but fails the predeclared density-convergence gate and increases covariance
error to about `0.022`.

An offline terminal-state experiment now shows that conservative Stage-1
average repair followed by a cell-local minimum-change QP is materially less
intrusive than scalar scaling. It gives `E_cov=0.005876/0.005874` at the two
timestep levels, zero measured negative mass, complete Bernstein
certification, and cross-timestep `L1=3.94e-5`. Its mass-matrix correction
objective is about 17% of matched scalar scaling. Purely cell-local repair is
incomplete because about 17,500 raw cells have negative averages.

The historical three-level **in-loop Stage-1 plus local-QP
Q2--Crank--Nicolson trajectory** is complete. A reduced fixed-matrix OSQP
backend passed a 2,413-cell SLSQP comparison and reduced the matched three-step
projection time by a factor of `10.78`. Across all 560 production-mesh steps,
every final state was Bernstein-certified, negative mass was zero, no optimizer
fallback occurred, and covariance error stayed near `0.0075`. The adjacent
density differences, `5.24e-4` and `5.42e-4`, both pass their absolute gate but
do not decrease; observed order is `-0.0488`. Full and quarter levels also have
absolute mass errors `1.25e-10` and `2.75e-10`, above the `1e-10` gate. A
subsequent tight-solve four-level diagnostic supersedes that method decision:
its final two differences are `5.418e-4` and `1.620e-4`, giving observed order
`1.741`; all 1,200 steps pass positivity and mass gates with no optimizer
failure or fallback. The candidate therefore advances to spatial refinement.

The aggregate classification is `FULL_SPD_DIFFUSION_CERTIFIED`; no threshold
was relaxed after seeing the full-SPD result. This remains narrower than
production certification. The next experiment must freeze the surviving method
and measure a common mature later-time or post-analysis state before domain
sensitivity. Sections 18--27 record the experimental sequence.

Role assignments are separate:

| Role | Decision |
|---|---|
| Production reference solver | **Unfilled.** Local-QP Q2--Crank--Nicolson is the leading admissible candidate after passing startup-state temporal/positivity, identity-noise spatial and full-SPD spatial gates; mature-state and domain evidence remain required. |
| Independent verification solver | **Develop alongside correction work:** a dynamically scaled, translated whole-space Hermite-Galerkin solver, checked by mode decay and moment convergence, plus Monte Carlo for moments. Spectral positivity is not assumed. |
| Current baseline | Q1 upwind/SIPG, backward Euler, quadrature-14 L2 initialization, projected Bayesian analysis and conservative postprocessing. It is a controlled comparator rather than a production selection. |

The full-SPD requirement controls the ranking. Directional
Scharfetter-Gummel/Chang-Cooper and the 2026 Diagonal Frog/FCDF methods become
more attractive if production noise is restricted to diagonal `B`; their present
theory and evidence do not justify selecting them for arbitrary mixed diffusion.

Literature was checked through 10 September 2026. The attached request ends
mid-sentence in Section 31; all complete requirements through that point are
addressed here.

## 1. Mathematical target and governing risks

With constant `B` and `D=BB^T/2`, the forecast equation is

\[
  \partial_t p + \nabla\!\cdot J=0,
  \qquad J=f p-D\nabla p,
\]

on a finite box with `J.n=0`. The equation is linear in `p`, conservative,
transient and generally non-self-adjoint. Lorenz drift is nonlinear in state and
irreversible; it is not a gradient drift. For the standard parameters,

\[
  \nabla\!\cdot f=-\sigma-1-\beta=-\frac{41}{3},
\]

so the expanded equation contains the compressive reaction term
`-(41/3)p`. Any method that treats the drift as divergence-free solves a
different equation.

Full-rank `B` gives a uniformly parabolic equation on the bounded box. A
rank-deficient `B` gives a degenerate problem; hypoellipticity then requires a
separate bracket argument. Results requiring scalar diffusion, a diagonal
tensor, detailed balance, a known invariant density, or a gradient-flow
factorization do not transfer automatically.

The physical SDE lives on `R^3`. Reflecting truncation is a model approximation,
even though the implemented total-flux weak form is internally consistent.

## 2. Historical Run-6 evidence (`WHAT_RUN6_ACTUALLY_ESTABLISHES`)

This section preserves the evidence available before the controlled same-mesh
and Crank--Nicolson experiments. Its Q1 and equal-DOF Q2 values remain valid for
their recorded configurations, but its method ranking and proposed next
experiment are superseded by Sections 20--23.

### Established numerical evidence

| Item | Verified result | Scope |
|---|---:|---|
| Best corrected Q1 covariance error | `E_P=0.0855765124` | Q1 `30x36x36`, `dt=0.000625`, `t=0.05`, 311,040 DOFs; same represented initial law as MC |
| MC covariance uncertainty | bootstrap p95 `0.0062823927`; Q1/noise ratio `13.6216` | 200,000 paths; MC `dt=0.000125` |
| MC timestep sensitivity | `0.000110865` normalized covariance change | common Brownian paths, `0.000125 -> 0.0000625` |
| Q1 marginal TV | `0.02347`, `0.01275`, `0.01116` | 100,000-path validation realization; not the 200,000-path covariance bootstrap run |
| Q1 forecast limiter | relative L1 mean/max `0.003448/0.006292`; L2 mean/max `0.000189/0.000322` | limiting at all 80 steps; final mass within `1.5e-11` |
| Unlimited Q2 L2 projection | `E_P=2.844e-10`; minimum `-1.2125e-6`; integrated negative mass `1.9715e-4` | analytic initial Gaussian; true negativity exists despite nearly exact moments |
| Q2 same-law forecast | `E_P=0.254842595`; marginal TV `0.02273`, `0.01586`, `0.02935` | Q2 `20x24x24`, `dt=0.00125`, 311,040 DOFs, 100,000 paths |
| Q2 forecast limiter | relative L1 mean/max `0.012381/0.025983`; L2 mean/max `0.000549/0.001166` | cell-average correction becomes zero after startup; high-order scaling dominates |
| Q2 correction mechanism | mean fraction with negative raw cell average `0.00547`; mean scaled fraction `0.362` | negative cell averages occur only at startup; polynomial scaling occurs at every step |
| Q1/Q2 comparison basis | equal total DOFs, unequal cells and unequal timestep | Q1 spacings `(2,2.222,2.222)`; Q2 `(3,3.333,3.333)` |
| Projection quadrature | degree 14 differs from degree 16 by `2.659e-10` in coefficients | `12x16x16` projection check |
| Corrected mature DA | no production-resolution validation | exploratory Q1 `8x10x10`, `dt=0.005`; analysis limiter L1 mean `0.3627`, p95 `0.6614` |

Evidence files: [initial representation](validation_repair_report.json),
[Q1/MC/FV comparison](independent_reference_refined_report.json),
[MC timestep](mc_timestep_same_initial_law.json),
[Q2 projection](higher_order_report.json),
[Q2 forecast](q2_common_law_subcell_monte_carlo.json),
[Q2 Bayesian analysis](q2_bayesian_update_subcell_report.json), and
[mature DA](mature_da_projected_report.json).

### Reasonable inferences

- Q1's covariance excess is compatible with numerical diffusion. Its covariance
  eigenvalues are systematically too large, upwind diffusion is large at the
  measured cell Péclet numbers, MC time error is much smaller, and the independent
  first-order FV hierarchy approaches Q1 and MC as it is refined. The existing
  experiments do not isolate upwind flux, backward Euler, mesh, and limiting well
  enough to prove which component dominates.
- Current Q2 accuracy is damaged mainly by high-order polynomial scaling rather
  than cell-average repair: Stage 1 is normally inactive after startup, while
  Stage 2 changes about 36% of cells on average and has a larger L1 correction
  than Q1.
- Fixed `2x2x2`-subcell Bernstein bounds probably generate some false positivity
  alarms, because negative Bernstein coefficients do not imply a negative
  polynomial. The initial Q2 projection also has measured negative mass, so
  certificate conservatism cannot explain every correction.
- Uniform meshes spend most cells in negligible-density regions. Adaptivity is
  likely valuable after a base operator and positivity architecture are selected.

### Unresolved questions

- Would Q2 beat Q1 on the same physical cells and timestep before and after a
  rigorously audited positivity correction?
- What fraction of Q2 scaling is caused by certified negativity, false
  Bernstein alarms, and unresolved near-zero cells?
- Does a local flux correction preserve covariance materially better than
  scaling a completed polynomial?
- Which full-SPD method has acceptable 3-D high-Péclet accuracy and cost?
- Are corrected mature posteriors representable at feasible resolution, and are
  reflecting-box effects negligible for them?
- No deterministic full-density reference is converged enough to assign a final
  L1 error.

## 3. Audit of the implemented Q1/Q2 method

The code uses discontinuous tensor `Q_k` polynomials on affine hexahedra,
conservative upwind advection, SIPG diffusion for a constant full tensor, and
backward Euler by default. The single exterior total-flux term is set to zero;
advection and diffusion are not separately assigned zero normal flux. Testing
with `p=C exp(0.4x-0.3y+0.2z)`, `D=I/2` and
`f=(0.2,-0.15,0.1)` gives about second-order Q1 L1 convergence and maximum mass
error `3.12e-12`. This validates the discrete boundary derivation for that
manufactured problem. It does not estimate finite-box error for Lorenz DA states.

The positivity postprocessor has two stages:

1. cell averages are projected onto the non-negative, equal-total-mass set;
2. each polynomial is scaled about its corrected average until chosen Bernstein
   coefficients are non-negative.

For equal-volume cells with a lower bound of zero, the Stage-1 KKT solution has
the form `x_K=max(0,w_K-lambda)`. The local code solves this exact convex
projection on rank 0 and broadcasts the result. Stage 2 provides a whole-cell
sufficient certificate for the chosen subcells. Its global scaling of all
nonconstant modes can alter first and second moments substantially.

The limiter is conservative, but MPI scalability is limited by the rank-0 gather.
Measured eight-rank step times are `0.330 s` for Q1 and `0.282 s` for equal-DOF
Q2; diagnostics/output and global postprocessing scale worse than assembly and
linear solution. Matrix reuse is already available because the drift, diffusion,
mesh and timestep are fixed during a forecast. The measured serial Q1
`30x36x36`, 80-step forecast took `88.10 s`; the eight-rank step benchmark
extrapolates to `26.39 s` before non-scaling diagnostics and output. Same-mesh Q2
will have 1,049,760 unknowns, 3.375 times Q1, so peak memory and wall time must be
measured rather than inferred from the favourable equal-DOF Q2 benchmark.

## 4. Q2 raw-moment preservation

Let `Pi_2 p` be the exact cellwise L2 projection into tensor-product `Q2(K)`.
For every `v in Q2(K)`,

\[
  \int_K (\Pi_2p-p)v\,dx=0.
\]

On an affine Cartesian/hexahedral cell, `Q2(K)` contains

\[
  1,\quad x_i,\quad x_i^2,\quad x_ix_j.
\]

Choosing these functions as tests and summing over cells proves exact
preservation of mass, first raw moments and all second raw moments. Consequently
the mean and covariance of the projected finite-box density are preserved,
provided the projection integrals and subsequent moment integrals are exact.
This is a proof for the projection operation, not for the time-dependent Q2
scheme.

The property is broken or perturbed by:

- inexact quadrature;
- Stage-1 cell-average redistribution, which preserves only global mass;
- Stage-2 scaling, which preserves each cell average but changes higher moments;
- approximate time propagation;
- a non-moment-preserving export or voxel projection.

The measured `2.844e-10` initial covariance error confirms the projection
argument numerically. Its importance is conditional: it removes initialization
moment error but offers no protection against transport diffusion or repeated
limiting.

## 5. Optimization-based DG and Zhang–Shu theory

The 2025 Liu–Hu–Taitano–Zhang method uses modal broken total-degree
`P^k`, `k >= 1`, on uniform rectangular cells and a tensor-product
`(k+1)`-point Gauss test set. Its operator combines Lax–Friedrichs convection,
nonsymmetric interior-penalty diffusion and a first-order semi-implicit split:
convection is explicit and diffusion implicit. The formulation permits variable
full SPD diffusion and a total no-flux condition. The reported experiments use
`P^2` and `P^3` only, are all two-dimensional, and exhibit the even/odd NIPG
pattern of second-order convergence for `P^2` and fourth-order convergence for
`P^3`. No 3-D convergence or scaling result is supplied.[^1]

Its first stage solves a convex Euclidean projection of cell averages subject to
mass and box constraints. Douglas–Rachford splitting converges to that projection;
it does not establish accuracy of the underlying PDE discretization. Its second
stage uses Zhang–Shu scaling about each feasible average. Positivity is imposed at
a finite quadrature/test set `S_h`; positivity of the complete polynomial between
those points is not claimed.[^1]

The paper's high-order argument is asymptotic. If the exact solution obeys the
bounds and the unlimited discretization has the assumed high-order error, the
projection is no farther from the feasible exact averages than the unlimited
averages, and scaling retains formal order. This controls absolute discretization
error under the theorem's regularity/bound assumptions. It gives no finite-mesh
upper bound for the relative L1 correction in near-zero tails and no guarantee
that a DA covariance gate will pass.

The local implementation shares the two-stage architecture but differs in the
DG diffusion flux (SIPG rather than NIPG), temporal treatment (fully implicit
advection-diffusion rather than explicit/implicit split), advective flux (upwind
rather than Lax–Friedrichs), tensor nodal basis, zero lower tolerance, full-cell
Bernstein certificate, and centralized rather than distributed optimization.
Calling it paper-faithful would overstate the match.

Classical Zhang–Shu scaling preserves the cell average because it multiplies only
deviations from that average. The usual weak-positivity proof first expresses a
forward-Euler cell-average update as a convex combination of monotone fluxes and
quadrature values under a method-specific CFL condition; SSP Runge–Kutta retains
the property because its stages are convex combinations of forward-Euler
steps.[^2] Those arguments do not establish positivity for the present fully
implicit SIPG update. Diffusion needs a separate weak-monotonicity flux analysis,
and the available convection-diffusion constructions are limited to specific
operators, dimensions and boundary conditions.[^3]

## 6. Maximum-principle DG and monotone high-order elements

Liu and Yu prove up-to-third-order maximum-principle DG for the potential-driven
FPE

\[
  p_t=\nabla\cdot(\nabla p+p\nabla U)
\]

with a direct-DG diffusive flux, forward Euler plus SSP time stepping and a
method-specific test set/CFL condition. The full derivation is one-dimensional;
rectangular higher-dimensional extension is stated, while no 3-D theorem or test
with full SPD diffusion is given.[^4]

Srinivasan, Poggie and Zhang construct a nonlinear positivity-preserving LDG
diffusion flux for scalar convection-diffusion in one and two dimensions, with
explicit SSP time stepping and periodic or restricted Dirichlet/Neumann
conditions. Their accuracy proof requires a compatibility condition at zeros of
the exact solution; the paper gives boundary counterexamples where limiting
destroys high order.[^3] This is useful design evidence for local flux correction,
not a theorem for Lorenz/SIPG/full tensor/reflecting 3-D.

Monotone `Q2` and `Q3` finite/spectral-element results by Zhang and collaborators
concern structured-grid Laplace-type operators. The `Q2` results require mesh and
quadrature structure; the `Q3` construction proves a 2-D Laplacian result and
reports only numerical indications for 3-D.[^5] They do not cover a general
non-self-adjoint Lorenz convection-diffusion operator with mixed derivatives.

The irreversible FPE method of Liu, Gao and Zhang starts from a known strictly
positive invariant measure, rewrites the operator through a symmetric/skew
decomposition, and uses structured `Q1/Q2` finite-difference implementations with
backward Euler. The paper explicitly simplifies to a constant scalar diffusion;
monotonicity is proved in one and two dimensions and tests are 2-D.[^6] For
Lorenz-63, the invariant density is unknown and is itself a difficult FPE
solution. The method is attractive for steady-state structure after such a
measure is available, but it is not a direct short-forecast algorithm here.

## 7. AFC/FCT and local flux correction

Algebraic flux correction constructs

\[
  A_{\rm high}=A_{\rm low}+F_{\rm anti},
\]

where mass lumping and added graph viscosity make the low-order update monotone,
then conservative pairwise antidiffusive fluxes are limited against local bounds.
Foundational FEM-FCT work proves positivity for multidimensional transport and
supports arbitrary time stepping; published demonstrations include 1-D shocks
and 2-D scalar transport.[^7] Later AFC analysis covers scalar
convection-diffusion and general simplicial meshes, but theorem assumptions and
convergence rates depend on the limiter and low-order operator.[^8]

Advantages for this project are conservation by pairwise fluxes, dimension-
agnostic graph algebra, natural compatibility with sparse PETSc matrices and a
correction placed inside the update rather than after a complete polynomial has
formed. A parallel FEniCS/PETSc Poisson–Nernst–Planck implementation shows
engineering feasibility, although it uses legacy FEniCS and a different system.[^9]

The gaps are material. A monotone low-order matrix for full anisotropic diffusion
is mesh/operator dependent; a generic Galerkin matrix does not become an
M-matrix automatically. High-order accuracy and nonlinear solver convergence are
limiter-specific. No source found supplies 3-D Lorenz, full-SPD reflecting FPE,
MPI scaling and covariance preservation in one result. AFC is the strongest
architecture-level fallback after the Q2 diagnostic, while the claim that it
damages covariance less remains untested.

## 8. Exponential fitting, complete flux and finite volume

Chang–Cooper and classical Scharfetter–Gummel solve a one-dimensional local
drift-diffusion balance with an exponential fit. They are conservative, positive
under their standard implicit formulations and accurate for equilibrium fluxes.
Dimension-by-dimension extensions are natural for diagonal diffusion; mixed
derivatives destroy the independent 1-D flux structure.[^10]

The 2022 positive Scharfetter–Gummel DDFV scheme is the strongest mature
full-tensor finite-volume candidate found. It treats transient nonlinear
convection-diffusion, general anisotropic tensors and Neumann/no-flux boundaries
with a fully implicit nonlinear positive scheme; formal second-order spatial
accuracy and coercivity/existence are established.[^11] The analysis writes
`Omega subset R^d`, but its primal-dual polygonal construction and every reported
test are two-dimensional unit-square cases. There is no published 3-D Lorenz
convergence, high-Péclet covariance or runtime result. A separate 3-D nonlinear
cell-centred method proves and tests positivity for anisotropic **diffusion** on
distorted meshes, without Lorenz convection or transient no-flux validation.[^12]

Complete-flux variants can reduce upwind smearing and reach second order where
their reconstruction is resolved. General full-tensor monotonicity commonly
requires nonlinear multipoint fluxes or restrictive grids. These methods merit a
full-SPD challenger implementation if the Q2 path fails, but the literature does
not establish a ready production winner.

Structure-preserving FPE finite volumes often preserve entropy or a known
invariant measure under potential/detailed-balance assumptions. Lorenz drift is
irreversible. Such labels alone supply no covariance guarantee, and invariant-
measure formulations can require the very steady density being sought.

## 9. Diagonal Frog and FCDF

Diagonal Frog, Flux-Corrected Diagonal Frog and the ADI variant are arXiv
preprints from June–August 2026, without peer-reviewed publication or independent
replication at the time of this audit.[^13][^14]

The original Diagonal Frog uses eventually nonnegative directional generators;
directional positivity appears only above a lower timestep threshold. Mixed
derivatives use a factorized resolvent with a conditional timestep window. The
split is exactly mass conservative and formally second order in space and time.
Tests are two-dimensional, including anisotropic Gaussian, Kramers and
advection-dominated cases; multidimensional extension is described but no 3-D
experiment is reported.[^13]

FCDF splits a one-dimensional directional operator into an M-matrix upwind core
and Zalesak-limited antidiffusion inside an implicit iteration. The preprint proves
directional positivity for all timesteps, conservation and conditional second-
order behavior, and reports a uniform-Péclet L1 result for its stated 1-D setting.
Its table of contents, proof and experiments are one-dimensional. Full-SPD mixed
diffusion relies on companion splitting ideas rather than an FCDF theorem.[^14]

The August DF-ADI paper selects a second-order L-stable Padé factor with linear
per-step cost. It explicitly states that the composite scheme is only empirically
positive in the strong cross-diffusion regime because the directional lower step
bound can conflict with the mixed-term upper bound. These methods are valuable
research leads for diagonal `D`; their recency, dimensional gap and conditional
cross-diffusion positivity keep them below mature full-SPD candidates.

## 10. Spectral, low-rank and characteristic methods

Hermite functions match the physical whole space and eliminate artificial box
reflection. Published Hermite FPE analysis proves spectral convergence in
weighted Sobolev spaces for a kinetic FPE and shows the importance of basis
scaling.[^15] Time-dependent scaling and translation stabilize broader parabolic
convection-diffusion problems on unbounded domains.[^16] In three state
dimensions, a tensor Hermite basis is computationally plausible and Lorenz's
quadratic drift gives sparse mode couplings.

The obstacles are absence of pointwise positivity, possible oscillations in
small tails, and poor efficiency when a single global Gaussian-like basis must
represent two curved Lorenz lobes or a narrow multimodal posterior. Adaptive
translation/scaling, sparse grids or tensor trains can reduce mode counts, but
rank growth and positivity remain problem dependent. Accordingly Hermite is the
best independent high-accuracy reference candidate, not the present production
choice. It must be validated by coefficient-tail decay, order/basis refinement,
mass and raw-moment convergence rather than by visual smoothness.

Conservative Lagrange–Galerkin methods can follow non-divergence-free transport
and reduce upwind diffusion. A mass-preserving two-step method has 1-D/2-D/3-D
tests, second-order time accuracy and optimal L2 estimates, assuming exact-enough
integration and a characteristic map compatible with its boundary hypotheses.[^17]
SLDG-LDG convection-diffusion provides high order and mass conservation with
large timesteps, but published tests are 1-D/2-D and positivity is absent.[^18]
Lorenz characteristics leave the finite box while only the **combined** flux is
reflecting. A boundary-consistent 3-D remap coupled to full diffusion and
positivity is therefore a research project, rather than the next controlled
comparison.

## 11. Q2 positivity certification

For a polynomial in tensor Bernstein form on a box, the range lies in the convex
hull of its coefficients. Therefore:

- all coefficients non-negative is a **sufficient certificate** of whole-cell
  non-negativity;
- a negative coefficient is **not a necessary indication** of a negative
  polynomial;
- degree elevation and subdivision tighten bounds; every polynomial with a
  strictly positive minimum is eventually certifiable under shrinking
  subdivision;[^19]
- non-negative polynomials with zeros can fail to acquire a non-negative
  Bernstein certificate under every subdivision; explicit counterexamples are
  known.[^20]

Adaptive Bernstein subdivision is thus mathematically appropriate as a rigorous
**sufficient certificate** and a high-value **diagnostic**. It is neither a
necessary condition nor a complete decision procedure for `p>=0`, particularly
for probability tails that legitimately approach zero. A production test needs
a maximum depth, scale-aware rounding policy and conservative unresolved-case
fallback. Point evaluation can witness negativity but cannot prove positivity.
Sum-of-squares or general polynomial optimization offers alternative sufficient
hierarchies at far higher per-cell cost and still needs numerical certification.

The recommended experiment uses Bernstein subdivision to classify and measure
the failure mechanism. It does not assume that adaptive Bernstein itself is the
final limiter.

## 12. Genuine 3-D and Lorenz-specific evidence

The literature search found very little evidence at the exact intersection of
3-D, transient, irreversible nonlinear drift, full SPD diffusion, no-flux,
proved positivity and high-Péclet convergence.

The clearest Lorenz-63 FPE computation found solves a **stationary** null-mode
problem using centered finite differences on `160^3` points with isotropic
diffusion and density set to zero outside the box. It reports 500 GB memory,
compares projected densities with very long stochastic simulation, and gives no
positivity theorem.[^21] This is genuine 3-D Lorenz evidence, but its goal,
boundary, diffusion tensor and memory profile differ sharply from repeated
short-time DA forecasts.

Other genuine 3-D evidence is fragmented: Lagrange–Galerkin convection-diffusion
has 3-D tests without positivity; 3-D anisotropic finite volume has positivity
for diffusion without Lorenz transport; the current project has 3-D Lorenz/full-
tensor assembly and conservation but fails its covariance/limiter gates. No
published method found satisfies the entire target specification directly.

## 13. Theorem-applicability matrix

Codes:

- `PD`: `PROVED_DIRECTLY` for the stated property;
- `PR`: `PROVED_WITH_RESTRICTIONS`;
- `PE`: `PLAUSIBLE_EXTENSION_NOT_PROVED`;
- `EO`: `EMPIRICAL_ONLY`;
- `NA`: `NOT_APPLICABLE`;
- `UK`: `UNKNOWN`.

“Nonlinear drift” means a prescribed state-dependent coefficient; the FPE remains
linear in density.

| Candidate | 3-D theorem | nonlinear drift | irreversible | scalar D | diagonal D | full SPD/mixed | no-flux | mass | positivity/type |
|---|---|---|---|---|---|---|---|---|---|
| Current Q1/Q2 SIPG | PR: mass and limiter only | PD | PD | PD | PD | PD | PD | PD | PR: postprocessed whole-cell certificate |
| Liu et al. optimization DG | PE | PR | PR | PD | PD | PD | PR | PD | PR: feasible averages + finite test set |
| Liu–Yu MPP/DDG | PE | PR: potential drift | PR | PD | PE | NA | PR | PD | PR: test-set/CFL + scaling |
| Positivity LDG convection-diffusion | PE | PR | PR | PD | PE | NA | PR: special boundaries | PD | PR: explicit weak positivity + scaling |
| Monotone Q2/Q3 elements | EO | NA | NA | PD | PE | NA | PR | PR | PR: DMP under structured constraints |
| Liu–Gao–Zhang irreversible FPE | PE | PR: known invariant measure | PD | PD | PE | NA | PD | PD | PR: 1-D/2-D monotonicity conditions |
| AFC/FCT FE | PE | PD | PD | PD | PR | PR: low-order M-matrix required | PR | PD | PR: nodal/local DMP |
| Chang–Cooper/directional SG | PE | PD | PD | PD | PR | NA | PR | PD | PR: nodal/cell positivity |
| Positive SG-DDFV | PE: notation general, construction/tests 2-D | PD | PD | PD | PD | PR: 2-D DDFV full tensor | PD | PD | PD: discrete non-negativity |
| 3-D anisotropic positive FV | PD: steady diffusion | NA | NA | PD | PD | PD | PR: Dirichlet paper | PD | PD: cell positivity |
| Diagonal Frog | PE | PD | PD | PD | PD | PR: conditional mixed block | PR | PD | PR: timestep window |
| FCDF | PE | PD | PD | PD | PE | NA in FCDF theorem | PR | PD | PD: 1-D directional iterates |
| Lagrange–Galerkin | PD | PD | PD | PD | PE | PE | PR: map assumptions | PD | NA |
| SLDG-LDG | PE | PD | PD | PD | PE | PE | UK | PD | NA |
| Hermite-Galerkin | PR | PD | PD | PD | PD | PE | NA: whole space | PR | NA |

Practical and accuracy attributes:

| Candidate | space/time order | high-Péclet evidence | mesh | FEniCSx/PETSc/MPI | covariance evidence | diffusion risk | maturity |
|---|---|---|---|---|---|---|---|
| Current Q1/Q2 SIPG | nominal `k+1` / BE1 | project only; failing observable | Cartesian hex | implemented; rank-0 limiter bottleneck | direct, negative | Q1 high; Q2 limiter dominated | mature ingredients, uncertified combination |
| Liu et al. optimization DG | high order / semi-implicit 1 | 2-D numerical tests | rectangles | feasible, substantial mismatch from current code | none | LF + scaling dependent | peer reviewed 2025 |
| Liu–Yu MPP/DDG | up to 3 / SSP order | lower-D tests | rectangles | possible new flux/operator | none | limiter/CFL dependent | peer reviewed 2014 |
| Positivity LDG | high order / SSP | 1-D/2-D tests | intervals/rectangles | major operator change | none | low when resolved; boundary caveat | peer reviewed 2018 |
| Monotone Q2/Q3 | 4th-ish elliptic stencil / BE1 in FPE work | weak for transport | uniform structured | possible FD/FE rewrite | none | transport treatment unresolved | peer reviewed |
| Liu–Gao–Zhang | Q1 second, Q2 fourth / BE1 | 2-D tests | uniform structured | possible, invariant precompute | none | lower than upwind when conditions hold | peer reviewed 2024 |
| AFC/FCT | high target, locally low / explicit or implicit | extensive transport literature | general simplicial; tensor cases conditional | PETSc practical, custom graph/MPI work | none here | low-order fallback can smear | mature architecture |
| Chang–Cooper/directional SG | usually 1–2 / implicit 1 | strong 1-D tradition | aligned Cartesian | separate FV/FD implementation | none | crosswind/splitting risk | mature diagonal method |
| Positive SG-DDFV | formal 2 / BE1 | anisotropy tests, 2-D | general polygonal primal-dual | nontrivial new FV framework | none | nonlinear monotone flux can smear layers | peer reviewed 2022 |
| 3-D anisotropic positive FV | observed 2 / steady | diffusion tests | distorted polyhedra | separate FV | none | convection absent | peer reviewed 2021 |
| Diagonal Frog | 2 / 2 | 2-D high-Péclet tests | Cartesian | separate FD, banded/Krylov | none | split/cross-term risk | 2026 preprint |
| FCDF | conditional 2 / defect-corrected 2 | 1-D Péclet sweep | Cartesian lines | separate nonlinear FD | none | limiter layers | 2026 preprint |
| Lagrange–Galerkin | high / 2 | transport-favourable, no Lorenz test | FE | feasible, expensive remap/quadrature | none | interpolation/remap | peer reviewed 2022 |
| SLDG-LDG | high / high | 1-D/2-D | structured DG | major 3-D implementation | none | interpolation/positivity | peer reviewed/preprint lineage |
| Hermite-Galerkin | spectral / method dependent | no direct Lorenz transient benchmark found | whole-space modes | separate sparse tensor implementation, MPI plausible | none here | oscillatory tails, basis mismatch | mature analysis, new application |

No row has `PD` across the full target. Entries describe source scope and project
evidence; they are not endorsements.

## 14. High-Péclet assessment

Use the directional finite-volume convention

\[
  \mathrm{Pe}_i=\frac{|f_i|h_i}{2D_{ii}}.
\]

For the default `D=I/2`, this reduces to `|f_i|h_i`. At the initial mean
`(1,1,20)`, `f=(0,7,-52.333...)`:

| Mesh | spacings | directional Pe at initial mean |
|---|---|---|
| Q1 `30x36x36` | `(2,2.222,2.222)` | `(0,15.56,116.30)` |
| Q2 `20x24x24` | `(3,3.333,3.333)` | `(0,23.33,174.44)` |

Over the entire current box, componentwise drift maxima are
`(700,1300,1386.67)`, giving Q1 worst-case directional values
`(1400,2888.9,3081.5)`. These are conservative box maxima where density may be
tiny, rather than distribution-weighted typical values. They still show that
diffusion-dominated asymptotics are irrelevant on the present grids.

First-order upwind adds a modified-equation diffusivity of order `|f_i|h_i/2`.
At the initial mean in `z`, this is about 58, compared with physical `D_zz=0.5`.
That calculation supports the numerical-diffusion hypothesis but does not prove
that the multidimensional DG covariance error equals this local estimate.

Formal order is therefore a weak ranking criterion. A credible method needs
pre-asymptotic layer tests at comparable Péclet numbers, positivity and moment
checks under narrow/skewed/multimodal inputs, and mesh refinement that reaches an
observable plateau. FCDF has the most explicit uniform-Péclet claim, but only for
its recent 1-D directional theorem. The current project supplies the only direct
3-D Lorenz high-Péclet comparison and it fails the covariance gate.

## 15. Time integration

| Method | Relevant property | Decision here |
|---|---|---|
| Backward Euler | first order, L-stable; positive when paired with an inverse-positive/M-matrix spatial system | retain for the controlled comparison; matrix reuse and robustness are valuable |
| Crank–Nicolson | second order and A-stable; non-L-stable and can create negative/oscillatory stiff modes | insufficient as a positivity upgrade; the project coarse test changed old `E_P` only about `0.614 -> 0.602` |
| BDF2 | second order and A-stable; no unconditional monotonicity in the ordinary form | future candidate only with a proved bound-preserving realization |
| SSP Runge–Kutta | preserves convex forward-Euler bounds under inherited CFL | diffusion CFL is expensive in 3-D; useful for theorem-faithful explicit DG/FV tests |
| IMEX/semi-implicit | can isolate stiff diffusion and reuse matrices | positivity is split- and flux-specific; Liu et al.'s theorem does not cover the current fully implicit operator |
| Directional/ADI splitting | low cost for aligned diagonal operators | mixed diffusion and boundary closures introduce commutator and positivity restrictions |

Time order is not the next variable to change. The recommended experiment fixes
the same backward-Euler timestep for Q1 and Q2, then requires a timestep halving
before any method is promoted.

## 16. Boundary and validation architecture

Reflecting total flux is defensible as the current conservative baseline. The
manufactured test verifies its implementation, and the startup density is
negligible near the box boundary. Evidence for mature posteriors is absent.
Absorbing truncation would deliberately lose probability; a far-field/open
condition is difficult to make conservative; whole-space Hermite avoids the
boundary but introduces spectral positivity issues. The next certification stage
must compare the current box with an expanded box on mature states. No boundary
change is justified before that measurement.

Monte Carlo is adequate for the present covariance discrimination: Q1 error
`0.0856` is 13.6 times the p95 sampling floor, and common-noise timestep error is
smaller still. It is inadequate as a precise full-density truth at 200,000 paths.
Five 40,000-particle subhistograms differ from the full histogram by TV about
`0.119–0.122`; Gaussian-filtered L1 changes strongly with bandwidth. If a future
deterministic method reaches covariance differences near `0.006`, increase paths
and pair with the Hermite/deterministic hierarchy rather than declaring a winner
from MC alone.

### DA and neural-operator consequences

Mature Bayesian inputs are a harder distribution than the startup Gaussian:
narrow and anisotropic peaks raise resolution demands; skewness and multiple
modes stress a global Hermite basis; extensive near-zero regions are precisely
where relative scaling corrections and incomplete positivity certificates are
most troublesome. A monotone low-order core can remain stable on these states
while still smearing covariance and separate modes. Every surviving production
candidate must therefore be tested on regenerated post-burn-in posterior states,
with mass, raw moments, covariance eigensystems, marginals, full-density error and
correction size reported separately. Cartesian tensor convenience for ML export
does not enter the method ranking; conservative projection to the training grid
is a later operation.

## 17. Historical hypothesis state before the executed Q2 experiments

The table below records the pre-experiment hypotheses. Sections 20--23 provide
their current disposition: the controlled same-mesh result refutes the apparent
Q2 inferiority, unlimited Crank--Nicolson passes the temporal gates, and the
current global positivity correction fails to preserve that result.

| Hypothesis | Attempted falsification | Verdict |
|---|---|---|
| A. Q1 is robust but too diffusive | Boundary/mass tests support structural robustness. Same-law MC, eigenvalue overdispersion, high Pe and FV refinement support excess diffusion. BE, upwind, mesh and limiter were not separately isolated. | **Supported numerical inference; mechanism not proved.** |
| B. Q2 is accurate but positivity destroys it | Unlimited projection preserves moments almost exactly; Stage 2 dominates corrections. Existing forecast uses wider cells and twice `dt`, so it cannot isolate Q2. | **Survives, underdetermined.** |
| C. Fixed Bernstein is too conservative | Bernstein theory proves false alarms are possible; 2x subdivision improved Q2 over the older whole-cell certificate. True initial negative mass shows some alarms are genuine. | **Partly supported; material impact unresolved.** |
| D. Paper-faithful optimization + scaling is sufficiently nonintrusive | Stage 1 is already nearly inactive; current stronger whole-cell scaling is intrusive. Paper scaling constrains only a finite point set, with lower-D evidence and a different operator. | **Falsified for the tested whole-cell variant; paper-faithful finite-point claim remains untested and would weaken positivity scope.** |
| E. Positivity belongs in flux/operator | AFC, M-matrix and local-flux literature supports the architecture. No direct 3-D Lorenz/full-SPD covariance evidence was found. | **Plausible, not established; leading fallback.** |
| F. A different FPE method wins | SG-DDFV is structurally strong but effectively 2-D in published construction/tests; diagonal methods miss full SPD; Hermite lacks positivity; characteristics have boundary gaps. | **No winner established. Hermite wins only the future independent-reference role.** |

## 18. Executed experiment specification (historical predeclaration)

This was the predeclared next experiment. It has been executed and is reported
in Sections 20--23; it is retained here to preserve the decision rules fixed
before results were known.

### Objective

Determine whether Q2's failure is intrinsic to its propagation or caused mainly
by the comparison and positivity treatment. This is the highest-information
small experiment because it decides whether to retain or terminate the existing
high-order branch before a substantially larger AFC/FV implementation.

### Fixed configuration

- domain, Lorenz parameters and `D=I/2`: unchanged;
- physical mesh: `30x36x36` for both Q1 and Q2;
- timestep: `0.000625`; final time: `0.05`;
- initial density: the same already-positive limited Q1 polynomial embedded
  exactly into Q2 on the same mesh, avoiding a Q2-initial-projection confound;
- reference: at least 200,000 exact-native-law MC paths with the existing
  bootstrap and common-random-number timestep check;
- quadrature: degree 14 or higher, with a recorded convergence check;
- run Q1 baseline, Q2 with current fixed-subcell scaling, and Q2 with the
  certificate-gated branch. Raw Q2 coefficients are saved before each correction.

### New diagnostic/certificate gate

For each raw Q2 cell, adaptive tensor-Bernstein branch-and-bound reports exactly
one status:

1. `CERTIFIED_NONNEGATIVE`: all leaf lower bounds are non-negative;
2. `WITNESSED_NEGATIVE`: a reproducible point evaluation is below a
   scale-aware negative tolerance;
3. `UNRESOLVED`: maximum depth or enclosure tolerance is reached.

Record depth, lower/upper bounds, witness value, cell mass, high-order quadrature
estimate of negative mass, and raw/corrected mass, mean, second raw moment,
covariance and L1/L2 change. Keep Stage-1 and Stage-2 changes separate. For the
certificate-gated propagation, skip scaling only for
`CERTIFIED_NONNEGATIVE`; use the existing conservative correction for the other
two statuses. This preserves the current whole-cell guarantee without treating a
negative coefficient as proof of negativity.

### Predeclared decision rule

Advance Q2 to local/operator-level positivity development only if all of the
following hold:

- same-mesh Q2 raw propagation improves normalized covariance and all three
  marginal TVs over Q1;
- certificate gating reduces forecast limiter relative L1 to mean `<=0.001`
  and maximum `<=0.005`;
- corrected Q2 reaches `E_P<=0.03` and `E_P/MC_p95<=5`;
- mass and whole-cell non-negativity remain within existing tolerances;
- a timestep-halving check changes `E_P<=0.003` and L1 `<=0.0025`;
- wall time and peak memory are recorded, without using equal DOFs as a proxy for
  cost.

If raw Q2 beats Q1 but corrected Q2 fails only the limiter gates, implement a
local conservative flux-correction/AFC prototype next. If raw Q2 itself fails,
close the postprocessed Q2 branch and prototype a full-SPD positive flux/FV
method. If most cells are `UNRESOLVED`, adaptive Bernstein is rejected as the
production decision procedure even if it remains useful diagnostically.

No mature-data run or large dataset should precede this gate.

## 19. Historical pre-experiment ranking and remaining uncertainty

This ranking predates the executed same-mesh and Crank--Nicolson comparisons.
The current ranking and next action are stated in the opening Decision and
Sections 22--23.

| Rank for next research | Method/path | Reason |
|---:|---|---|
| 1 | Same-mesh Q2 falsification with rigorous positivity audit | directly resolves three current confounds at modest implementation cost |
| 2 | Local/AFC correction around a high-order conservative operator | best architecture-level route for 3-D/full SPD if raw Q2 is accurate |
| 3 | Positive full-tensor FV/SG-DDFV challenger | strongest structural alternative, but 3-D convection implementation and evidence gap are large |
| 4 | Dynamically scaled whole-space Hermite reference | independent, high-order and boundary-free; positivity limits production use |
| 5 | Directional FCDF/complete flux | high value only after diagonal-noise scope is fixed; current 1-D/2-D and maturity gaps are decisive |
| 6 | Conservative characteristics | strong transport rationale, weak boundary/positivity fit for this box |

Adaptivity follows base-method selection. Covariance can be targeted through its
raw moment functionals, and anisotropic/nonuniform refinement should eventually
reduce wasted tail cells. The installed DOLFINx 0.11 hexahedral refinement path
does not support the required local refinement, so immediate adaptivity would
also change topology, positivity certification and export format.[^22]

Remaining uncertainty is dominated by absent mature-posterior validation, lack
of a converged deterministic density reference, and lack of a positive
low-order comparator or directly applicable 3-D/full-SPD/high-Péclet positivity
theorem for a local correction of the accurate Q2--Crank--Nicolson path.
These are decision-relevant unknowns rather than implementation details.

## 20. Same-mesh Q2 experiment result (2026-09-11)

**Superseded evidence notice.** A subsequent invariant audit found that the
Stage-1 floating-point mass repair could make tiny active cell averages
negative and produce Stage-2 scaling factors outside `[0,1]`. The values below
are preserved as diagnostic history and cannot support a method decision until
the predeclared corrected run reproduces or revises them.

The predeclared experiment has now been executed. On `30x36x36` with
`dt=0.000625`, corrected Q1 gave covariance error `0.08719`, fixed-subcell Q2
gave `0.03483`, and adaptive-certificate Q2 gave `0.02377`. Adaptive Q2 also
improved all three physical-cell marginal TVs to
`(0.00481, 0.00186, 0.00327)` and reduced limiter relative L1 mean/max to
`0.000606/0.004127`. Thus the earlier equal-DOF Q2 rejection was confounded:
Q2 is materially better on the same physical mesh, and adaptive certification
is materially less damaging than fixed-subcell scaling.

The production decision remains `INSUFFICIENT_EVIDENCE`. At half timestep,
covariance error changed by only `0.00159`, passing that gate, while the
conservative three-subcell density changed by `L1=0.01552`. Jensen's inequality
makes this a lower bound on the full polynomial L1 difference, already more than
six times the `0.0025` gate. Half-step mass drift was `2.56e-10`, above the
`1e-10` gate. The next controlled diagnostic is unlimited Q2 at both timesteps:
raw pre-correction states from a limited trajectory inherit earlier limiter
changes and cannot distinguish backward-Euler/DG sensitivity from accumulated
postprocessing.

Evidence: [`same_mesh_q2_falsification_report.json`](same_mesh_q2_falsification_report.json)
and the hashed immutable run paths recorded there.

## 21. Corrected rerun and unlimited attribution (2026-09-11)

The bound-preserving Stage-1 repair and clamped Stage-2 factor were rerun under
the same mesh, initial law, Monte Carlo sample, timesteps and gates. Every
recorded corrected cell average was non-negative and every scaling factor lay
in `[0,1]`. The earlier branch values were reproduced to roundoff: adaptive Q2
gave covariance errors `0.02377` and `0.02218`, while its timestep-halving
subcell-average difference remained `L1>=0.01552` and half-step mass error
remained `2.56e-10`. The failed method decision is therefore robust to the
formal limiter repair.

The two genuinely unlimited backward-Euler Q2 trajectories gave covariance
errors `0.00727` and `0.00464`, but terminal integrated negative masses
`7.23e-4` and `7.73e-4`. Their timestep-halving density difference was
`L1>=0.00541`, above the `0.0025` limit, while covariance-error change `0.00262`
passed. Positivity correction increases the corrected cross-timestep difference
by a factor of about `2.87`; the unlimited failure shows that accumulated
limiting does not fully explain the sensitivity. The next discriminator is an
unlimited Crank--Nicolson pair under unchanged density and covariance gates.

Evidence: [`same_mesh_q2_corrected_report.json`](same_mesh_q2_corrected_report.json)
and [`unlimited_q2_timestep_report.json`](unlimited_q2_timestep_report.json).

## 22. Unlimited Crank--Nicolson temporal diagnostic (2026-09-11)

At `theta=0.5`, the unlimited Q2 full- and half-step covariance errors are
`0.003711` and `0.003706`. Their conservative subcell density difference is
only `L1>=4.19e-5`, and covariance-error change is `4.74e-6`; both predeclared
temporal gates pass by wide margins. Integrated negative mass remains about
`8.28e-4`, so the raw method remains unsuitable for target generation. This
evidence retains the Q2 spatial branch and focuses the next comparison on
whether positivity correction preserves Crank--Nicolson consistency.

Evidence: [`unlimited_q2_crank_nicolson_report.json`](unlimited_q2_crank_nicolson_report.json).

## 23. Corrected Crank--Nicolson comparator (2026-09-11)

The current adaptive global limiter does not preserve the unlimited temporal
result. Full- and half-step corrected covariance errors are `0.02192` and
`0.02263`, while the conservative density difference is `L1>=0.01088`, above
the `0.0025` gate. Full-step mass error is `1.27e-10`, slightly above the
`1e-10` gate. Positivity and limiter-impact gates pass, and all repaired limiter
invariants hold. The evidence rejects global completed-polynomial scaling for
the Crank--Nicolson production path and sets a quantitative target for a local
conservative correction.

Convex limiting supplies a general local-correction architecture when a
positive low-order update and conservative pairwise antidiffusive increments
are available,[^23] and recent DDG Fokker--Planck work applies local correction
to diffusive fluxes.[^24] Their proved settings differ from the present
full-SPD SIPG Lorenz operator and Crank--Nicolson time step. They motivate the
next derivation without certifying it.

Evidence: [`corrected_q2_crank_nicolson_report.json`](corrected_q2_crank_nicolson_report.json).

## 24. Local-QP specialization and dynamic decision (2026-09-11)

The cell-average equality was eliminated in a fixed null-space basis, reducing
each Q2 correction from 27 coefficients plus an equality to 26 variables with
125 distinct fixed Bernstein inequalities. OSQP updates only the cell-dependent
lower bound and reuses its factorization. On 1,413 saved terminal problems and
1,000 deterministic random stress problems, OSQP solved all 2,413 cases.[^25] It
preserved the normalized average to `6.67e-16`, had no feasibility or
scalar-objective-bound violation, agreed with successful SLSQP objectives to
`3.76e-10` relative, and was `12.51` times faster. SLSQP failed in 28 cases;
those failures are oracle limitations rather than evidence against OSQP because
every specialised result independently passed the primal and objective checks.

The production-mesh three-step profile reduced mean projection time from
`16.65 s` with SLSQP to `1.54 s` with OSQP, passing the predeclared 10x
engineering gate. The subsequent 80-, 160-, and 320-step branches completed in
`205.8`, `494.5`, and `1076.3 s`.

All 560 corrected steps were whole-cell Bernstein-certified, had zero measured
negative mass, no optimizer failure or scalar fallback, and maximum
projection-induced mass change `7.99e-15`. Covariance errors were `0.007509`,
`0.007488`, and `0.007516`, each below `1.5` times the common bootstrap p95.
The full/half and half/quarter conservative subcell differences were
`5.238e-4` and `5.418e-4`, both below `0.0025`. Their ratio is `0.9668`, giving
observed order `-0.0488`; the required positive-order gate fails. Absolute final
mass errors were `1.25e-10`, `1.75e-11`, and `2.75e-10`, so the full and quarter
levels also fail the `1e-10` gate. The correction itself preserves incoming
mass, indicating that the latter failure is accumulated linear-solve drift,
but that attribution does not waive the gate.

This is a mixed scientific result: local QP is far less destructive than global
scaling and retains useful non-negative accuracy, while the tested timestep
sequence shows a roughly `5.3e-4` density-difference floor rather than positive
temporal convergence. It remains a comparator and does not advance to dataset
certification. Because its mean correction is approximately proportional to the
timestep and it improves the global-scaling density discrepancy by about 20.8
times, one further full/half/quarter/eighth diagnostic is predeclared with KSP
`rtol=1e-12`, `atol=1e-15`. A decrease in the final adjacent difference advances
only to spatial/full-SPD testing; another plateau prioritizes adaptive
constraints or an operator-level positive low-order/AFC correction.

Evidence: [`local_q2_optimizer_validation_report.json`](local_q2_optimizer_validation_report.json),
[`local_q2_projection_performance_report.json`](local_q2_projection_performance_report.json),
and [`local_q2_dynamic_projection_report.json`](local_q2_dynamic_projection_report.json).

## 25. Tight four-level decision and spatial promotion (2026-09-12)

The predeclared tight-KSP full/half/quarter/eighth run completed at
`30x36x36`. Its adjacent conservative density differences are `5.238e-4`,
`5.418e-4`, and `1.620e-4`. The first consecutive order remains `-0.0488`,
while the decisive final order is `1.741`. This is evidence of a decreasing
fine-level temporal difference, not a proof of asymptotic second-order
convergence.

All 1,200 completed timesteps are whole-cell Bernstein-certified. Measured
negative mass, optimizer failures and scalar fallbacks are zero. Maximum
projection-induced mass change is `9.11e-15`, and the largest terminal absolute
mass error is `1.87e-11`. Covariance discrepancies remain between `0.007488`
and `0.007519`. Every predeclared dynamic gate passes, so the project status is
promoted to `TEMPORAL_POSITIVITY_CERTIFIED`; large dataset generation remains
unauthorized.

The next experiment is predeclared in
`experiments/local-q2-cn-spatial-refinement.yaml`. It holds Q2 DG,
Crank--Nicolson, the local QP, OSQP tolerances, Bernstein certificate, domain,
noise and boundary treatment fixed. The mesh sequence is `20x24x24`,
`30x36x36`, and `45x54x54`, with constant refinement ratio `3/2` and
`dt=1.5625e-4`. Each mesh independently projects the same continuous finite-box
Gaussian. Exact polynomial averages use 9, 6, and 4 subvoxels per physical cell
axis so every final density is compared on the same `180x216x216` grid without
interpolation.

The primary spatial gates require the second mesh-pair L1 difference to be
smaller than the first and the observed constant-ratio spatial order to be
positive. Positivity, mass and optimizer invariants apply at every mesh. If the
finest spatial difference is below `8.1e-4`, the two finest meshes must be
repeated at `dt=7.8125e-5` before interpreting spatial order. A passing spatial
study advances the candidate to full-SPD and mature-state testing.

Evidence: [`local_q2_tight_refinement_report.json`](local_q2_tight_refinement_report.json)
and immutable run
`runs/local-q2-cn-tight-ksp-refinement/20260912T003213Z`.

## 26. Identity-noise spatial decision and full-SPD predeclaration (2026-09-13)

The frozen candidate completed the predeclared `20x24x24`, `30x36x36`, and
`45x54x54` spatial hierarchy at `dt=1.5625e-4`. Exact conservative comparisons
on the common `180x216x216` grid give L1 differences `0.141394` and `0.0355845`.
Their ratio yields observed spatial rate `3.4026`. This is an observed
common-grid rate; it is neither a proved formal order nor proof that the meshes
are asymptotic.

All 960 completed steps are whole-cell Bernstein-certified. Measured negative
mass, optimizer failures and scalar fallbacks are zero, and maximum terminal
absolute mass error is `1.20e-11`. Covariance discrepancies decrease from
`0.03033` to `0.005209` to `0.002340`. The finest discrepancy lies below the
200,000-path bootstrap p95 `0.006491`, so the current reference cannot resolve
further covariance improvement. Deterministic mesh-to-mesh L1 differences
remain the primary convergence evidence.

The method status is promoted to `SPATIAL_POSITIVITY_CERTIFIED`; dataset
generation remains unauthorized. The next required gate is
`FULL_SPD_DIFFUSION`. The predeclared tensor and factor are

\[
D=\begin{pmatrix}1&0.4&0.2\\0.4&1&0.3\\0.2&0.3&1\end{pmatrix},
\qquad D=\tfrac12BB^T,
\]

with eigenvalues approximately `(0.581212, 0.811321, 1.607467)`. First run the
frozen method at `30x36x36`; a pass authorizes the complete spatial hierarchy
under the same tensor. The strengthened common reference uses one million
particles, 1,000 bootstrap replicates and fixed bootstrap seed `20261910`.
Predeclared gates cover every-step positivity, mass, optimizer/fallback counts,
fixed covariance and correlation thresholds, correction strength, decreasing
common-grid L1 differences and positive spatial order.

The controlled `30x36x36` branch has now completed and passes all fixed gates.
Normalized covariance error is `0.004163`; maximum absolute off-diagonal
covariance and correlation errors are `0.003806` and `0.007067`; mean and
maximum relative L1 corrections are `7.61e-5` and `9.66e-4`. All 320 steps are
whole-cell certified, measured negative mass is zero, final mass error is
`3.86e-12`, and optimizer failures and fallbacks are zero. This result activates
the already-predeclared full-SPD spatial hierarchy while leaving dataset
generation unauthorized.

Evidence: [`local_q2_spatial_refinement_report.json`](local_q2_spatial_refinement_report.json),
[`local_q2_full_spd_control_report.json`](local_q2_full_spd_control_report.json),
immutable run `runs/local-q2-cn-spatial-refinement/20260912T194930Z`, and
configurations [`experiments/local-q2-cn-full-spd-controlled.yaml`](experiments/local-q2-cn-full-spd-controlled.yaml)
and [`experiments/local-q2-cn-full-spd-spatial-refinement.yaml`](experiments/local-q2-cn-full-spd-spatial-refinement.yaml).

## 27. Full-SPD spatial certification (2026-09-13)

The conditional non-diagonal full-SPD hierarchy completed successfully on
`20x24x24`, `30x36x36`, and `45x54x54`. Conservative common-grid L1 differences
are `0.139500` and `0.0348401`. Their ratio gives observed spatial rate `3.4215`.
This is a common-grid numerical rate, without a formal-order or asymptotic-regime
claim.

All 960 steps are whole-cell Bernstein-certified. Measured negative mass,
optimizer failures and scalar fallbacks are zero; maximum absolute mass error is
`3.87e-12`. Normalized covariance discrepancies are `0.02879`, `0.004163`, and
`0.002261`. The finest value is below the strengthened one-million-particle
bootstrap p95 `0.002735`. Maximum off-diagonal correlation error decreases from
`0.0551` to `0.00707` to `0.00178`; all fixed covariance, correlation and
correction-strength gates pass. Total branch forecast time is `4,817 s` across
8,881,349 local optimizer invocations.

The method status advances to `FULL_SPD_DIFFUSION_CERTIFIED`; dataset generation
remains unauthorized. The next required gate is `MATURE_STATE`, using one common
conservatively projected later-time or post-analysis Lorenz density and measuring
spatial/temporal differences, covariance, marginal TVs, correction norms,
negative-average and projected probability mass, projected-cell counts,
optimizer performance and conservation. Domain-size sensitivity follows a
mature-state pass.

The frozen first case is an ambiguous bimodal posterior. An independent
full-SPD stochastic ensemble is spun up, fitted by a symmetry-preserving
16-component Gaussian mixture and conditioned analytically with a z-only
likelihood. The same mixture is projected into all three meshes. The run also
records initial projection error, smoothed joint-density TV on a fixed grid and
positive/negative-x lobe probabilities. A pass requires decreasing deterministic
mesh differences and mean QP corrections, in addition to the established mass,
positivity, optimizer and distributional gates.

Evidence: [`local_q2_full_spd_spatial_report.json`](local_q2_full_spd_spatial_report.json)
and immutable run
`runs/local-q2-cn-full-spd-spatial-refinement/20260913T135455Z`.

## Sources

[^1]: C. Liu, J. Hu, W. T. Taitano and X. Zhang, [“An optimization-based positivity-preserving limiter in semi-implicit discontinuous Galerkin schemes solving Fokker–Planck equations”](https://www.math.purdue.edu/~zhan1966/research/paper/DG_anisotropic_Fokker_Planck.pdf), *Computers & Mathematics with Applications* (2025).
[^2]: X. Zhang and C.-W. Shu, [“On maximum-principle-satisfying high order schemes for scalar conservation laws”](https://doi.org/10.1016/j.jcp.2009.12.030), *Journal of Computational Physics* 229 (2010), 3091–3120.
[^3]: S. Srinivasan, J. Poggie and X. Zhang, [“A positivity-preserving high order discontinuous Galerkin scheme for convection–diffusion equations”](https://www.math.purdue.edu/~zhan1966/research/paper/conffusion3.pdf), *Journal of Computational Physics* 366 (2018), 120–143.
[^4]: H. Liu and H. Yu, [“Maximum-principle-satisfying third order discontinuous Galerkin schemes for Fokker–Planck equations”](https://doi.org/10.1137/130935161), *SIAM Journal on Scientific Computing* 36 (2014), A2296–A2325.
[^5]: X. Li and X. Zhang, [“On the monotonicity and discrete maximum principle of the finite difference implementation of C0-Q2 finite element method”](https://www.math.purdue.edu/~zhan1966/research/paper/Q2FEM_DMP.pdf), and G. Cross and X. Zhang, [“On the monotonicity of Q3 spectral element method for Laplacian on quasi-uniform rectangular meshes”](https://arxiv.org/abs/2010.07282).
[^6]: H. Liu, Y. Gao and X. Zhang, [“A high order finite difference method for irreversible Fokker–Planck equations”](https://yuangaogao.github.io/LGZ2024-JSC.pdf), *Journal of Scientific Computing* (2024).
[^7]: D. Kuzmin and S. Turek, [“Flux correction tools for finite elements”](https://doi.org/10.1006/jcph.2001.6955), *Journal of Computational Physics* 175 (2002), 525–558; D. Kuzmin, [“Multidimensional FEM-FCT schemes for arbitrary time stepping”](https://doi.org/10.1002/fld.493), *International Journal for Numerical Methods in Fluids* 42 (2003), 265–295.
[^8]: G. R. Barrenechea, V. John and P. Knobloch, [“A unified analysis of algebraic flux correction schemes for convection–diffusion equations”](https://doi.org/10.1007/s40324-018-0160-6), *SeMA Journal* 75 (2018), 655–685.
[^9]: M. Shariati, E. W. Weber and D. Höche, [parallel Poisson–Nernst–Planck AFC implementation](https://github.com/mrshariati/FEMCorrosionSimulation) associated with *Finite Elements in Analysis and Design* 202 (2022), 103734.
[^10]: J. S. Chang and G. Cooper, [“A practical difference scheme for Fokker–Planck equations”](https://doi.org/10.1016/0021-9991(70)90001-X), *Journal of Computational Physics* 6 (1970), 1–16; N. Loy and M. Zanella, [“Structure preserving schemes for Fokker–Planck equations with nonconstant diffusion matrices”](https://arxiv.org/abs/1905.02970), *Mathematics and Computers in Simulation* 188 (2021), 342–362, an exclusively two-dimensional full-matrix construction.
[^11]: E.-H. Quenjel, [“Positive Scharfetter–Gummel finite volume method for convection–diffusion equations on polygonal meshes”](https://doi.org/10.1016/j.amc.2022.127071), *Applied Mathematics and Computation* 425 (2022), 127071.
[^12]: B. Lan et al., [“The cell-centered positivity-preserving finite volume scheme for 3D anisotropic diffusion problems on distorted meshes”](https://doi.org/10.1016/j.cpc.2021.108099), *Computer Physics Communications* 269 (2021), 108099.
[^13]: A. Itkin, [“Diagonal Frog: high-order positivity-preserving FD schemes for anisotropic Fokker–Planck equations”](https://arxiv.org/abs/2606.23980), arXiv:2606.23980 (2026); A. Itkin and R. Kazbek, [“Diagonal Frog meets ADI”](https://arxiv.org/abs/2608.22703), arXiv:2608.22703 (2026).
[^14]: A. Itkin, [“Flux-Corrected Diagonal Frog: second order and positivity at all time steps”](https://arxiv.org/abs/2607.20415), arXiv:2607.20415 (2026).
[^15]: J. C. M. Fok, B. Guo and T. Tang, [“Combined Hermite spectral–finite difference method for the Fokker–Planck equation”](https://www.math.hkbu.edu.hk/~ttang/Papers/FokGuoT.pdf), *Mathematics of Computation* 71 (2002), 1497–1528.
[^16]: H. Ma, W. Sun and T. Tang, [“Hermite spectral methods with a time-dependent scaling for parabolic equations in unbounded domains”](https://doi.org/10.1137/S0036142903421278), *SIAM Journal on Numerical Analysis* 43 (2005), 58–75; [adaptive multidimensional Hermite analysis](https://arxiv.org/abs/2203.15630).
[^17]: T. Futai et al., [“A mass-preserving two-step Lagrange–Galerkin scheme for convection–diffusion problems”](https://doi.org/10.1007/s10915-022-01885-w), *Journal of Scientific Computing* 92 (2022).
[^18]: S. Ding, S. Tan and Y. Zhang, [“High order semi-Lagrangian discontinuous Galerkin method coupled with local discontinuous Galerkin method for convection–diffusion problems”](https://arxiv.org/abs/1907.06117), arXiv:1907.06117.
[^19]: F. Boudaoud, F. Caruso and M.-F. Roy, [“Certificates of positivity in the Bernstein basis”](https://doi.org/10.1007/s00454-007-9042-x), *Discrete & Computational Geometry* 39 (2008), 639–655; R. Leroy, [“Certificates of positivity in the simplicial Bernstein basis”](https://hal.science/hal-00589945/document), with convergence under degree elevation/subdivision for strictly positive polynomials.
[^20]: C. Sloth, [“Nonnegative polynomial with no certificate of nonnegativity in the simplicial Bernstein basis”](https://arxiv.org/abs/1710.05735), arXiv:1710.05735.
[^21]: A. Allawala and J. B. Marston, [“Statistics of the stochastically-forced Lorenz attractor by the Fokker–Planck equation and cumulant expansions”](https://arxiv.org/abs/1604.00867), *Physical Review E* 94 (2016), 052218.
[^22]: [DOLFINx 0.11 mesh API](https://docs.fenicsproject.org/dolfinx/v0.11.0.post0/python/generated/dolfinx.mesh.html); the local hexahedral refinement probe fails with `RuntimeError: Refinement only defined for simplices`.
[^23]: J.-L. Guermond, B. Popov and I. Tomas, [“Invariant domain preserving discretization-independent schemes and convex limiting for hyperbolic systems”](https://doi.org/10.1016/j.cma.2018.11.036), *Computer Methods in Applied Mechanics and Engineering* 347 (2019), 143–175.
[^24]: J. A. Carrillo, H. Liu and H. Yu, [“Positivity-preserving and energy-dissipating discontinuous Galerkin methods for nonlinear nonlocal Fokker–Planck equations”](https://arxiv.org/abs/2403.15643), *Communications in Applied and Industrial Mathematics* 16 (2025), 19–40.
[^25]: B. Stellato, G. Banjac, P. Goulart, A. Bemporad and S. Boyd, [“OSQP: an operator splitting solver for quadratic programs”](https://doi.org/10.1007/s12532-020-00179-2), *Mathematical Programming Computation* 12 (2020), 637–672.
