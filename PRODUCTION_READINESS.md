# Numerical accuracy closure and production-readiness decision

> **Superseded by [METHOD_SELECTION_REPORT.md](METHOD_SELECTION_REPORT.md).**
> This file preserves the 2026-09-08 pre-repair evidence. Its Monte Carlo
> comparison mixed two initial laws and its mature states used the old nodal
> Bayesian analysis; neither is final method-selection evidence.

Date: 2026-09-08  
Decision: **`NOT_READY`**

## Executive decision

The current solver is conservative, postprocessed-positive, reproducible, and
algebraically well solved.  It is **not yet accurate enough to be the source of
ground-truth neural-operator forecast pairs**.  On the best configuration
tested (`30x36x36`, DG1/Q1, backward Euler, `dt=0.000625`, forecast interval
0.05), the normalized covariance error against 100,000 SDE paths is 0.2193.
The bootstrap 95% Monte Carlo covariance-noise floor is 0.00874, so the observed
error is 25.1 times sampling uncertainty.  Mature non-Gaussian DA examples have
normalized covariance errors of 0.169--0.321, 14--24 times their MC noise
floors.  These are systematic numerical errors, not Monte Carlo fluctuation.

The existing `sample_dataset` has therefore been re-audited with a limiter
severity gate.  All 24 cycles are excluded and its manifest now reports zero
accepted training samples.  This is an intentional safety result.

## Method and positivity audit

The detailed hypothesis-by-hypothesis audit is in
[POSITIVITY_AUDIT.md](POSITIVITY_AUDIT.md).  The main findings are:

- Liu et al. analyse a linear Fokker--Planck equation on uniform rectangular
  cells with tensor-product `Q^k`, `k >= 1`, variable uniformly positive-
  definite anisotropic diffusion, Lax--Friedrichs convection, NIPG diffusion,
  and an explicit-convection/implicit-diffusion first-order update.
- This code uses continuous-drift upwinding, SIPG diffusion, and fully implicit
  backward Euler.  It therefore uses the paper's two-stage limiter framework,
  but is not a literal implementation of the complete published scheme.
- Stage one solves the same strictly convex lower-bounded, mass-constrained
  projection directly through its KKT multiplier.  Douglas--Rachford is an
  algorithm used in the paper, not a mathematical requirement for this simple
  projection.  Bisection tolerance and the final equality correction are
  reported.
- Stage two preserves each corrected average and makes the eight Q1 vertex
  coefficients non-negative.  Independently of the paper's finite admissible-
  point guarantee, an affine box Q1 polynomial is a convex combination of its
  eight coefficients.  The implementation therefore guarantees non-negativity
  everywhere in each cell after limiting.  This argument does not extend to
  Q2, curved cells, or an unlimited raw solve.
- MPI collects global averages on rank zero, solves one globally conservative
  projection, and scatters the result.  This preserves the serial mathematics
  to roundoff, as the two-rank test confirms, but is not the scalable parallel
  iteration proposed by the paper.
- The paper's uniformly positive-definite diffusion hypothesis does not cover
  a rank-deficient configurable `B`; the default `B=I` is covered.

Primary reference: Chen Liu, Jingwei Hu, William T. Taitano, and Xiangxiong
Zhang, “An optimization-based positivity-preserving limiter in semi-implicit
discontinuous Galerkin schemes solving Fokker--Planck equations,” *Computers &
Mathematics with Applications* 192 (2025), 54--71,
<https://doi.org/10.1016/j.camwa.2025.05.008>.

## Covariance and Monte Carlo uncertainty

All main reports include full PDE and MC covariance matrices, entrywise
variance/correlation errors, eigenvalues and their errors, principal-axis
angles, bootstrap 95% intervals, and independent-batch diagnostics.

| Configuration | Paths | `E_P` | MC noise p95 | Ratio | Marginal TV `(x,y,z)` |
|---|---:|---:|---:|---:|---|
| `20x24x24`, `dt=.00125` | 100,000 | 0.6142 | 0.00874 | 70.3 | (0.1240, 0.1143, 0.0636) |
| `20x24x24`, `dt=.000625` | 100,000 | 0.6108 | 0.00862 | 70.8 | (0.1241, 0.1143, 0.0629) |
| `30x36x36`, `dt=.000625` | 100,000 | 0.2193 | 0.00874 | 25.1 | (0.0507, 0.0502, 0.0320) |

Here `E_P = ||P_DG-P_MC||_F / ||P_MC||_F`.  The path-count sequence at
30k/60k/100k is stable, and five independent 20k batches give normalized
covariance deviations from the full sample of 0.0070--0.0194.  The PDE error is
well outside both checks.

At the fine configuration the covariance matrices are

```text
P_DG = [[3.43544, 3.19268,  0.20967],
        [3.19268, 6.40782, -0.01720],
        [0.20967,-0.01720,  8.00865]]

P_MC = [[2.54178, 2.68865,  0.17613],
        [2.68865, 5.03163, -0.04885],
        [0.17613,-0.04885,  6.87211]]
```

The corresponding mean error is `(-0.00233,-0.00719,0.01361)`: means look
good while covariance is still over-diffused.  This is precisely why mass and
mean agreement are insufficient acceptance criteria.

## Error budget

| Source | Quantitative evidence | Assessment |
|---|---|---|
| Monte Carlo sampling | normalized covariance noise p95 0.00874 at 100k paths | small and quantified |
| MC SDE timestep | common-Brownian comparison `h=.00025` vs `.000125`: normalized covariance change 0.000222 | negligible here |
| Spatial discretisation | at fixed `dt=.000625`, `E_P` falls 0.6108 to 0.2193 under 1.5x refinement; analytic fixed-dt L1 orders 1.08 and 1.12 | dominant unresolved error |
| Temporal discretisation | Lorenz fixed-mesh BE self-comparison at `dt=.000625` vs `.0003125`: L1 0.00228 and covariance Frobenius 0.0170; approximately first order | materially below spatial error at chosen `dt` |
| Time scheme choice | coarse Crank--Nicolson `E_P=0.6018` vs BE `0.6142`; limiter mean rises slightly | BE is not the main discrepancy |
| Positivity processing | fine run: mean/max relative L1 0.00287/0.00549; negative raw averages and scaling on every step | still frequent and material |
| Voxel export | two subcells/axis exactly reconstruct solver-produced Q1 to roundoff; mass to roundoff | below PDE error if `export_subcells=2` |
| Domain | aligned Gaussian baseline/expanded test changes moments and covariance at roundoff with low boundary mass | encouraging, but mature-state expanded-domain evidence is incomplete |

The spatial and limiter contributions are coupled: refinement reduces both
oscillation and over-diffusion, but the present experiments do not identify a
unique additive split.  The table therefore avoids falsely adding dependent
error estimates.

## Limiter analysis

The code now retains raw, post-projection, and post-scaling states, and records
stage masses, L1/L2 changes, mean, covariance, entropy, negative averages,
corrected/scaled fractions, scaling factors, iterations, and timings.

- At `20x24x24`, `dt=.00125`, all 40 steps have negative raw averages and
  scaling.  Mean/max relative L1 corrections are 0.0114/0.0146; the mean raw
  negative-average fraction is 46.3%.  This is classified severe.
- At `30x36x36`, `dt=.000625`, all 80 steps still require both stages.
  Mean/max relative L1 corrections improve to 0.00287/0.00549; 44.6% of raw
  averages are negative and approximately 49.8% of cells are corrected.
- In the three mature forecast probes, mean limiter corrections are
  0.0470--0.0665 and maxima 0.0555--0.1070.  The limiter is masking a severely
  under-resolved coarse forecast in those examples.

The constrained average correction changes moments only weakly in the
inspected Gaussian run; most observable change is introduced by polynomial
scaling.  This does not make scaling incorrect—it makes raw resolution a
quality issue.  The provisional per-cycle gate is maximum relative L1 <=0.005.
Passing it is necessary, not sufficient: a configuration must also pass the
independent distribution-level accuracy gates below.

## Separate convergence and higher-order investigation

Analytic constant-advection/diffusion with fixed `dt=.00125` gives L1 errors
0.6409, 0.4702, 0.3662 for 6, 8, 10 cells/axis and observed orders 1.08, 1.12.
L2 orders are 0.94, 0.90.  Lorenz temporal self-convergence on fixed
`12x16x16` gives L1 differences 0.0308, 0.0158, 0.00693, 0.00228 as `dt` falls
from .005 to .000625 against the .0003125 reference.  This is consistent with
a roughly first-order method before reference-proximity effects.

The paper supports `Q^k`, but a correct Q2 implementation needs weighted
quadrature averages and a new admissible positivity point set.  FEniCSx can
represent the element, but the existing whole-cell Q1 proof cannot be reused.
No Q2 accuracy-per-cost claim is made without that method and its tests.

An experimental conservative theta method was added.  Crank--Nicolson did not
meaningfully close the coarse covariance error and has no inherited paper-level
positivity theorem for this fully coupled formulation, so backward Euler stays
the supported baseline.

## Mature DA distribution and forecast validation

Twenty independent `xz` trajectories with 20 cycles were run as a deliberately
coarse exploratory distribution study (`8x10x10`, `dt=.005`, observation
variance 9, seed 71023).  Cross-trajectory entropy, covariance spectrum,
trace/determinant, support volume, skewness, kurtosis, modes, mean state,
successive tensor TV, limiter activity, and boundary metrics are recorded.

No defensible burn-in is established within 20 cycles.  A provisional final
window of cycles 15--19 is available for coverage analysis, but the formal
stability criterion does not pass (final standardized change 0.504 versus the
0.5 criterion), and successive TV remains roughly 0.3--0.53.  Limiter means
are about 7--11%, so the run characterises pipeline diversity rather than a
trustworthy physical posterior law.  Validation/test feature-box coverage is
90--100%, but stationarity and observation-operator-specific burn-in remain
open.

Three native, non-Gaussian posterior states were sampled exactly from their
non-negative Q1 densities and forecast against 50,000 particles, without
Gaussianisation:

| State | `E_P` | MC p95 | Ratio | Mean limiter L1 |
|---|---:|---:|---:|---:|
| narrow | 0.2578 | 0.01225 | 21.1 | 0.0470 |
| broad | 0.1694 | 0.01215 | 13.9 | 0.0483 |
| skewed | 0.3208 | 0.01325 | 24.2 | 0.0665 |

These mature-state results independently reinforce `NOT_READY`.

## Projection and representation

Interpreting one Q1 cell average as a piecewise-constant field loses substantial
shape information.  Two subvoxels per cell axis are now the default.  The eight
subvoxel averages uniquely determine Q1, and the automated round-trip test has
L1/L2 and mass errors at floating-point level.  This representation uses eight
times as many tensor values as the old cell-average export, but it prevents the
ML interface from becoming an additional uncontrolled projection error.

## Scalability and cost

On `12x16x16`, mean step times for 1/2/4/8 ranks are
0.1139/0.1061/0.0310/0.0164 s (6.94x speedup at 8 ranks).  The limiter consumes
94--96% of step time.  Diagnostics take 1.43--1.97 s and do not strong-scale;
rank-zero global work is already visible.

On `30x36x36`, one step is 1.152 s on one rank and 0.330 s on eight ranks.
Limiter time is 1.078 s and 0.253 s respectively; diagnostics remain 2.51 s and
2.27 s.  The present dataset writer explicitly requires one rank, so the
eight-rank result is a forecast benchmark, not an available dataset speedup.

For 30 cycles/trajectory, burn-in 10, `dt=.000625`, and interval .05, a
one-rank lower-bound cycle cost (80 steps + three diagnostics + three exports,
excluding Bayesian analysis and three checkpoint writes) is about 101 s.
Each cycle stores two 60x72x72 float64 tensors plus three 311,040-coefficient
native checkpoints: approximately 12.44 MB before filesystem overhead.

| Trajectories | Cycles | Candidate post-burn samples | Lower-bound serial wall/CPU | Approx. storage | Current accepted |
|---:|---:|---:|---:|---:|---:|
| 20 | 600 | 400 | 16.8 h | 7.5 GB | unknown; do not generate |
| 100 | 3,000 | 2,000 | 3.5 d | 37 GB | unknown; do not generate |
| 1,000 | 30,000 | 20,000 | 35.1 d | 373 GB | unknown; do not generate |

Actual cost is higher.  Rejection rates cannot be responsibly extrapolated
from the coarse sample: its measured rate is 100%, while the fine Gaussian run
barely crosses the current limiter maximum gate.  Accuracy closure must precede
production-cost commitment.

## Acceptance gates and next experiment

Before production, one solver configuration should satisfy all of:

1. Gaussian and representative mature forecasts have normalized covariance
   error <=0.05 and no more than five times the experiment's bootstrap MC p95
   noise floor.
2. Marginal TV is <=0.03 for each coordinate, with path-count stability.
3. Mean limiter relative L1 is <=0.001 and maximum <=0.005; every exceedance is
   rejected and reported.
4. Temporal refinement changes covariance by <=10% of the allowed covariance
   error and L1 by <=0.0025 over one observation interval.
5. Expanded-domain mature forecasts change normalized covariance and marginal
   TV by <=0.005, with boundary mass <=0.002.  These thresholds must be revised
   if the actual convergence/noise floor is larger.
6. Q1-to-tensor round-trip L1 and mass errors remain <=1e-11.
7. Burn-in/stationarity and coverage pass separately for each intended
   observation operator and variance.

The thresholds deliberately sit above measured MC and roundoff floors while
remaining materially below errors that would train a surrogate to reproduce
known numerical diffusion.  They are provisional research acceptance levels,
not universal mathematical constants.

The next discriminating experiment is another fixed-`dt=.000625` spatial
refinement beyond `30x36x36`, followed by mature-state particle checks at that
resolution.  If cost becomes prohibitive before the gates pass, implement and
validate Q2 or a less-diffusive positivity-compatible spatial flux rather than
generating compromised labels.

Candidate solver-validation command (not a production certificate):

```bash
micromamba activate pde
mpirun -n 8 python solver.py --cells 30 36 36 --dt 0.000625 --t-final 0.05 --theta 1.0
```

Exploratory multi-trajectory command, retained only to exercise the gated
pipeline:

```bash
micromamba activate pde
python generate_dataset.py \
  --output exploratory_dataset \
  --trajectories 20 --cycles 30 --burn-in 10 \
  --observation xz --obs-variance 4 \
  --obs-interval 0.05 --cells 30 36 36 --dt 0.000625 \
  --theta 1.0 --export-subcells 2 \
  --max-limiter-relative-l1 0.005
```

There is intentionally **no recommended production dataset command** while the
decision is `NOT_READY`.

## Evidence files

- `monte_carlo_uncertainty_20x24x24.json`
- `monte_carlo_fixed_dt_20x24x24.json`
- `monte_carlo_uncertainty_30x36x36.json`
- `crank_nicolson_mc_20x24x24.json`
- `separate_convergence_report.json`
- `limiter_impact_20x24x24.json`
- `mature_da_report.json`
- `mature_forecast_validation.json`
- `scaling_rank1.json`, `scaling_rank2.json`, `scaling_rank4.json`, `scaling_rank8.json`
- `scaling_30_rank1.json`, `scaling_30_rank8.json`
- `validation_report.json`
- `experiment_manifest.json`
