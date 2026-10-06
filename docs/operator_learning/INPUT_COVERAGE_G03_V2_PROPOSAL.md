# G03 v2 proposal — hierarchical finite-window coverage characterization

2026-10-06, OL-D024/OL-D025. IMPLEMENTED_PENDING_GIT_PREDECLARATION. G03 remains OPEN.
This proposal follows verified v1 distinctness evidence; it cannot retroactively
pass v1 or establish an optimal training population.

## Question and scientific object

How much finite-window density variation arises across initial-state groups
versus different windows of the same recorded path, and what structures remain
poorly represented by small candidate training pools?

Keep the owner-selected deterministic Lorenz occupation-density family, Lorenz
parameters,20-unit spinup,10-unit window and box widths(4,40/9,40/9).
No Gaussian/GMM closure, posterior substitution, bandwidth tuning or outcome-
dependent removal of legitimate cases. Each input remains a regularized volume
density; prediction for every initial condition is not a finite-study claim.

Proposed bounded design:12 fresh initial-state groups with seeds83001–83012,
using the existing uniform generator on[-10,10]×[-10,10]×[10,30]. Record original
and post-spinup states. Save one30-unit fine path/group and three consecutive,
nonoverlapping10-unit windows:36 finite laws. These are different windows of
one source group, not36 independent trajectories. Sampling of initial states
does not prove statistical independence of the resulting chaotic densities.
The box is the existing generator's scope, not all possible Lorenz initial states.

20k endpoint reconstructions,80k finite controls and four deterministic phase
replicates retain G02's recipe. Matched-time fine/coarse integration starts
from the SAME recorded post-spinup state; do not reintegrate chaotic spinup
to define a purported common law. Recompute prior whole-space bounds per new
window. G02's historical pass does not guarantee every fresh window passes.
Retain unresolved reconstructions; show both full-attempt diagnostics and
conditional resolved-law diagnostics, with every denominator stated.

Use60×72×72 conservative grids for the complete matrix, then120×144×144 for
all36 endpoints as an export-resolution diagnostic. Kernel support leaving
the physical box is a recorded failure, not clipped or normalized-away mass.
Stream phase controls and avoid holding all high-resolution arrays in RAM.
No MPI, GPU, FPE forecast or training is needed for this characterization.

## Comparisons and candidate coverage

Report every within-law reconstruction pair, within-source between-window pair
and cross-source pair; full-density TV, mean/covariance, marginal TVs, lobe,
tail, transition and common-physical-region boundary diagnostics. Define that
common boundary region BEFORE execution rather than using equal voxel counts.
Pair observations are dependent; pair count is not an independent sample size.

Keep related windows together in any candidate allocation. Predetermine two
seed-order permutations and candidate pool sizes2,4,8 source groups. Report
nearest-density distances for all remaining source groups and their median,
p90, maximum and identity/structure of poorly covered cases. Repeat across
the two orders; these small descriptive comparisons cannot optimize selection.
The candidate pools are development diagnostics, not qualified training data.
The remaining groups become inspected development data on review; a future
untouched evaluation population must be independently generated.

Competing explanations: substantial cross-source density diversity; variation
dominated by window placement on the same occupation population; resolved but
poor coverage of localized structures; reconstruction errors obscuring diversity.
Retain duplicates, rare structures and every failure. No outcome chooses a new
window length, initial-state region or smoothing recipe within this run.

## Thresholds, authority and reporting

Technical invariants follow v1: finite nonnegative raw fields, mass error≤1e-10,
all attempts, immutable config/source/input/output hashes and failure accounting.
The existing owner-approved1% G02 finite-control budget is a reconstruction
diagnostic; exceeding it remains recorded and does not justify dropping a law.
Positive TV lower margins are sufficient separation diagnostics, not quotas.

Population coverage and surrogate-accuracy thresholds:
TO_BE_PREDECLARED_BEFORE_RUN for a later qualification experiment. This proposed
characterization deliberately has no scientific pass consequence. It reports
what was sampled, dependence, blind spots and uncertainty; G03 remains OPEN.
Owner-reviewed scope and explicit qualitative/numerical criteria are required
before qualification. More distinct laws alone cannot establish adequacy.

Method HIERARCHICAL_OCCUPATION_COVERAGE_V2: project experimental design, nearest-
TV diagnostics and grouped source controls. TV triangle/export derivation uses
INPUT_DIVERSITY_G03_V1.md and its Canonne reference; no i.i.d. theorem imported.
Research context newly consulted at proposal time: Esther Rolf, Theodora T
Worledge, Benjamin Recht, Michael Jordan, Representation Matters: Assessing the
Importance of Subgroup Allocations in Training Data, ICML2021, PMLR139:9040–9051,
https://proceedings.mlr.press/v139/rolf21a.html. Abstract-level rationale for
objective-aware allocation only; its learning results do not certify Lorenz
coverage, this population, independence or any chosen sample count. No theorem
from that paper is used. Group/sample counts above are engineering budget
choices, not derived optimality results; runtime must be measured at dispatch.

Implementation: scripts/run_input_coverage.py; tests/operator_learning/test_input_coverage.py;
experiments/operator_learning/OL-G03_input_coverage_characterization_v2.json.
Both group orders are fixed in config: ascending seeds and a deterministic
interleaving83007,83001,83010,83004,83012,83006,83009,83003,83011,83005,83008,83002.
Common boundary slabs have physical thickness(4,40/9,40/9); integrate the
piecewise-constant export by exact fractional voxel overlap. Statistical
moments use voxel centres as declared diagnostics, not exact native FE moments.
Fine-grid endpoint exports are restricted by aligned2×2×2 conservative averaging
and compared to coarse exports; agreement does not bound subvoxel information.
630 endpoint pairs are evaluated on the coarse grid;216 within-law phase pairs
also on that grid. Fine grids are endpoint/export diagnostics only.
Path failures retain all three law attempts; law failures retain partial arrays.
Missing references remain counted as unavailable queries, without fabricated TV.
Both all-attempt and reconstruction-resolved-only coverage reports are retained.

Before dispatch: validate streaming runner/grouped diagnostics and COMMIT phase A.
Earlier read-only.git prevented that commit; OL-D026 restores access and records
owner authorization to review, commit and run. No uncommitted draft may be dispatched.
Do not start an expensive campaign as a substitute. After launch of any job
lasting more than one minute, confirm persistence and hand back with an ETA.
