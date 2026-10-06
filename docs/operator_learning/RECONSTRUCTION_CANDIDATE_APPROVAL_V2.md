# Reconstruction candidate: approval with reservations

2026-10-06, OL-D014. Owner approves proceeding with the proposed bin-free
empirical top-hat reconstruction candidate, explicitly retaining reservations.
Approval accepts a candidate for qualification, not a scientific G02 pass.
ACCEPTED_POPULATION_V1.md, its historical representation and all pilot inputs
remain unchanged. The scoped G01 pass applies to its archived v1 pipeline;
it does not certify a new candidate's FE transfer or learning representation.

Candidate law on the whole space, for recorded samples X_i:

\[
p_N(x)=\frac1N\sum_{i=1}^N\prod_{d=1}^3
\frac{\mathbf1_{|x_d-X_{i,d}|\le w_d/2}}{w_d}.
\]

The completed empirical_v4 diagnostic used w=(4,40/9,40/9) and exact box/voxel
overlap integration. These widths define a regularized occupation law. The
finite mixture has a Lebesgue density, potentially discontinuous; it is not a
proof of continuous or application-representative posterior reconstruction.
On the whole space it represents X+U for independent centred box noise U:
mean unchanged, covariance increased by diag(w_d²/12). Truncation changes these
identities and requires measured lost mass, without hidden renormalization.

The owner has not approved a numerical reconstruction-error budget, definitive
sample count, universal bandwidth, posterior smoothing, or scientific dataset
promotion. Freeze a new versioned executable recipe and justified thresholds
before a qualification run. Reverify changed representation interfaces.
Retain all difficult cases, raw masses and historical alternative results.

Completed local diagnostic evidence (not a qualification run):
`runs/operator-learning/OL-G02_reconstruction_empirical_v4/20261006T121248833844Z`.
Its large payload remains ignored/local; no portability claim is made here.
The candidate is not continuum truth merely because it avoids histogram bins.

Eventual assimilation follows the
[full-density Bayesian contract](../BAYESIAN_ASSIMILATION_CONTRACT.md).
No automatic posterior regularization or Gaussian/GMM state closure is approved.
