# G03 input diversity v1 — bounded characterization

2026-10-06, OL-D022. Owner asks to start G03. Method DIVERSITY_TV_MARGIN_V1:
compare reconstruction variation within a fixed recorded occupation law with
between-law differences. This study does not authorize G03 promotion or targets.
No arbitrary population-coverage threshold is introduced.

## Scientific object and alternatives

Use all six G02 qualification_v5 windows82029–82034, recorded after identical
declared spinup protocol. Their ten-unit duration, full trajectories and fixed
box widths(4,40/9,40/9) stay unchanged. Each80000-point regularized finite law
has four deterministic20000-point phase reconstructions. Phase replicates are
quadrature controls of ONE law, not four independent trajectories or new laws.
No new trajectories, longer windows, Gaussian/GMM replacement, optimized
bandwidth, outcome-dependent selection or lobe templating is permitted.

Competing explanations: distinct occupation windows produce resolved geometry;
sampling/representation variation explains apparent separation; observed windows
are distinct but insufficiently diverse for the intended forecast population.
Only the first two can be characterized in this bounded study. G03 remains OPEN
until population/coverage criteria are separately predeclared and assessed.

## Frozen comparisons and mathematical resolution diagnostic

On both60×72×72 and120×144×144 conservative grids, reconstruct phases0–3 with
exact box/voxel overlaps. Verify phase3 bitwise against archived G02 candidate.
Keep raw mass/negativity and kernel loss; no clipping or renormalization repair.
Require finite nonnegative fields, mass error≤1e-10 and every attempted case.
Record six phase-pairs per law (72 comparisons over two grids), and all15
endpoint-phase between-law pairs (30 comparisons over two grids). Archive
phase arrays, summaries, source/config/provenance/report/seal, all failures/costs.

Let q_i be the full-space endpoint reconstruction, p_i the80k finite control,
and e_i the already-recorded worst sampling+aligned-integration TV bound.
Grid TV is contractive before normalization. Since each field's raw mass is
checked, report numerical adjustment d_i=|mass_i-1| conservatively, plus1e-10
roundoff allowance. Triangle inequality gives the diagnostic lower bound

    TV(p_i,p_j) >= max(0, TV_grid(q_i,q_j)-e_i-e_j-d_i-d_j-1e-10).

This uses the existing project paired-box inequality and a TV metric property.
Derivation: triangle inequality bounds TV(q_i,q_j) above by
e_i+TV(p_i,p_j)+e_j; conservative export cannot increase TV. Normalizing
the retained voxel field changes its L1 by the raw mass defect, and kernel
truncation adds lost mass. Using the full raw defect per law is conservative
under the nonnegative, approximately unit-mass invariant; float64 evaluation
is numerical evidence without interval certification. Finite controls are not
exact trajectories or continuum occupation laws. A positive signed margin
resolves this pair against the stated finite-control errors. A nonpositive
margin means unresolved separation, not equality. No positive-pair quota is
selected retrospectively to manufacture a gate pass.

Source: Clément Canonne,Lecture11,Definition50.1/Fact50.2 and TV data processing,
https://ccanonne.github.io/files/compx270-chap11.pdf. Used for TV conventions and
metric/representation rationale, not its i.i.d. sampling theorems. Exact box
coupling is project derivation in RECONSTRUCTION_QUALIFICATION_PROPOSAL_V3.md.
No mixing/independence assumption or statistical hypothesis-test p-value.

## Reporting and next decision

Report all individual/median/p90/worst within-law and between-law distances,
signed/resolved margins, pair denominators, means/covariance/marginal/lobe/tail
and boundary differences, per-law nearest neighbor and lower-cost uncertainty.
Boundary diagnostics use the declared four-voxel region separately on each
grid; those regions have different physical thicknesses and are not equivalent.
Preserve unresolved pairs and execution failures. Zero variation on one coarse
grid cannot imply exact law agreement. No six-window universal initial-condition,
posterior-population, coverage or surrogate-generalization claim follows.
The cases are development data, not untouched evaluation. Longer windows could
collapse occupation variability and are not an automatic remedy.

After characterization, justify a larger hierarchical population design if
needed: independent initial-state groups, multiple nonoverlapping windows,
declared structures/difficult cases, separate reconstruction replicates. Do not
silently substitute invariant-law estimation for finite-window density forecast.
New scope/thresholds require owner-approved predeclaration before qualification.

## Dispatch and accountability

Commit this design/config/source before executing. Preserve unrelated untracked
plot script and record the exact dirty status as explicitly disclosed in G02.
All tracked inputs must match the predeclaration. New immutable evidence only;
no modification to G02 or pilot. Self-review under direct owner instruction,
no independent assessor. G03 OPEN and G04–G17 LOCKED regardless of technical
completion; no FEM targets, model training or assimilation. Earlier read-only
.git dispatch blocker is recorded in validation history; OL-D023 restores access.
