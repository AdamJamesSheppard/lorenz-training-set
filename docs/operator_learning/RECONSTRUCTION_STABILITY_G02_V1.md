# G02 reconstruction stability — characterization v1

Scope: owner-selected ATTRACTOR_DENSITY_V1. Existing laws remain regularized
state-space distributions sampled from deterministic Lorenz trajectories.
No Gaussian/GMM state closure, posterior replacement, FEM targets or training.

## Scientific object

Hold the initial seed, burn-in20, window10 and scalar RK4 dt=.001 fixed per
historical law. The conditional finite-window occupation law is the distribution
of the state when the time is sampled uniformly within that same window.
Denser temporal sampling estimates that same window; extending the window would
change the finite-window law. Independent trajectories concern G03 diversity,
not reconstruction noise conditional on one path.

Replay every saved trajectory bit-for-bit at the historical stride10 before
using newly computed dense samples. The dense10000-point occupation measure is
a diagnostic reference, not a proved stationary law or continuum truth. Its
integration/time-discretization errors remain unqualified.

## Controlled comparisons

- Sampling: strides40,20,10,5,2,1 in the same fixed window, with up to four
  sampling phases. Compare conservative densities on the same60×72×72 grid.
- Independent reconstruction: independently draw uniform time indices from that
  fixed dense path at counts1000,4000,16000, with three replicates per count.
  Conditional independence of random draws does not imply independence of the
  original serial trajectory or provide independent underlying laws.
- Dependence: biased autocorrelations for x,y,z,positive-x,x²,z² on the original
  sequence, up to lag250. Heuristic first-nonpositive truncated correlation time
  and ESS are observable-specific; report censoring and undefined constant cases.
- Block perturbations: circular block lengths25,50,100,200, four replicates each.
  Report sensitivity to block length, with no bootstrap confidence/coverage claim.
- Histogram:30×36×36,45×54×54,60×72×72 at fixed physical top-hat smoothing
  widths derived from the original3-cell bandwidth. Overlap-weighted convolution
  handles noninteger widths. Vertex lifting still changes with histogram size;
  report that coupling rather than promising a pure smoothing-free comparison.
- Regularization: original histogram with filters1,3,5. These deliberately change
  the regularized probability law and quantify modelling sensitivity; they are
  not replicate noise at fixed smoothing. Original pilot arrays remain unchanged.

Report raw mass/negative mass, density L1/TV, marginal TVs, means/covariance,
positive-x probability, boundary probability and effective volume. Common-grid
diagnostics do not independently pass G05 resolution adequacy.

Dependence-aware resampling motivation:
[Shalizi, Time Series, including block bootstrap](https://stat.cmu.edu/~cshalizi/uADA/16/lectures/26.pdf).
Autocorrelation diagnostics require stationarity qualifications, and zero linear
correlation cannot establish independence. The programme makes no such proof.

## Predeclaration and adjudication

Executable characterization config: experiments/operator_learning/
OL-G02_reconstruction_characterization_v1.json. It freezes technical invariants
(mass1e-10, zero measured negativity, exact trajectory replay), comparisons,
seeds, dependencies, runtime and required output before scientific execution.
Every result and failed run receives a fresh directory and sealed provenance.
The runner refuses dirty/uncommitted source or a changed input/hash.

**Characterization completion leaves G02 OPEN.** Neither decreasing error alone
nor a heuristic ESS is an adequate absolute accuracy criterion. A scientific
reconstruction-error budget has not been approved. Do not manufacture an L1
tolerance to permit this gate to pass. After reviewing characterization, propose
a versioned reconstruction recipe and justified error budget relative to intended
surrogate accuracy, then predeclare qualification on new trajectories/replicates.
Preserve this diagnostic evidence; no retrospective promotion of its thresholds.

Two possible interpretations to adjudicate explicitly: adequate sampling of a
precisely declared finite-window regularized law, versus uncertain estimation
of a broader stationary occupation law. The owner-approved current meaning is
the former. Posterior representativeness remains outside this gate.

## Running once phase A is committed

```bash
python3 scripts/prepare_operator_run.py \
  experiments/operator_learning/OL-G02_reconstruction_characterization_v1.json
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  ./scripts/run-in-env python scripts/run_reconstruction_stability.py RUN_DIRECTORY
```

Use the fresh directory printed by the preparation command. Run CPU only;
do not start neural/FEM jobs. Source arrays stay read-only. Dense path arrays
and reference densities are newly computed, labelled diagnostic artifacts and
sealed with the report. They are never substituted into historical figures or
claimed as previously archived evidence. Git tracks compact adjudication and
hash ledgers; ignored large arrays require separate local retention.
