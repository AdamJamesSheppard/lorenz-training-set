# Lorenz-63 Fokker–Planck numerical-method selection

Date: 2026-09-09  
Scope: density-to-density forecasts inside sequential Bayesian data assimilation  
Machine-readable companion: [`method_selection_report.json`](method_selection_report.json)

## Final decision

**INSUFFICIENT_EVIDENCE**

Recommended production forecast generator: No method is certified. The strongest tested interim baseline is corrected Q1 upwind/SIPG with backward Euler, quadrature-14 L2 initialization, projected Bayesian analysis, and conservative positivity postprocessing.  
Recommended independent validator: exact-native-law Monte Carlo with at least 200,000 paths, bootstrap uncertainty and common-random-number timestep refinement, triangulated with the independent refined finite-volume hierarchy.  
Recommended representation for neural-operator targets: for a pilot only, float64 exact conservative subcell averages; Q1 needs two subcells per native cell per axis.  
Expected covariance error: the best measured short-startup result is `E_cov=0.08558`; corrected mature-state error at this resolution is unknown.  
Expected full-density error: not certified; Q1 and the finest independent FV result differ by `L1=0.15390`.  
Expected cost per DA forecast: `86.9 s` serial for one Q1 `30x36x36`, `Delta t=0.05` forecast; approximately `26.4 s` for step work on eight ranks, excluding non-scaling diagnostics/output.  
Principal remaining limitation: no corrected mature-posterior forecast has been validated at a production-like resolution, and the available coarse regenerated DA ensemble requires severe forecast and analysis limiting.

Should a large neural-operator training dataset be generated now?

**NO**

The best corrected Q1 covariance discrepancy is 13.6 times the 200,000-path MC noise floor. Q2 is worse at equal DOFs, the deterministic reference is not converged, and the corrected mature ensemble is under-resolved. A large dataset would encode known numerical artifacts.

## 1. PDE classification

For constant `B`, `D=BB^T/2` and

```text
p_t + div(f p - D grad p) = 0.
```

This is linear in `p`, transient, conservative, second order, variable-coefficient through `f(x)`, generally non-self-adjoint, potentially strongly convection dominated, and irreversible/non-gradient. If `B` is full rank, `D` is positive definite and the equation is uniformly parabolic on the bounded box. If `B` is rank deficient, it is degenerate parabolic; it is hypoelliptic only if an appropriate Hörmander/bracket condition holds. Uniform-elliptic arguments cannot be transferred automatically.

For Lorenz-63,

```text
div f = d_x[sigma(y-x)] + d_y[x(rho-z)-y] + d_z[xy-beta z]
      = -sigma - 1 - beta
      = -41/3.
```

Consequently the expanded equation is

```text
p_t + f.grad(p) - (41/3) p = div(D grad p).
```

The negative divergence represents phase-volume contraction: along a drift characteristic, density is amplified by compression in the absence of diffusion. The conservative form is therefore essential; treating it as divergence-free advection solves a different PDE.

The physical SDE is posed on `R^3`. The implemented box and total reflecting condition `(f p-D grad p).n=0` are a separate truncation approximation.

## 2. Original Q1/SIPG audit

The FEniCS book was used for variational theory—not current APIs. Its L2-projection example formulates `(p_h,v_h)=(p,v_h)`; its DG advection-diffusion chapter gives cellwise upwinding, interior-penalty diffusion and theta time integration; its verification chapters warn that convergence claims require an independent exact-enough reference. Current implementation calls were checked against the installed FEniCSx 0.11 stack and the [current FEniCSx documentation](https://docs.fenicsproject.org/).

Let `n=n+` on an interior facet and `beta_n=f.n`. The code represents

```text
a_adv(p,v) = - sum_K integral_K f p . grad(v)
             + sum_F integral_F beta_n p_up (v+ - v-),

p_up = p+ when beta_n >= 0, otherwise p-.
```

For constant symmetric `D`, it represents SIPG

```text
a_diff(p,v) = sum_K integral_K D grad(p).grad(v)
 - sum_F integral_F avg(D grad(p)).jump(v n)
 - sum_F integral_F avg(D grad(v)).jump(p n)
 + sum_F integral_F eta k^2 avg(n.D.n)/avg(h) jump(p n).jump(v n).
```

Backward Euler uses `(M+dt A)p^(n+1)=M p^n`; the experimental theta path uses the corresponding old-state spatial term. With `v=1`, all volume gradients and interior jumps vanish, establishing discrete mass conservation before the limiter.

The physical boundary derivation must be done before splitting advection and diffusion. Cellwise integration produces the single exterior term

```text
integral_boundary (f p-D grad p).n v.
```

The reflecting condition sets this *total* term to zero. The absence of exterior terms in the split UFL is consistent with that combined derivation; it does not assert separately that `f p.n=0` and `D grad(p).n=0`.

## 3. Initial-law validation repair

The confound was real:

- the original FEM branch used a normalized nodal Q1 interpolant;
- the original MC branch sampled the exact analytic whole-space Gaussian.

Those were different laws. The old discrepancy is now labelled **representation + propagation error**, not propagation error.

At `30x36x36`, against the finite-box-normalized analytic Gaussian:

| Initial representation | L1 | L2 | `E_cov(0)` | Minimum | Limiter relative L1 |
|---|---:|---:|---:|---:|---:|
| Nodal Q1 interpolation | 0.14135 | 0.006348 | 0.12619 | positive | 0 |
| L2 projection, unlimited | 0.05554 | 0.002282 | `5.10e-9` | `-4.91e-5` | n/a |
| L2 projection, limited | 0.05807 | 0.002323 | 0.006835 | roundoff | 0.01165 |

The projected cell-average entropy diagnostic is `6.8531`, versus `7.0516` for interpolation (the whole-space Gaussian entropy is `6.7417`; the diagnostic itself uses cell averages). L2 projection is much more accurate but is not positive. The limiter restores a whole-cell positivity guarantee and reintroduces measurable error.

Projection quadrature convergence at `12x16x16`, relative to degree 16, is:

| Quadrature degree | Relative coefficient difference |
|---:|---:|
| 4 | `1.065e-2` |
| 6 | `5.966e-4` |
| 8 | `2.271e-5` |
| 10 | `6.144e-7` |
| 12 | `1.276e-8` |
| 14 | `2.659e-10` |

Degree 14 is adopted for accuracy-sensitive initialization and analysis.

## 4. Corrected same-law Monte Carlo comparison

All branches now start from the identical limited native Q1 polynomial. Cells are selected by exact polynomial mass; within a selected cell, rejection sampling uses the largest Bernstein control coefficient as a rigorous envelope. This is exact sampling from the represented density, apart from pseudorandom sampling error.

For Q1 `30x36x36`, `dt=0.000625`, `t=0.05`, and 200,000 paths with MC `dt=0.000125`:

- `E_cov=0.08558`;
- bootstrap MC covariance noise p95 `=0.006282`;
- `R_cov=13.62`;
- limiter relative L1 mean/max `=0.003448/0.006292`;
- mean differences remain small, while covariance eigenvalues and principal directions show systematic over-diffusion.

A same-sample, common-Brownian MC refinement from `0.000125` to `0.0000625` changes normalized covariance by only `0.000111`. MC time discretization is not the cause of the Q1 discrepancy.

At `20x24x24`, the corrected propagation-only `E_cov` was `0.2604` from the limited L2 initial law. The old `0.219` fine result had mixed initialization and propagation; the corrected fine result is `0.0856`. Initialization was a major confound, but removing it does not certify Q1.

Evidence: [`validation_repair_report.json`](validation_repair_report.json), [`independent_reference_refined_report.json`](independent_reference_refined_report.json), [`mc_timestep_same_initial_law.json`](mc_timestep_same_initial_law.json).

## 5. Bayesian analysis audit

For nodal Lagrange DG, multiplying each coefficient by a likelihood evaluated at the matching DOF constructs the nodal interpolant `I_h[L p_h]`. Because `L p_h` is generally outside Q1, this is not an L2 projection.

The repaired update solves

```text
find q_h in V_h: integral q_h v_h = integral L p_h v_h  for all v_h,
p_h+ = q_h / integral q_h,
```

with degree-14 quadrature, followed by the conservative positivity limiter. Its mass matrix and symbolic likelihood form are cached across DA cycles.

The conjugate Gaussian `xz` observation test at Q1 `30x36x36` gives:

| Update | Mean error norm | L1 | L2 | `E_cov` | Analysis limiter L1 |
|---|---:|---:|---:|---:|---:|
| Nodal product | 0.07468 | 0.19361 | 0.01094 | 0.14494 | approximately 0 |
| L2-projected product | 0.002055 | 0.11554 | 0.006262 | 0.03706 | 0.05688 |

Projection substantially improves moments and density error on the fine Q1 mesh. However, a 5.69% limiter correction means the projected update is still not certified as an accurate production analysis operator. Coarse results are much worse.

Evidence: [`q1_fine_bayesian_update_report.json`](q1_fine_bayesian_update_report.json).

## 6. Boundary-flux manufactured solution

The mandatory test uses

```text
p = C exp(0.4x-0.3y+0.2z),  D=I/2,
f = D(0.4,-0.3,0.2) = (0.2,-0.15,0.1).
```

Then `f p` and `D grad p` have nonzero normal traces on appropriate faces, but `J=f p-D grad p=0` pointwise. Q1 results are:

| Cells/axis | L1 | L2 | L1 order | Mass error |
|---:|---:|---:|---:|---:|
| 4 | `1.446e-3` | `6.478e-4` | — | `2.53e-12` |
| 6 | `6.431e-4` | `2.882e-4` | 1.9992 | `3.40e-14` |
| 8 | `3.618e-4` | `1.621e-4` | 1.9997 | `3.11e-12` |
| 12 | `1.608e-4` | `7.207e-5` | 1.9997 | `4.44e-13` |

This validates the combined total-flux treatment for a nontrivial reflecting trace. It does not by itself bound whole-space truncation error for mature Lorenz densities.

Evidence: [`boundary_flux_report.json`](boundary_flux_report.json).

## 7. Positivity and Q2

Stage 1 projects cell averages onto the nonnegative, equal-global-mass set. For the present lower-only constraint, the KKT solution is `x_K=max(0,w_K-lambda)`; the scalar multiplier is found by bisection. Stage 2 scales the polynomial around its corrected average.

For Q1 on affine hexahedra, nonnegative vertex/Bernstein coefficients imply nonnegativity throughout the cell because tensor Q1 is a convex combination of its vertex values.

Ordinary Q2 nodal coefficient positivity has no such implication. The Q2/Q3 extension converts the polynomial to Bernstein coefficients on `2x2x2` control subcells and scales until all are nonnegative. Since every subcell Bernstein basis is nonnegative and partitions unity, this is a sufficient whole-cell guarantee. It is conservative but not necessary and can be intrusive.

Exact L2 projection into discontinuous Q2 preserves mass and first and second raw moments before positivity correction: `1`, `x_i`, `x_i x_j`, and `x_i^2` all belong to Q2 on affine tensor-product cells and can be chosen as projection test functions. With sufficiently converged quadrature, the measured unlimited Q2 covariance error was `2.84e-10`.

The limiter defeats that theoretical advantage in the tested Lorenz case. At equal 311,040 global DOFs:

| Method | Mesh | Same-law `E_cov` | Limiter L1 mean/max | Serial step | 8-rank step |
|---|---|---:|---:|---:|---:|
| Q1 | `30x36x36` | 0.08558 | 0.00345 / 0.00629 | 1.152 s | 0.330 s |
| Q2 | `20x24x24` | 0.25484 | 0.01238 / 0.02598 | 0.628 s | 0.282 s |

Q2 is faster per step because there are fewer cells, but its covariance is roughly three times worse. In the analytic Bayesian test, Q2 projected analysis has `E_cov=0.09347` and 9.88% limiter correction, versus Q1's `0.03706` and 5.69%. Q2 is not adopted. Q3 was not pursued after Q2 failed its priority comparison.

Evidence: [`higher_order_report.json`](higher_order_report.json), [`q2_common_law_subcell_monte_carlo.json`](q2_common_law_subcell_monte_carlo.json), [`q2_bayesian_update_subcell_report.json`](q2_bayesian_update_subcell_report.json).

## 8. Spatial/time convergence and limiter contribution

The older isolated constant-coefficient Q1 test gives fixed-time-step L1 orders `1.08` and `1.12` and L2 orders `0.94` and `0.90`. A smoother controlled study reaches approximately second-order L1 behavior on its finer Q1 levels, but Q2 is strongly pre-asymptotic and limiter-contaminated. These are convergence tests, not universal Lorenz error rates.

At fixed `12x16x16`, Lorenz backward-Euler self-comparison against `dt=0.0003125` changes L1 by `0.00228` and covariance Frobenius norm by `0.0170` at `dt=0.000625`. A fine-mesh normalized temporal error has not been measured, so this number is not promoted to a production bound.

On fine Q1 startup propagation, limiting occurs at every step; mean/max relative L1 corrections are `0.00345/0.00629`. This is not clipping: mass is conserved by Stage 1 and Stage 2. Nevertheless positivity does not imply accuracy, and the size of the correction is part of the error budget.

## 9. Independent deterministic reference

A separate NumPy finite-volume solver was implemented without UFL or the DG operator:

- cell-centred first-order upwind advective flux;
- centred diagonal diffusion;
- SSPRK(3,3);
- zero total numerical flux on every exterior face;
- explicit positivity and mass checks.

It supports the default diagonal `D=I/2`; it rejects off-diagonal diffusion rather than silently approximating it.

Starting from exact subcell averages of the same native Q1 initial law, its normalized covariance discrepancy from the common 200,000-path MC result is:

| FV refinement factor | Cells | `E_cov` | Wall time |
|---:|---|---:|---:|
| 1 | `30x36x36` | 0.5883 | 0.128 s |
| 2 | `60x72x72` | 0.2718 | 1.64 s |
| 4 | `120x144x144` | 0.1308 | 66.0 s |

The hierarchy moves toward both MC and Q1 but remains unconverged. At the finest level, Q1 and FV differ by `L1=0.15390`. This is useful triangulation: it confirms that coarse deterministic diffusion is large, but it cannot identify a high-accuracy truth.

Evidence: [`independent_reference_refined_report.json`](independent_reference_refined_report.json).

## 10. Monte Carlo as a production density generator

The comparison is full-density versus full-density, not deterministic density versus cheap MC moments. For 200,000 CPU paths and a `120x144x144` histogram:

- native-law sampling: `0.246 s`;
- SDE propagation: `3.104 s`;
- histogram: `0.020 s`;
- covariance bootstrap p95: `0.00628`;
- raw histogram L1 versus refined FV: `0.19824`;
- raw histogram L1 versus Q1: `0.24284`;
- five 40,000-path batch histograms differ from the full histogram by TV `0.1194–0.1218`.

Gaussian smoothing is bias-sensitive. L1 versus FV is `0.09896`, `0.08899`, `0.17392`, and `0.30175` for bandwidths `0.75`, `1.0`, `1.5`, and `2.0` voxels. Voxels with under one expected particle hold 1.378% of FV probability but only 0.621% of histogram probability. The particle propagation is cheap and moment-accurate, but the density reconstruction is not stable enough to be an unqualified target generator. The RTX 4070 was not used, so no GPU production claim is made.

## 11. Characteristic methods

The strongest relevant sources were reviewed rather than treating every “Fokker–Planck” method as interchangeable:

- [Futai et al., mass-preserving two-step Lagrange–Galerkin](https://link.springer.com/article/10.1007/s10915-022-01885-w): conservative convection-diffusion in 1–3 D, second order in time, optimal L2 estimates, and a total-flux boundary form. Exact mass requires exact integration. Its characteristic-map estimates assume velocity behavior that keeps the map in the domain (including a zero-boundary velocity hypothesis), and no positivity result is supplied.
- [Colera et al., high-order nearly conservative Lagrange–Galerkin](https://www.sciencedirect.com/science/article/abs/pii/S004578252030551X): non-divergence-free velocity and a 3-D test, but no whole-density positivity guarantee and no verified Lorenz reflecting-boundary construction.
- [Ding et al., SLDG-LDG convection-diffusion](https://arxiv.org/abs/1907.06117): high-order, compact and mass conservative with large steps, but numerical evidence is in 1-D/2-D and the needed 3-D reflecting-boundary and positivity properties are not established.

Lorenz drift is nonzero at the truncation boundary and characteristics can leave the box while the *total* flux remains reflecting. None of these sources supplies a ready remap satisfying that boundary plus whole-cell positivity for this 3-D problem. The user's conditional instruction to implement a challenger only if assumptions were sufficiently close was therefore not met. Implementing a superficially similar periodic/pure-transport scheme would not be a controlled challenger.

## 12. Adaptivity

The installed runtime is DOLFINx 0.11.0. Although the [Python mesh API](https://docs.fenicsproject.org/dolfinx/v0.11.0.post0/python/generated/dolfinx.mesh.html) exposes `refine`, an actual hexahedral probe fails for both uniform and marked-edge calls with:

```text
RuntimeError: Refinement only defined for simplices
```

Adaptive hexahedral Qk is therefore unavailable in this runtime. Tetrahedral h-adaptivity would change the approximation space, export layout and positivity proof. Other candidates are nonuniform structured meshes outside the current `Domain` assumptions, p-adaptivity, and domain decomposition. Goal-oriented/dual-weighted refinement for `integral x_i x_j p` is mathematically attractive, but it is not implementation-ready without one of those topology choices.

## 13. Literature applicability matrix

Codes: `Y` supported; `P` partial/conditional; `N` not supported; `U` not established by the source. Columns are A linear FP/convection-diffusion, B irreversible/non-gradient, C 3-D, D full anisotropic diffusion, E transient, F arbitrary non-Gaussian input, G reflecting/no-flux, H positivity, I conservation, J high order.

| Primary source | A | B | C | D | E | F | G | H | I | J | Lorenz-63 assessment |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| [Liu et al. 2025 limiter](https://arxiv.org/abs/2410.19143) | Y | P | P | Y | Y | Y | U | Y | Y | Y | Limiter architecture applies; NIPG/semi-implicit theorem is not the present SIPG/BE scheme |
| [Liu & Yu 2014 MPP DG](https://epubs.siam.org/doi/10.1137/130935161) | Y | P | P | N | Y | Y | P | Y | Y | Y | Rectangular extension stated, but flux/time/diffusion hypotheses do not establish the current 3-D anisotropic scheme |
| [Futai et al. 2022 LG](https://link.springer.com/article/10.1007/s10915-022-01885-w) | Y | Y | Y | N | Y | Y | P | N | Y | Y | Closest characteristic theory; boundary characteristic-map and positivity gaps remain |
| [Colera et al. 2020 LG](https://www.sciencedirect.com/science/article/abs/pii/S004578252030551X) | Y | Y | P | N | Y | Y | U | N | P | Y | Promising transport accuracy; not ready for total reflection/positivity |
| [Ding et al. 2020 SLDG-LDG](https://arxiv.org/abs/1907.06117) | Y | Y | N | N | Y | Y | U | N | Y | Y | 1-D/2-D evidence only; boundary and positivity gaps |
| [Liu, Gao & Zhang irreversible FP](https://arxiv.org/abs/2210.16628) | Y | Y | P | P | Y | Y | P | Y | Y | Y | Important alternative finite-difference direction; its equilibrium reformulation/mesh constraints need a dedicated Lorenz derivation |
| [Positive Scharfetter–Gummel FV](https://doi.org/10.1016/j.amc.2022.127071) | Y | P | P | Y | Y | Y | Y | Y | Y | Y | Strong general anisotropic/no-flux candidate, but nonlinear primal-dual implementation and Lorenz accuracy were not available in this cycle |
| [Carrillo–Liu–Yu gradient-flow DG](https://ora.ox.ac.uk/objects/uuid%3A5ff5ab65-acf2-4d70-ae4d-e1e0b2b99fc1) | P | N | P | P | Y | Y | P | Y | Y | Y | Gradient-flow/nonlocal structure is not interchangeable with irreversible Lorenz drift |

No theorem from these papers is claimed for the complete present solver. The [Liu et al. paper](https://doi.org/10.1016/j.camwa.2025.05.008) justifies the two-stage optimization/scaling architecture; the measured Lorenz result determines usefulness here.

## 14. Mature DA regeneration

Old mature posterior files were produced by the old analysis operator and are excluded from final validation.

A new exploratory ensemble was generated with 20 independent `xz` trajectories, 20 cycles, observation variance 9, projected degree-14 analysis, Q1 `8x10x10`, and `dt=0.005`. The distribution-level stationarity rule is first met at cycle 12. Final-window mean mode count is 1.06; mean absolute marginal skewness is approximately `(0.457,0.203,0.400)`.

However:

- forecast limiter relative L1 mean is `0.08684`;
- analysis limiter relative L1 mean is `0.36266`, p95 `0.66144`, maximum `0.80433`;
- successive-state TV averages `0.5106`.

Thus an operational *coarse numerical* distribution appears to exist, but it is not a trustworthy approximation to the physical posterior family. It would be circular to validate a production method on those severely limited states. No corrected mature forecast at `30x36x36` or finer has yet been generated, so mature-forecast accuracy is explicitly **unknown**, not inferred from startup Gaussians.

Evidence: [`mature_da_projected_report.json`](mature_da_projected_report.json).

## 15. Accuracy-per-cost comparison

| Method | Resource | Time for `Delta t=0.05` | Covariance evidence | Full-density evidence | Status |
|---|---:|---:|---:|---:|---|
| Q1 DG | 311,040 DOFs, serial | 86.9 s | `E_cov=0.0856`, `R=13.6` | Q1–FV L1 0.1539 | Best deterministic candidate, not certified |
| Q1 DG | 311,040 DOFs, 8 ranks | approx. 26.4 s step work | same coefficients to MPI tolerance | output/diagnostics do not scale | Forecast benchmark only |
| Q2 DG | 311,040 DOFs | approx. 50.2 s at `dt=.000625` from step benchmark | `E_cov=0.2548` at `dt=.00125` | no converged reference | Reject current Q2 |
| Independent FV | 2,488,320 cells | 66.0 s | `E_cov=0.1308` | validator; still refining | Not production candidate |
| MC histogram | 200,000 paths, CPU | 3.37 s | noise p95 0.00628 | L1 0.1982 vs FV | Reconstruction too noisy |
| MC Gaussian filter | same particles | small extra cost | moments unchanged | best L1 0.0890 vs FV, bandwidth sensitive | Not certified |

The Q2 time extrapolation uses its measured `0.628 s` serial step and 80 steps; the accuracy measurement used `dt=.00125`, so this is a cost comparison rather than an unrun accuracy claim.

## 16. Controlled error budget

The terms are estimated separately and are **not added**, because they interact.

| Source | Controlled evidence | Assessment |
|---|---|---|
| Initial representation | fine limited L2 `E_cov=0.006835`, L1 0.05807 | materially repaired |
| Spatial + temporal + limiter propagation | same-law Q1 `E_cov=0.08558` | unresolved dominant aggregate |
| Time discretization | coarse fixed-mesh covariance Frobenius change 0.0170 under last halving | below old spatial error, not a fine normalized bound |
| Boundary formulation | manufactured order 2, mass below `3.2e-12` | formulation passes |
| Box truncation | startup boundary density negligible | mature expanded-domain test missing |
| Forecast limiter | relative L1 mean/max 0.00345/0.00629 | material |
| Bayesian analysis | fine projected `E_cov=0.03706`; limiter 0.05688 | improved but not closed |
| Export | Q1 two-subcell and Q2 three-subcell round trips about `1e-10` or better | controlled |
| MC covariance | p95 0.006282; SDE step change 0.000111 | resolved for covariance |
| Deterministic full-density reference | Q1–FV L1 0.15390 | not converged |

## 17. Evidence-derived gates

These are provisional research gates, not universal tolerances:

1. On startup and corrected mature states, `E_cov <= 0.03` and `R_cov <= 5`. With current MC p95, the ratio gate is approximately 0.0314.
2. Do not set a final full-density L1 gate until the deterministic hierarchy is converged; present reference disagreement is too large.
3. Forecast limiter relative L1 mean `<=0.001`, maximum `<=0.005`; analysis limiter `<=0.005`.
4. Halving `dt` changes normalized covariance by `<=0.003` and L1 by `<=0.0025`.
5. Expanded-domain mature-state covariance and marginal-TV changes are each `<=0.005`.
6. Conservative export/round-trip mass and L1 remain at `1e-10` or better.

Q1 currently fails gates 1 and 3. Mature gates 1, 4, and 5 are unmeasured. Q2 and MC reconstruction fail their respective controlled comparisons.

## 18. Reproducibility and API scope

Runtime: Python 3.12.13, DOLFINx 0.11.0, Basix 0.11.0, UFL 2026.1.0, PETSc 3.25.4, Open MPI 5.0.10. Hardware: AMD Ryzen 7 9800X3D (8 cores/16 threads), NVIDIA RTX 4070 12 GB present but unused. The project is not a Git repository, so SHA-256 hashes in [`experiment_manifest.json`](experiment_manifest.json) are authoritative.

Current APIs were checked against the official [DOLFINx](https://docs.fenicsproject.org/dolfinx/v0.11.0.post0/python/), [Basix](https://docs.fenicsproject.org/basix/v0.11.0/python/), [UFL](https://docs.fenicsproject.org/ufl/2026.1.0/), and [petsc4py KSP](https://petsc.org/release/petsc4py/reference/petsc4py.PETSc.KSP.html) documentation. The older FEniCS book informed only variational reasoning and verification methodology.

## 19. Smallest additional experiment required to decide

Generate at least four independent corrected `xz` DA trajectories through cycle 20 on Q1 `30x36x36`, `dt=0.000625`, using projected degree-14 analysis. Use burn-in 12 provisionally, then choose narrow, broad, skewed and anisotropic posteriors. For each:

1. propagate Q1 on `30x36x36` and one finer aligned Q1 mesh;
2. propagate 200,000 exact-native samples with bootstrap and a common-random-number SDE timestep check;
3. run independent FV factors 2 and 4 from the exact same input averages;
4. report covariance/eigensystems, marginal TV, full-density L1, limiter stages, domain expansion, wall time and memory.

Retain Q1 only if the mature covariance, limiter, timestep and boundary gates pass and the deterministic hierarchy makes the full-density comparison interpretable. If they fail, the next implementation should be a boundary-consistent characteristic remap or a general positive anisotropic finite-volume method—not more labels from an uncertified solver.
