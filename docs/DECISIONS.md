# Decision log

Decisions here are dated and revisable. Add a new entry that marks an older
decision `superseded`, `narrowed`, or `confirmed` rather than rewriting history
to make the current direction look inevitable.

## 2026-09-23 - Test a third geometric AMR depth on conservative voxel averages

**Decision.** Confirm the numerical validity of the first and second static
NC-hex trajectories while keeping mature-density convergence and production
authorization open. Predeclare a third geometric refinement depth within the
second-level marked region, using the unchanged time-aggregated indicator and
95% total indicator-energy target. Require
`D_AMR2,AMR3 <= 0.007853258960160175`, half the observed first-to-second
common-grid difference, plus the existing positivity, mass, correction,
statistical and DOF gates.

**Evidence.** The first 320-step run passes `D_AMR1,gf=0.0187157<0.02`;
the second passes every declared gate with `D_AMR1,AMR2=0.0157065<0.05`
and mean correction `1.04980e-4`. Its distance to `g_f` rises slightly
to `0.0191270`, so the prior loose gate does not establish asymptotic
convergence. The second run takes 155 minutes, with 6.33 GiB peak RSS per
rank. A one-step third-depth test contains 208,983 cells and passes positivity,
mass and exact conservative voxel-export checks; its observed 7.15 GiB
peak RSS per rank motivates a memory check during the full run.

**Scope.** The `180x216x216` common grid is the frozen comparison
representation. Third-depth cells are integrated conservatively into its
voxels, so any pass demonstrates contraction of voxel averages, not
subvoxel Q2 convergence. Domain sensitivity and independent full-density
reference remain required.

## 2026-09-16 - Certify uniform MFEM equivalence and authorize static NC-hex AMR

**Decision.** Certify the tested conforming MFEM port as numerically equivalent
to the frozen DOLFINx mature Q2-CN/local-QP trajectory. Authorize a fixed-mesh,
replay-marked NC-hex reproduction experiment against the fine graded `g_f`
solution. Keep mature full-density convergence and production dataset
authorization open.

**Evidence.** The primary clean 320-step equivalence run has final conservative
common-grid `L1=5.26e-11`. A later counted-certificate rerun produced identical
final bytes with zero uncertified cells, but its wrapper failed after the solve;
the comparison was completed separately and provenance records the distinction.
The `2:1` NC-face probe agrees with a conforming comparator within `5.87e-14`
relative action error on two ranks. A one-step 140,418-cell AMR smoke test has
zero uncertified cells and `1.43e-14` mass drift. These small tests do not yet
establish full AMR trajectory accuracy.

**Consequence.** The first AMR run must reproduce `g_f` to `L1<0.02` while
meeting positivity, mass, correction, statistical and DOF gates. Only a second
AMR level can provide a density-convergence sequence. Domain sensitivity and
production dataset gates follow later.

## 2026-09-15 - Correct the MFEM port and pass small-mesh physical equivalence

**Decision.** Supersede the earlier MFEM operator probe as structural evidence
only. Correct the Cartesian-box construction, formulate the MFEM matrix as the
evolution operator in `M p_t = K p`, match the DOLFINx SIPG penalty on physical
faces, and require conservative physical-field comparisons before any mature
forecast. The frozen limits are in
`experiments/mfem-physical-equivalence-gate.yaml`.

**Evidence.** The earlier constructor call created an x extent of one rather
than sixty, and the diffusion/CN signs did not represent the frozen DOLFINx
evolution. The staged diagnostic caught both defects. On the corrected
`4x5x5` mesh, four independently represented Q2 fields give maximum relative
L1 discrepancies `2.55e-16` for state mapping, `4.95e-15` for the full operator,
`2.43e-15` for raw CN, and `7.81e-12` after the local QP. The fourth field makes
all 100 cell QPs active; both ports report no optimizer fallback.

**Consequence.** The corrected implementation advances to the predeclared
`30x36x36` one-step repetition. A full mature forecast and NCMesh AMR remain
locked until that production-mesh diagnostic passes.

**Evidence.** Immutable local run
`runs/mfem-physical-equivalence/20260915T184304Z`.

## 2026-09-15 - Replace tensor grading with a gated MFEM AMR branch

**Decision.** Reject another tensor-product graded level. Keep DOLFINx as the
frozen reference and port the identical Q2 DG, Crank--Nicolson, full-SPD and
local-QP mathematics to MFEM. Require uniform conforming-mesh equivalence before
using `NCMesh`; initially use a fixed isotropically refined mesh driven by the
completed time-aggregated replay.

**Evidence.** The replay is deterministic to common-grid `L1=3.61e-11` against
the completed fine run. Dörfler `theta=0.5` selects only 71 cells, but their
coordinate-product bands require 699,600 cells even at 75% axis-energy coverage,
above the frozen 311,040-cell ceiling. This is a topology/representation failure,
not a failure of the indicator or Q2 trajectory.

**Consequence.** The MFEM gate proceeds in stages: operator conservation,
element/face matrix agreement, one-step CN agreement, local-QP agreement, then
the mature uniform-mesh comparison. AMR remains unauthorized until all stages
pass. Dataset generation remains unauthorized.

## 2026-09-15 - Accept production-scale MFEM one-step equivalence

**Decision.** Accept physical state, operator-action, raw-CN and local-QP
equivalence on the conforming `30x36x36` mesh. Keep the mature trajectory and
AMR gates locked in that order.

**Evidence.** Immutable run
`runs/mfem-physical-equivalence-production/20260915T185006Z` passes all
predeclared relative-L1 gates with maxima `1.19e-15`, `7.96e-14`, `9.43e-15`
and `1.21e-11`. The earlier `20260915T184604Z` attempt failed only because the
MFEM diagnostic projected 1,321 polynomials that DOLFINx had already certified
positive by depth-four Bernstein subdivision; matching that certificate removes
the discrepancy.

**Consequence.** Implement and run the frozen full uniform mature equivalence
forecast. Nonconforming AMR and production data remain unauthorized.

## 2026-09-15 - Pass full MFEM mature equivalence and unlock static AMR

**Decision.** Accept the MFEM conforming implementation as numerically
equivalent to the frozen DOLFINx method over the complete 320-step mature
forecast. Authorize the predeclared fixed nonconforming-hexahedral AMR branch.

**Evidence.** Immutable run
`runs/mfem-mature-uniform-equivalence/20260915T193445Z` passes every gate. The
shared initial field differs by `4.15e-16` in common-grid L1 and the final fields
by `5.26e-11`; mean and covariance errors are `8.04e-12` and `3.70e-11`.
Mean and maximum relative local-QP corrections agree within `7.52e-15` and
`1.72e-13`. Maximum absolute mass error is `3.98e-13`, with zero optimizer
failures and fallbacks under fail-closed execution. The original positivity
field was inferred from the projection code path; a second run now counts the
cell certificates explicitly at every step before closing that measurement.

**Consequence.** Construct one replay-driven static `NCMesh`, then test it
against the fine graded reference under the frozen `D_AMR,gf < 0.05`, positivity,
statistics, correction and resource gates. Production dataset authorization
remains false until mature-density convergence and domain sensitivity pass.

## 2026-09-15 - Use full-trajectory indicators for the third graded level

**Decision.** Keep `MATURE_DENSITY_CONVERGENCE = OPEN` and freeze every method
parameter except the mesh. Build the third graded mesh from eleven deterministic
replay snapshots over all 320 steps. Use a componentwise time maximum of
normalized QP correction, negative-witness probability, high-mode content and
jump indicators. Dörfler marking uses `theta=0.5`; contiguous tensor bands retain
the highest predeclared axis energy coverage that stays within the uniform-60
cell ceiling.

**Evidence.** The completed `58x68x56` run reduces mean QP correction from
`8.31e-4` to `1.13e-4` and affected probability from `0.428` to `0.00418`, while
`D_60,gf=0.108680` and `D_g,gf=0.107936`. All positivity, conservation,
optimizer and statistical gates pass. Runtime is 76.4 minutes, 10.1% above
uniform-60, so the formal efficiency classification remains failed.

**Consequence.** Predeclare `D_gf,gff < 0.0543401` as the primary contraction
gate. Mean correction remains limited to `8e-4`; invariant/statistical gates
remain unchanged. Runtime, memory and cell count are compared with uniform-60.
The observed nonuniform-mesh rate remains heuristic.

**Evidence.** Immutable run
`runs/mature-full-spd-graded-fine-comparison/20260914T231639Z` and executable
pipeline `experiments/mature-time-aggregated-level3-pipeline.yaml`.

## 2026-09-15 - Validate static grading for efficiency and open density convergence

**Decision.** Set
`METHOD_STATUS = MATURE_STATE_STATISTICAL_AND_POSITIVITY_GATES_PASSED`,
`MATURE_DENSITY_CONVERGENCE = OPEN`,
`MATURE_GRADED_EFFICIENCY = SUPPORTED_NOT_CERTIFIED`, and
`NEXT_REQUIRED_GATE = MATURE_DENSITY_CONVERGENCE`. Production dataset
generation remains unauthorized.

**Evidence.** Uniform `60x72x72` passes the original mature mean-correction
limit with `0.0008313` and passes positivity, conservation, optimizer,
covariance, marginal, joint-TV and lobe tests. Static `44x52x46` grading
reproduces its full density to common-grid `L1=0.001688`, while reducing DG
unknowns by `66.2%`, runtime by `53.0%`, and peak memory per rank by `61.7%`.
The graded run's `0.0008384` mean correction remains a formal failure against
its separately predeclared `0.0008` efficiency threshold. A reported marginal
degradation failure compared different histogram resolutions; matched-grid
recomputation gives a maximum increase of `1.75e-4`, below the `0.005` limit.

**Consequence.** Static grading is supported as an efficient reproduction of
uniform-60. The historical coarse mature hierarchy and graded `0.0008` failure
remain immutable evidence. The next controlled test increases only the lobe
resolution on `58x68x56`, compares against uniform-60 and the first graded run,
and retains all positivity/statistical/cost gates.

**Evidence file.** `mature_graded_efficiency_report.json`.

## 2026-09-13 - Reject certificate depth as mature-state failure cause

**Decision.** Deprioritize deeper Bernstein subdivision and promote an
operator-level positive low-order/AFC treatment as the next research branch.
Retain `FULL_SPD_DIFFUSION_CERTIFIED`, `NEXT_REQUIRED_GATE = MATURE_STATE`, and
no production dataset authorization.

**Evidence.** On identical raw initialization and forecast polynomials across
all three meshes, increasing adaptive certification depth from 4 to 8 rescues
at most `0.0788%` of depth-4 non-certified cells. Mean L1 correction reduction
is `0.779%` and the maximum is `2.89%`, triggering the predeclared rejection
rule. Almost every non-certified cell is `WITNESSED_NEGATIVE`; unresolved cells
are negligible. The local QP remains useful as a comparator because scalar
limiting changes L1 by `1.96x` to `6.70x` more.

**Consequence.** Do not rerun the mature hierarchy with deeper certificates.
The next controlled implementation should prevent or locally correct the
negative update at operator/flux level, then compare accuracy and correction
against the immutable mature local-QP failure.

**Evidence file.** `mature_positivity_certificate_diagnostic_report.json`.

## 2026-09-13 - Retain mature-state gate after bimodal failure

**Decision.** Keep `METHOD_STATUS = FULL_SPD_DIFFUSION_CERTIFIED`, keep
`PRODUCTION_DATASET_AUTHORIZED = false`, and keep
`NEXT_REQUIRED_GATE = MATURE_STATE`.

**Evidence.** The first full-SPD mature bimodal hierarchy completes all 960
steps with zero measured negative mass, optimizer failures or fallbacks. Density
differences decrease `0.42059 -> 0.35373`, giving observed common-grid rate
`0.42695`; covariance, marginal, lobe and smoothed joint-density gates pass.
Mean relative L1 corrections decrease `0.003047 -> 0.002789 -> 0.001840`, but
all exceed the predeclared `0.001` limit. Initial projection corrections are
also material: `0.380`, `0.158` and `0.0313`.

**Consequence.** Do not advance to domain sensitivity or a pilot dataset.
Diagnose whether the frozen mature law requires finer/nonuniform resolution or
whether the positivity architecture remains too active in this regime. Preserve
the failed run as the comparator and predeclare any follow-up before execution.

**Evidence file.** `local_q2_mature_bimodal_report.json`.

## 2026-09-13 - Promote local-QP CN to mature-state certification

The predeclared non-diagonal full-SPD hierarchy passes. Common-grid L1
differences decrease from `0.139500` to `0.0348401`, yielding observed rate
`3.4215`. All 960 steps are whole-cell certified with zero measured negative
mass, optimizer failure or fallback. Maximum absolute mass error is `3.87e-12`.
Normalized covariance discrepancies decrease from `0.02879` to `0.004163` to
`0.002261`; off-diagonal covariance and correlation errors remain within their
fixed gates. The finest covariance discrepancy is below the strengthened
one-million-particle bootstrap p95 `0.002735`.

This confirms the full-SPD direction in the earlier 2026-09-13 decision and
sets status `FULL_SPD_DIFFUSION_CERTIFIED`. Treat `3.4215` as an observed
common-grid rate rather than a proved formal order. Dataset generation remains
unauthorized. The next required gate is a mature later-time or post-analysis
density, followed by domain-size sensitivity.

## 2026-09-13 - Promote local-QP CN to full-SPD certification

The predeclared identity-noise spatial hierarchy passes. Exact common-grid L1
differences decrease from `0.141394` to `0.0355845`, giving observed rate
`3.4026`. All 960 timesteps are whole-cell Bernstein-certified with zero
measured negative mass, optimizer failure or fallback; maximum final mass error
is `1.20e-11`. Treat `3.4026` as an observed common-grid rate rather than a
proved formal order.

This supersedes the spatial-pending portion of the 2026-09-12 decision and sets
the status to `SPATIAL_POSITIVITY_CERTIFIED`. Dataset generation remains
unauthorized. The next gate is `FULL_SPD_DIFFUSION`: first run the frozen
candidate at `30x36x36`, then conditionally run the complete spatial hierarchy
under the predeclared non-diagonal diffusion tensor. The strengthened reference
uses one million common-random-number particles, 1,000 bootstrap replicates and
one fixed bootstrap seed. Exact specifications are
`experiments/local-q2-cn-full-spd-controlled.yaml` and
`experiments/local-q2-cn-full-spd-spatial-refinement.yaml`.

The controlled `30x36x36` run subsequently passed all of its fixed gates:
normalized covariance error `0.004163`, maximum off-diagonal covariance and
correlation errors `0.003806` and `0.007067`, mean relative L1 correction
`7.61e-5`, zero measured negative mass, zero optimizer failure/fallback and
absolute mass error `3.86e-12`. This activates the conditional full-SPD spatial
hierarchy without changing production authorization.

## 2026-09-12 - Promote local-QP CN to spatial certification

The tight full/half/quarter/eighth diagnostic passes all predeclared dynamic
gates. Adjacent density differences are `5.238e-4`, `5.418e-4`, and
`1.620e-4`; the final consecutive order is `1.741`. All 1,200 timesteps are
whole-cell Bernstein-certified, with zero measured negative mass, optimizer
failure or fallback. Maximum terminal mass error is `1.87e-11`.

This supersedes the three-level decision that retained local QP only as a
comparator and narrows the active classification to
`TEMPORAL_POSITIVITY_CERTIFIED`. Dataset generation remains unauthorized.
Freeze the solver and run the predeclared constant-ratio spatial hierarchy in
`experiments/local-q2-cn-spatial-refinement.yaml`; use its temporal safeguard
before interpreting a finest spatial difference below `8.1e-4`.

## 2026-09-12 - Run one tighter-solve local-QP refinement before AFC

Narrow the 2026-09-11 decision that made operator-level AFC the immediate next
experiment. The local-QP dynamic run reduced the global-scaling density
discrepancy by about 20.8 times, kept every step positive, and showed a mean
correction proportional to the timestep across the three tested levels. Those
facts support one further falsification test before undertaking the larger AFC
redesign; they do not establish convergence.

Rerun full, half, quarter, and new eighth timestep branches with forecast KSP
`rtol=1e-12` and `atol=1e-15`. Rerunning all four levels controls the comparison
after changing solver tolerances and tests whether the prior absolute mass
failures were linear-solve effects. Retain the existing positivity, correction
mass, covariance, adjacent-density, and absolute-mass gates. The decisive
temporal condition is
`L1(quarter,eighth) < L1(half,quarter)`, equivalently positive observed order
on the final three levels. Passing advances the candidate only to spatial and
full-SPD testing; it does not authorize dataset generation or prove an
asymptotic rate. Failure returns priority to adaptive constraint generation or
operator-level low-order/AFC correction, according to the resulting failure
mode. The exact predeclaration is
`experiments/local-q2-cn-tight-ksp-refinement.yaml`.

## 2026-09-11 - Run a terminal-state local-QP isolation study before in-loop AFC

Implement a cell-local mass-matrix projection of Q2 coefficients onto fixed
`2x2x2` control-subcell Bernstein inequalities while preserving each feasible
cell average. Adaptive subdivision may skip raw cells already certified
non-negative, but the QP constraint matrix remains fixed during each solve.
This makes the nearest-point comparison with scalar scaling a genuine convex
quadratic program.

The final unlimited Crank--Nicolson states already show a hard limit: 17,515
full-step and 17,572 half-step cells have negative averages, with total negative
average mass `4.341e-6` and `4.344e-6`. A pure cell-local mass-preserving
projection is infeasible there. The diagnostic therefore compares (i) pure
local QP with those cells explicitly retained and flagged, and (ii) the
incumbent conservative Stage-1 average repair followed by local QP. It does not
feed corrections into later steps. Only a favourable terminal result can
justify a later in-loop experiment; material average transfer or dynamic
failure moves the project to a positive low-order flux/AFC construction.

## 2026-09-11 - Advance Stage-1 plus local QP to an in-loop diagnostic

The clean terminal-state run `20260911T114957Z` fully certifies the hybrid at
both timestep levels and measures zero negative mass. Covariance errors are
`0.0058764` and `0.0058742`; the cross-timestep density difference is
`3.943e-5`. The QP correction objective is about 17% of matched scalar scaling,
and the terminal L1 correction falls from about `0.03937` to `0.01618`.

These results justify a dynamic test while leaving production classification
unchanged. Predeclare three timestep levels so repeated-projection effects and
an observed temporal order are visible. Scalar fallback after optimizer failure
must remain explicit. If the dynamic trajectory loses the terminal advantage,
stop post-step projection development and construct the positive low-order
full-SPD flux/AFC comparator.

The in-loop implementation passes a short whole-cell certification and mass
smoke test. A production-mesh profile with one numerical-library thread per MPI
rank takes `49.6 s` for three steps; local projection time grows from `14.7 s`
to `16.3 s` as projected cells grow from 4,451 to 8,882. A prior eight-step
profile without warm starts reached 11,305 projected cells and `27.3 s` of
projection time at step eight. The full three-level experiment remains
predeclared, but generic per-cell SLSQP is too costly for a responsible
brute-force run. Preserve the mathematical problem and replace the optimizer
with a verified specialized or batched implementation before executing it.

## 2026-09-11 - Retain Q2 as a challenger but withhold production selection

Status: superseded as numerical evidence by the invariant audit below; its run
artifacts remain immutable diagnostic history.

The controlled same-mesh experiment resolves the earlier degree confound.
Adaptive-certificate Q2 reduced corrected covariance error from `0.08719` for
Q1 to `0.02377`, improved every marginal TV, and met the forecast correction
gates. Fixed-subcell Q2 reached `0.03483`; adaptive certification therefore had
a material effect rather than merely relabelling cells.

The complete gate still failed. Halving the timestep changed the conservative
three-subcell density by `L1=0.01552`, which is already a lower bound on the
polynomial L1 difference and exceeds the `0.0025` gate. The half-step mass error
was `2.56e-10`, above `1e-10`, although covariance-error change passed at
`0.00159`. Do not certify Q2 or generate production data. Before committing to
AFC, compare truly unlimited Q2 at both timesteps; the raw states recorded in a
limited trajectory still inherit all previous corrections and cannot isolate
time discretisation from accumulated limiting.

## 2026-09-11 - Repair the limiter invariant and rerun the Q2 decision

An independent audit found that the final unconstrained roundoff correction in
Stage 1 could push extremely small active cell averages below zero. In the
first adaptive-Q2 step this produced a minimum average near `-1.92e-22` and a
negative Stage-2 scaling factor. The prior numerical gate decision is therefore
superseded pending a replacement run.

The Stage-1 residual repair now contracts non-negative slacks when mass must be
removed and applies a guarded one-cell ulp repair. Stage-2 scaling is explicitly
clamped to `[0,1]`. The reported `corrected_fraction` now counts the union of
cells changed by either stage; separate Stage-1 and Stage-2 fractions are also
recorded. The replacement comparison and the truly unlimited two-timestep
diagnostic were predeclared before evaluation.

## 2026-09-11 - Retain local QP as comparator and advance operator-level correction

The reduced fixed-matrix OSQP implementation passed all predeclared engineering
gates on 2,413 saved and randomized cell problems. It solved every problem,
agreed with successful SLSQP objectives to `3.76e-10` relative, and was `12.51`
times faster. The matched three-step production-mesh projection speedup was
`10.78`. This closes optimizer cost as the immediate blocker without changing
the cell objective or positivity constraints.

The resulting three-level in-loop run does not pass its complete scientific
decision. Every one of 560 steps is whole-cell certified, has zero measured
negative mass, and uses no fallback. Covariance errors remain near `0.0075`,
and adjacent density differences `5.24e-4` and `5.42e-4` both pass the absolute
`0.0025` gate. Because the second difference is slightly larger, observed
order is `-0.0488`, failing the predeclared positive-order requirement. Full
and quarter absolute mass errors also narrowly exceed `1e-10`; per-projection
mass changes remain below `8e-15`, so accumulated linear-solve drift is the
supported attribution for those mass misses.

Do not relax the gates or advance this post-step method to dataset
certification. Retain it as the strongest current non-negative comparator and
move the leading correction branch to a positive low-order full-SPD update with
local conservative flux/AFC correction. Dataset generation remains blocked.

## 2026-09-11 - Attribute only part of Q2 timestep sensitivity to limiting

The corrected replacement run reproduced the prior branch metrics to roundoff
with all recorded scaling factors in `[0,1]` and non-negative corrected cell
averages. Its cross-timestep density lower bound remains `0.01552` and the
half-step mass error remains `2.56e-10`, so Q2 remains uncertified.

The truly unlimited backward-Euler Q2 pair also fails the density timestep gate:
its conservative subcell lower bound is `0.00541` versus the `0.0025` limit.
Global positivity correction increases the corrected discrepancy by a factor
of about `2.87`, but the unlimited failure rules out correction as the sole
cause. Unlimited Q2 has lower covariance errors (`0.00727` and `0.00464`) while
carrying integrated negative mass of `7.23e-4` and `7.73e-4`. Proceed to a
predeclared unlimited Crank--Nicolson two-timestep diagnostic; close the present
uniform-mesh DG branch if second-order time integration also fails.

## 2026-09-11 - Retain Q2 after the Crank--Nicolson temporal diagnostic

Unlimited Crank--Nicolson Q2 passes the two predeclared timestep gates. Halving
`dt` changes the conservative subcell density by only `4.19e-5` and covariance
error by `4.74e-6`. Both trajectories have covariance error about `0.00371`,
below the common Monte Carlo bootstrap p95, but integrated negative mass remains
about `8.28e-4`. This supports retaining the uniform-mesh Q2 spatial branch and
shifts the main effort toward a positivity treatment compatible with the
second-order trajectory. First run the existing adaptive global limiter as a
controlled comparator; it is not presumed to preserve this improvement.

## 2026-09-11 - Reject global scaling for the Crank--Nicolson Q2 path

Adaptive global correction changes the successful unlimited Crank--Nicolson
timestep result from `L1>=4.19e-5` to `L1>=0.01088`, failing the `0.0025` gate.
The full-step corrected mass error is `1.27e-10`, also above its gate. Covariance,
marginal, negativity and limiter-impact metrics pass, but they do not override
the density and conservation failures. Global scaling remains an audit
comparator and is rejected as the production correction for this path.

Proceed to a local conservative correction only after defining a genuinely
positive low-order update for the full drift-diffusion operator. Published
convex-limiting results for hyperbolic systems and local DDG flux corrections
for gradient-flow Fokker--Planck equations motivate architectures; their proofs
do not directly cover this fully implicit SIPG, full-SPD Lorenz operator or
Crank--Nicolson step.

## 2026-09-10 - Implement the predeclared Q2 diagnostic without relaxing positivity

The same-mesh experiment now has fixed and adaptive Bernstein branches. The
adaptive branch skips scaling only for cells certified non-negative after exact
de Casteljau subdivision; witnessed-negative and depth-limited unresolved cells
retain the fixed `2x2x2` conservative scaling. Raw Q2 coefficients before every
correction, final per-cell classifications, correction norms, negative-mass
quadrature estimates, time and memory are retained in immutable runs. This is
an experimental comparator and does not change the production classification.

## 2026-09-10 - Gate the next implementation on a same-mesh Q2 falsification

The existing Q1/Q2 comparison is insufficient to rank polynomial degree because
it held total DOFs fixed while Q2 used 1.5-times-wider cells in every direction
and twice the timestep. Before implementing a new solver family, compare Q1 and
Q2 on the same `30x36x36` mesh and `dt=0.000625`, starting from the same positive
represented Q1 law embedded exactly in Q2. Audit raw Q2 polynomials before
correction and separate cell-average from high-order changes.

Adaptive Bernstein subdivision is authorized for this diagnostic as a rigorous
sufficient certificate. It is not selected as a complete production positivity
test because negative coefficients are inconclusive and non-negative polynomials
with zeros may remain uncertified under arbitrary subdivision.

If raw Q2 is accurate but correction fails, the next architecture is local
conservative flux correction/AFC. If raw Q2 fails, close that branch and test a
positive full-tensor finite-volume/flux method. Detailed gates are predeclared in
`METHOD_SELECTION_REPORT.md`.

## 2026-09-10 - Require general full-SPD production diffusion

The production target must ultimately support a constant general `3 x 3` noise
matrix and therefore mixed derivatives in full SPD `D=BB^T/2`. This supersedes
the unresolved production-scope part of the 2026-09-09 challenger-priority
decision. Identity noise remains the controlled experiment. Directional FCDF,
Chang--Cooper and complete-flux variants remain valid special-case challengers,
but diagonal-only theory cannot certify the general production role.

## 2026-09-10 - Assign solver roles separately

No production reference solver is certified. Q1 remains the baseline. A
dynamically scaled whole-space Hermite-Galerkin method is the preferred future
independent deterministic reference because it changes both discretization and
boundary treatment; it must be validated by spectral and moment convergence and
is not presumed positive.

## 2026-09-09 - Keep the scaffold and method selection deliberately open

All version-controlled code and living documents may be edited when evidence
or a task makes them stale. Q1 DG remains a controlled comparator, not the
project's mandated destination. Future work should maintain competing method
hypotheses and may introduce repaired Q2/AFC, adaptive certification,
complete-flux/FCDF, characteristic, goal-oriented, spectral, Monte Carlo, or
hybrid approaches. Scientific integrity, raw-data preservation, and provenance
remain durable safeguards; implementation restrictions and rankings do not.

## 2026-09-09 - Dataset generation remains blocked

Classification is `INSUFFICIENT_EVIDENCE`; do not scale up dataset generation.
The short-time covariance discrepancy remains substantially above Monte Carlo
sampling uncertainty, and mature-state validation is missing.

## 2026-09-09 - Preserve Q1 as the interim comparator

Use Q1 upwind/SIPG, backward Euler, quadrature-14 L2 initialization, projected
Bayesian analysis, and the conservative limiter for further controlled tests.
This is a comparison baseline, not a production endorsement.

Status: active for comparison, explicitly non-exclusive.

## 2026-09-09 - Do not reject higher order on the existing Q2 result

The current Q2 result tests a particular fixed-subcell Bernstein certificate
and scaling strategy. That positivity treatment can erase the moment advantage
of the unlimited Q2 projection; it does not establish that Q2 itself is worse.

The next Q2 branch should first distinguish failed positivity certification
from genuine negativity, then compare less intrusive corrections on equal
physical meshes.

## 2026-09-09 - Challenger priority depends on the production noise model

If production `B` is identity or diagonal, directional FCDF and
Scharfetter--Gummel/complete-flux candidates become especially relevant. If
arbitrary full `B` is required, repaired high-order DG/AFC and full-tensor flux
methods receive higher priority. This scope is unresolved and must remain
branch-specific until established.

## 2026-09-09 - Use micromamba rather than uv for the numerical runtime

DOLFINx, PETSc, MPI, and their compiled ABI-compatible dependencies are already
provided by the conda-forge `pde` environment. `environment.yml` pins the direct
runtime and verification tools, while `environment-linux-64.lock` records exact
artifacts for this platform. This adapts the guides' deterministic-environment
requirement to the compiled FEniCSx stack.
