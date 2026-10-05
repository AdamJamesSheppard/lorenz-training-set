# Accepted scoped population v1 — 2026-10-05

Owner instruction: “Work on G01 I accept, keep the densities state space
distributions of an observed Lorenz attractor”. This accepts ATTRACTOR_DENSITY_V1
for the initial restricted fixed-physics p0→pT qualification programme and
authorizes G01. It does not accept the proposed mixed population.

## Probability meaning

Current implementation: an empirical time-occupation measure formed from
sampled deterministic Lorenz-63 trajectories, then explicitly regularized into
a nonnegative volume density. Here “observed” means sampled/recorded simulated
states; the existing six laws were not reconstructed from noisy sensor readings.
They are non-Gaussian full state-space densities, not point states or GMM fits.
The initial scope uses the historical generator recipe: RK4 dt=.001, burn-in20,
window10, sample interval.01, 1000 samples; histogram45×54×54, compact3×3×3
smoothing, trilinear reconstruction and conservative FE/voxel representation.
G02 may require a newly predeclared reconstruction version if stability fails.

## Roles and exclusions

OCCUPATION_PILOT_V1 is accepted as the input family for restricted operator
qualification, with engineering fixtures and future qualified train/validation
roles. Actual scientific dataset use still requires G01–G06 prerequisites;
no expensive campaign is authorized by family acceptance alone. The inspected
six-law pilot remains development/historical evidence. Final evaluation requires
a new untouched population and valid group splits.

The new ensemble/conditioned examples are retained as G00 comparison evidence,
outside the accepted current training population. Old GMM tests retain historical
FEM/regression scope. None silently replaces the owner-selected input family.

Eventual density-based DA remains the long-term application. Alignment/coverage
of actual observation-conditioned posteriors remains unverified and must be
tested at posterior-transfer gates. Fixed D/T, domain and boundary configuration
are unchanged. No claim of stationary-law estimation, independence of temporal
samples, arbitrary-density generalization, continuum accuracy or DA qualification.

## Scoped G00 decision

G00 passes population-definition/alignment review only for this bounded
attractor-derived forecast study. G00 numerical evidence and its warnings remain
unchanged; there was no numerical pass/fail threshold relaxation. The owner
selects a narrower initial scope rather than certifying posterior coverage.
Only G01 opens. The mixed-population recommendation is explicitly superseded
as a proposed initial direction, while its evidence is preserved.
