# How the state-space density neural-operator test works

Updated 2026-10-04. This records the user's final scope: a distribution sampled
from Lorenz trajectories is the input; the evolved distribution is the target.
There are no observation inputs or assimilation cycles in this particular test.

## The objective

The network should approximate the frozen numerical forecast map

`initial state-space density p_0(x,y,z) -> density p_T(x,y,z)`.

Here T=0.05 and the diffusion tensor is fixed:

```
D = [[1.0, 0.4, 0.2],
     [0.4, 1.0, 0.3],
     [0.2, 0.3, 1.0]]
```

The expensive Fokker--Planck solver produces the training targets. After
training, the neural operator predicts the final density directly. This pilot
tests whether that approximation works on a small family of sampled densities;
it does not certify a general-purpose or production-ready operator.

## 1. Simulate Lorenz trajectories and collect state-space samples

For each of six seeds, integrate the deterministic Lorenz-63 equations

```
dx/dt = 10(y-x)
dy/dt = x(28-z)-y
dz/dt = xy-(8/3)z
```

using RK4 with dt=0.001. Initial coordinates are sampled uniformly from
[-10,10] x [-10,10] x [10,30]. Discard the first 20 time units, then collect
1,000 points over the next 10 time units, at interval 0.01.

Each point is one sampled state (x,y,z). The cloud describes occupancy in
state space. Adjacent points are correlated; they are not 1,000 independent
training examples. Each complete cloud becomes one initial distribution and
one input/target pair. Six separately seeded trajectories give six pairs.
Transient removal is a design choice, not proof that an invariant measure has
been sampled accurately.

## 2. Convert the samples into an initial density

Bin the points in the box [-30,30] x [-40,40] x [-10,70] using 45x54x54 bins.
Apply a compact three-cell-wide box filter, average neighbouring bin values
onto the grid vertices, and interpolate trilinearly between vertices.
Normalize by the exact integral of this piecewise-trilinear field.

This is an explicitly regularized empirical state-space density. No Gaussian
initial distribution, fitted Gaussian covariance, or two-lobe Gaussian mixture
is used. Smoothing is specified because a finite point cloud itself is a
collection of point masses, rather than a volume density on which the current
PDE solver operates. Its width affects the initial law and must remain recorded
in every comparison. See assumption A12 in assumptions.yaml.

The solver must receive finite, nonnegative vertex values. The initial density
is projected onto Q2 on the frozen mesh, normalized, and checked/projected for
whole-cell positivity. The network input is the conservative export of this
accepted FE initial state, so input and target correspond to the same forecast.

## 3. Generate an evolved-density target with the solver

For each initial density, run the existing MFEM Q2 discontinuous-Galerkin
forecast with conservative upwind drift, full-SPD SIPG diffusion, reflecting
total flux, Crank--Nicolson and local-QP positivity correction.

The static locally refined mesh has 208,787 cells and 5,637,249 Q2 DOFs.
The background is 45x54x54, with the archived broader-support refinement marks.
Use dt=0.00015625 for 320 steps, giving T=0.05. Each forecast uses eight MPI
ranks; the six forecasts run sequentially so their large allocations do not
overlap. The refinement marks were designed for an earlier mature law, so
accuracy for these new empirical laws remains provisional.

The initial sampling trajectory is deterministic. The forecast uses the
stochastic full-SPD Fokker--Planck model. This is intentional: samples provide
an initial distribution; the PDE then transports and diffuses that distribution.
The target is a probability density, not the continuation of one sampled path.

## 4. Accept or reject each pair before training

Require whole-cell certified positivity at initialization and every accepted
forecast step, zero reported optimizer failures/fallbacks, and an absolute mass
bound below 1e-10. That mass bound includes both initialization error and drift
from the accepted initial mass. Require mean relative L1 correction below
0.0008. For initial/final exports, require finite values, measured negative mass
below 1e-13, mass error below 1e-10, and outer four-voxel-layer probability
below 1e-6.

Any failed pair stops this pilot before neural training. Preserve the failed
run and its diagnostics; do not quietly substitute different samples or relax
the thresholds. Successful optimizer flags are supported by guarded projection
acceptance, rather than a separately saved complete optimizer trace. This
wrapper does not add independent MC or full-history true-residual certification.

## 5. Prepare the density tensors

The solver exports exact polynomial volume averages on the common
180x216x216 grid. Average each aligned 3x3x3 block to obtain 60x72x72 values.
This averaging preserves exported probability mass in exact arithmetic.
Record the subsequent float32 conversion error separately.

Each neural input/target therefore contains 311,040 voxel-average densities.
Arrays use x,y,z axis order, and the domain volume is 384,000. For training,
multiply densities by that volume to obtain mean-one fields. Divide network
outputs by the same volume to recover physical densities.

## 6. Train and select the model

Use four complete trajectories for training, one for validation, and one held
out for testing. No cloud is split into training and test fragments.

The compact independently implemented 3D Fourier neural operator uses two
spectral layers, eight hidden channels, four retained modes per direction and
coordinate channels. It learns a correction starting near the unchanged-input
baseline. Positive output transformation and normalization impose nonnegative
values and unit discrete mass, subject to floating-point error.

Train for 100 epochs with seed 71023, Adam learning rate 0.002 and batch
size one. Minimize squared relative L2 density error. Choose the checkpoint by
validation loss, then evaluate it on the held-out test pair.

The user requested GPU use for neural training. Hardware inspection on
2026-10-04 confirms an NVIDIA RTX 4070 with nominal 12 GiB VRAM. The trainer
now selects CUDA automatically when available, moves the model and input/target
tensors onto it, and transfers outputs to CPU for NumPy diagnostics. It records
the actual device/runtime in `training_device.json`. The isolated environment
uses PyTorch 2.8.0+cu128 with bundled CUDA 12.8 libraries; the NVIDIA driver and
PDE environments are unchanged. `device=auto` retains CPU fallback; an explicit
unavailable CUDA request fails clearly. Available system RAM and GPU VRAM are
separate resource limits. No solver run is restarted by enabling CUDA.

This follows the supervised input-function/output-function workflow described
in the [official neuraloperator guide](https://neuraloperator.github.io/dev/user_guide/index.html).
The code here uses a small custom PyTorch model rather than that library.

## 7. Determine whether the result is useful

Compare predicted and solver-target densities using physical L1, relative L2,
mean error, voxel-centre covariance error and marginal total variations.
Compare all those errors against persistence: predicting p_T=p_0.

The network must improve on persistence to justify its usefulness. Mass and
positivity alone are insufficient, since its output architecture enforces them.
No quantitative neural-accuracy pass threshold has yet been predeclared.
Report the errors and comparisons without inventing a certification decision.

Six pairs provide a feasibility test. They cannot demonstrate broad
generalization, accurate assimilation, repeated-time rollouts, timestep/grid
independence, or agreement with the exact continuum solution. D and T are
fixed, so this model does not learn diffusion/horizon parameter dependence.

## Local execution and RAM behaviour

The persistent systemd user service continues independently of the chat.
Pause the solver process tree when MemAvailable drops below 2 GiB. Resume the
same processes when it reaches at least 2 GiB; do not discard and recompute
their work. Equal thresholds can cycle near the boundary. Pausing retains
allocations and cannot create additional RAM or guarantee avoidance of OOM.
Apply the same scheduling guard to training.

## Files and evidence

- Configuration: `experiments/neural-pilot.json`.
- Sampling, forecasts, acceptance and dispatch: `mfem/run_neural_pilot.py`.
- Empirical FE density coefficient: `mfem/empirical_prior.hpp`.
- Training and evaluation: `scripts/train_neural_pilot.py`.
- Technical specification: `docs/NEURAL_PILOT.md`.
- Immutable runs: `runs/neural-pilot/<UTC timestamp>/`.

Each run records source revision, configuration, input hashes, commands,
trajectory seeds and samples, density construction, solver logs and status.
Successful pairs produce a split manifest; successful training additionally
produces `best_model.pt`, `training_history.json` and `evaluation.json`.

## Actual status of the first launch

Run `runs/neural-pilot/20261004T131332Z` failed during law-0 initialization,
before any forecast timestep or neural training. MFEM correctly rejected
negative empirical vertex values. The saved array contains 12,939 negative
vertices, with minimum -4.9003769791999835e-20 and no nonfinite entries.
Its maximum value is 0.0006739453125000001.

Independent recomputation identifies tiny negative roundoff in the compact
uniform-filter pathway: direct convolution with the same nonnegative 3x3x3
kernel produces nonnegative values. The strict import guard exposed a data
preparation defect; this is not evidence of PDE evolution failure.
The preparer subsequently uses direct nonnegative-kernel convolution with the
same box kernel. A regression recreates the failed seed/window and requires
finite nonnegative vertices before dispatch. The user authorized a fresh
immutable restart; the original inputs remain unchanged. No clipping, threshold
relaxation, Gaussian substitution or PDE change is used.

Evidence hashes:

```
status.json: 45d0c58da0331c28b68cdbf29122181552a08b028155d3ffe9eca3509f7f77e0
law0/solver.log: 1d5e4b1310a9b80c31c62e392bab2f6abbffadb348c413aa308df878e000bfb4
law0/empirical_prior.bin: 1781d049f6f8b60fafff77c809dc159fd24de9de9c4df35962fe574427ae25a1
```
