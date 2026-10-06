# G02 bin-free qualification proposal v3 — DRAFT

OL-D015, 2026-10-06. Supersedes the proposed next design of v2, retaining v2
as history. Owner-approved candidate: RECONSTRUCTION_CANDIDATE_APPROVAL_V2.md.
No scientific pass threshold or execution authority is supplied by this draft.

## Precisely scoped object

Define the law as an empirical measure of a fixed recorded Lorenz window,
convolved with the declared box kernel w=(4,40/9,40/9). Keep ten-unit windows;
5000 points is the candidate sampling count, not yet an approved final recipe.
No histogram intermediate, Gaussian/GMM fit or outcome-based bandwidth choice.
G02 studies reconstruction stability of this regularized occupation law.
Actual Bayesian posterior applicability remains G16; no posterior smoothing
or independent-sample claim is inherited from the occupation construction.

## Qualification design to freeze after budget approval

Use fresh development windows, including differing lobe occupancy, from new
recorded initial states. Archive initial states and complete integration metadata.
Retain every attempted window. Compare 5000/10000/20000 matched-time samples,
multiple fixed sampling phases, independent conditional reconstruction replicates
and a common-start dt refinement. Separately integrated chaotic burn-in windows
must not be treated as reconstructions of one identical recorded law.
Independent reconstructions conditional on a recorded path do not prove time
samples independent. Retain autocorrelation/effective-sample-size limitations.

Exact conservative voxel overlap: compare grids60×72×72 and120×144×144.
Report raw mass/lost kernel mass, negativity, L1/TV, means, covariance, marginal
TVs, lobes and boundary mass, all cases and worst cases. Grid discrepancies are
lower bounds on whole-space L1 for the corresponding fields, not continuum
certificates. No clipping or silent renormalization of lost mass.

## Analytic control independent of comparison-grid resolution

For equal-size paired clouds a_i,b_i and normalized box kernel K_w, overlap
gives exactly

\[
\|K_w(\cdot-a_i)-K_w(\cdot-b_i)\|_1
=2\left[1-\prod_d(1-|a_{i,d}-b_{i,d}|/w_d)_+\right].
\]

Reason: both densities equal 1/volume on their respective equal-volume boxes;
their common mass is the product of relative overlap lengths. Integrating over
the symmetric difference gives twice one minus the common mass. Triangle
inequality bounds the L1 difference of the two mixtures by the average above.
Implementation: paired_box_l1_bound in reconstruction_controls.py.
This bound is valid for finite paired clouds regardless of temporal dependence;
it may be loose. Repeating each coarse sample equally permits a coupling to a
larger divisible fine cloud. Pair by predefined time groups, without optimizing
the pairing against observed scientific outcomes. Whole-space restriction to
the box remains contractive before normalization; normalized truncation needs
separate lost-mass accounting. Finite dt comparisons still do not bound an
unknown exact Lorenz trajectory without an independently justified tail bound.

## Decisions required before execution

Scientific total TV budget: TO_BE_PREDECLARED_BEFORE_RUN.
Sampling/integration component budgets: TO_BE_PREDECLARED_BEFORE_RUN.
Statistical component tolerances: TO_BE_PREDECLARED_BEFORE_RUN.
Scope of finite-control versus continuum claims: must be fixed explicitly.
Final sample count/bandwidth/representation interfaces: pending qualification.

Budget must follow intended downstream density/statistical accuracy, not the
observed pilot FNO error or the values this diagnostic already obtained. Owner
approval of a candidate does not approve arbitrary pass thresholds. New phase-A
commit and immutable config precede execution; failures remain recorded.
Changed FE transfer needs representation checks; no G01 scope extension here.

Kernel-filter convergence results require their own hypotheses, not supplied by
these correlated deterministic occupation samples:
[Crisan–Míguez, including erratum](https://arxiv.org/abs/1111.5866).
