# Bounded neural-operator pilot

Authorized by the user on 2026-10-04; production authorization remains false.
This is discrete-solver learning, not whole-space/continuum certification.

Implementation checks cover conservative coarsening, reproducible sampled
priors, the Python suite and executable solver invariants. The FNO passes a
forward/backward finite-gradient and probability-constraint test. A two-rank
5x6x6 one-step constant-field importer test verifies initial physical density,
export mass, whole-cell positivity and zero failure/fallback flags. This is
an importer smoke test, not accuracy certification of the attractor density.

Build: `bash scripts/build-pilot-solver`.
Run: `scripts/run-in-env python mfem/run_neural_pilot.py` under a persistent
local systemd user service. Evidence: immutable `runs/neural-pilot/<UTC>/`.

Six independent Lorenz-63 trajectories generate state-space input distributions.
Integrate deterministic Lorenz by RK4 at dt .001, discard t<20, then collect
1000 states at interval .01 over ten time units. Bin on 45x54x54, apply compact
three-cell box smoothing, and construct a nonnegative trilinear density on
the background vertices. This regularizes a sampled attractor measure into a
volume density; no Gaussian initial law or covariance fit is used. Twenty time
units of transient removal is a design choice, not proof of stationarity.
Split whole trajectories four/one/one for training/validation/test.
The deterministic attractor supplies initial data; subsequent forecasts use
the stochastic full-SPD FPE. Fixed full-SPD tensor, broader-support static NC mesh,
Q2/CN/local-QP, dt .00015625, 320 steps, T .05. Spatial support was derived
from the original law; new-law accuracy is provisional. This deliberately
small family gives a pipeline feasibility test, not broad generalization.

Reject each law on positivity, absolute mass bound 1e-10, measured negative
mass 1e-13, optimizer/fallback flags, mean correction .0008, or initial/final
outer four-voxel-layer mass 1e-6. Failing a
law stops training; preserve all outputs. No independent MC accuracy, per-step boundary,
or true residual gate is fabricated where this exporter lacks that evidence.
The inherited domain gate applies only to its tested law. Coarsening uses
aligned exact voxel-volume averaging to 60x72x72; float32 conversion is recorded
as training representation error rather than applying FE tolerances to it.

An eight-channel two-layer 3D Fourier operator, four modes per direction,
coordinates and zero padding predicts a density correction initialized near
persistence. Softplus and
normalization enforce nonnegativity/unit discrete mass; these diagnostics are
architectural constraints, not evidence that density predictions are accurate.
No D/T input channels are used because both parameters are fixed in this pilot.
Train 100 CPU epochs, batch one, seed 71023. Validation selects the checkpoint;
test is evaluated afterward. The input is only the state-space density; no
observations or assimilation cycles are included in this user-selected test.
Compare L1, relative L2, voxel-centre covariance,
means, marginal TVs against persistence. No autoregressive rollout is supported
by terminal-only pairs. Save model, training history, packages, hashes and splits.

Training uses isolated `.venv/neural-pilot` with CPU torch 2.8.0 and numpy
2.2.6; existing solver environments are preserved. Upstream architecture and
workflow reference: https://neuraloperator.github.io/dev/user_guide/index.html
The compact implementation here is independently written in PyTorch.

Pause below 2 GiB MemAvailable; resume the same process at >=2 GiB. Equal
thresholds may cycle. There is no kill/relaunch, checkpoint or swap-to-disk
pipeline. Pausing retains allocations; the safeguard cannot create RAM or
prevent every OOM. Sequential samples release solver allocations between laws.
Build the zero-padding low-memory binary from frozen MFEM source; this only
releases redundant assembly operators, retaining the original numerical method.
