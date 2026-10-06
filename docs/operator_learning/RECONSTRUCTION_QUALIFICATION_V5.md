# G02 qualification v5: approved finite-control TV budget

2026-10-06, OL-D020. Owner explicitly approves proposed reconstruction TV ≤.01.
Method ID BOX_OCCUPATION_FINITE_CONTROL_V5. This is an engineering accuracy
requirement: ≤one percentage point discrepancy for any event of the declared
regularized finite law. It is not a published accuracy recommendation.
Source for TV convention and event interpretation:
https://ccanonne.github.io/files/compx270-chap11.pdf (Clément Canonne, lecture11).
Box-mixture derivation and implementation: RECONSTRUCTION_QUALIFICATION_PROPOSAL_V3.md,
operator_learning/reconstruction_controls.py. Lorenz/RK4 implementation and
dependence limitations: reconstruction.py, previous G02 research records.
No mixing theorem or continuum trajectory bound is imported.

## Frozen scope and experiment

Six fresh seeds82029–82034, uniform initial xyz in[-10,10]²×[10,30], twenty-unit
spinup at dt=.001; take the first saved state at20.001 as the common t=0.
Save that common state. Two ten-unit RK4 paths at
dt=.000125 and .00025 start there. Fine path is an80000-point finite control;
it is not continuum truth. No reintegrated-burn-in comparison.
Fixed box widths(4,40/9,40/9); no histogram, Gaussian/GMM, clipping or hidden
normalization. Candidate uses20000 points, endpoint phase3 in stride4.
Every phase is tested. Counts5000 and10000 are competing lower-cost recipes,
reported equally; their failure does not silently invalidate a20k result.
Sample count20k reduces temporal discretization without changing smoothing or
the accepted population. No recipe adoption/FE scope extension happens at dispatch.

For each count, repeat each phase subsample in consecutive time groups and
compute half the paired-box L1 upper bound against the80k control. At phases
with matching coarse timestamps (odd fine indices), compare coarse and fine
candidate clouds for an aligned integration TV bound. Triangle inequality bounds
the matching coarse candidate versus fine control by their sum. Acceptance uses
the maximum sampling bound plus maximum aligned integration bound, ≤.01 for20k
in EVERY attempted window. The sum is conservative; a failed upper bound is
insufficient certification, not proof that actual TV exceeds.01. Floating-point
evaluation adds a fixed1e-10 safety allowance, not an interval proof.

Compute exact conservative box voxel integrals for endpoint candidate and control
on60×72×72 and120×144×144. Require finite, nonnegative fields and raw mass
error≤1e-10 for both; no discarded kernel probability. These are technical
roundoff tolerances carried from previous diagnostics. Raw invariants precede
normalized shape diagnostics. Report L1/TV, marginal TVs, means/covariance,
lobes/tails/boundary probability and ACF/heuristic ESS. Statistics remain
diagnostics, without invented independent scientific thresholds. Whole-space
TV bounds already constrain event/marginal discrepancies; moment diagnostics
are complementary. Grid values do not certify subvoxel accuracy.

## Outcomes, limits and authority

Record all seeds/phases/counts, initial states/paths, arrays, metrics, failed
components, elapsed time, exclusions(empty unless execution errors recorded),
source/config/version/command/hardware hashes and seal. A per-seed resource/error
failure retains partial records and processing continues to other seeds.
Technical completion is separate from scientific candidate eligibility.
G02 remains OPEN until reviewed adjudication; no automatic gate promotion.

If20k fails, preserve this run and require a new predeclaration to increase
sampling. Never change width, thresholds, law selection or delete difficult cases.
Finite six-window success supports only this finite-control recipe scope.
No exact trajectory, invariant law, independent-time-sample, universal initial
condition, posterior, FE-reference accuracy or learning-grid claim follows.
Random conditional resampling is deferred: candidate is deterministic matched-time
quadrature, not a random density estimator. G03 separately tests law diversity.
G01 changed transfer, G04 target accuracy and G05 grid fidelity remain necessary.

Implementer self-review under direct owner authority; no independent assessor.
No solver, neural training, target generation or assimilation is included.
Existing unrelated untracked plotting script is preserved and recorded in dirty
provenance; tracked inputs must be clean and exactly match the predeclaration.
