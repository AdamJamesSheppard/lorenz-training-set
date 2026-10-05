# G01 representation contract v1

Population: [owner-approved ATTRACTOR_DENSITY_V1](ACCEPTED_POPULATION_V1.md).
Source experiment: six-law pilot 20261004T133438Z, development evidence only.
No sensor conditioning is present. No Gaussian/GMM state approximation is used.

## Probability objects and transformations

1. Empirical temporal occupation measure mu_N = sum_j delta_(x_j)/N. Each xyz
   sample is a recorded simulated deterministic Lorenz state. Temporal dependence
   is retained; this measure has no three-dimensional Lebesgue density.
2. Regularized continuous p: histogram45×54×54 on
   [-30,30]×[-40,40]×[-10,70], direct nonnegative3×3×3 averaging with zero exterior
   padding, edge-padded corner averaging into46×55×55 vertices. Normalize by exact
   tensor-trapezoidal integral. This is a piecewise trilinear volume density,
   explicitly different from the singular empirical measure. Smoothing bias,
   sample-size stability and temporal dependence are G02 questions.
3. Accepted p_h: MFEM Q2 DG mass-matrix L2 projection using cube integration
   rule14, normalization and unchanged cell-average/local-QP positivity repair.
   The background45×54×54 and its aligned octree children contain the Q1 source
   polynomial in Q2. Initial correction is nevertheless measured, never assumed
   zero. Evolution uses the existing fixed full-SPD diffusion, reflecting box,
   dt=.00015625, T=.05 and320steps. G01 does not certify continuum target accuracy.
4. P_V p_h: conservative voxel averages, not point samples or voxel probabilities.
   Fine shape180×216×216, axesxyz, z fastest, C-order little-endian float64.
   Affine-piece tensor3-point Gauss integrates Q2 exactly. Coarse cells contribute
   each voxel integral; eight half-voxel children contribute volume-weighted
   averages. Native exporter checks coverage8 everywhere before writing.
5. Learning-grid density: aligned3×3×3 block means into60×72×72, then float32
   cast. No interpolation, clipping or additional normalization at this stage.
   Voxel probability equals density times voxel volume; domain volume384000.
6. Learning tensor u = float32(384000 * density), shape[batch,channel,x,y,z]
   = [1,1,60,72,72] per law. Mean approximately one. Decode as u/384000.
   Trainer positional channels are index-space linspace(-1,1,n), including
   endpoints; these are not physical voxel-centre coordinates. Physical metrics
   use actual voxel centres. Preserve this historical checkpoint convention.

Output: historical FNO uses softplus and global mean-one normalization, then
inverse scaling. These enforce positive normalized output only; their statistical
fidelity remains unqualified. No model changes are authorized by this contract.

## Frozen verification scope

OL-G01_representation_v1 checks all six archived initial/final exports, exact
reconstruction from archived samples, file shape/layout, mass and negativity,
coarsening/cast identity and tensor roundtrip. Float64 mass tolerance1e-10 reuses
the existing numerical invariant; negativity tolerance1e-13 is a numerical
roundoff budget. Initialization/export L1 tolerance1e-10 tests aligned Q1/Q2
representation identity, not a general discretization-accuracy requirement.
Float32 budgets are4eps times mass plus volume times smallest subnormal;
machine limits follow [NumPy finfo](https://numpy.org/doc/stable/reference/generated/numpy.finfo.html).
Thresholds are frozen before running the archived-array audit.

Source-level exporter and projection inspection plus asymmetric-axis and Q2
quadrature fixtures complement archive checks. Native FE coefficient states were
not archived for this pilot: independent native-field re-export is unavailable.
This limitation forbids claiming a complete native replay or continuum accuracy.
G04 checks reference applicability; G05 measures information loss/error budgets
from voxel resolution, coarsening and casting, rather than merely conservation.

Passing G01 unlocks G02 reconstruction stability only. It authorizes neither a
large target campaign nor qualified training, posterior transfer or DA use.
