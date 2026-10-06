# G02 adjudication: PASSED_SCOPED_FINITE_CONTROL_V5

2026-10-06, OL-D021. Owner explicitly requests adjudication after approving
the1% TV criterion. Implementing-agent self-review; no independent assessor.
Predeclaration commit651eec5aa781148b1b2fcc966681a0e8cf34dd07.
Frozen experiment: experiments/operator_learning/OL-G02_reconstruction_qualification_v5.json.
Run: runs/operator-learning/OL-G02_reconstruction_qualification_v5/20261006T132432282684Z.
Method/source/derivation/assumptions: ../RECONSTRUCTION_QUALIFICATION_V5.md and
../RECONSTRUCTION_QUALIFICATION_PROPOSAL_V3.md; no additional theorem imported.

## Decision and unchanged criteria

Accept the20k deterministic endpoint-phase bin-free box-mixture candidate for
SCOPED reconstruction stability versus the80k finite control on six fresh
windows. Every sampling phase was tested. Acceptance adds worst-phase sampling
TV, worst matched-time integration TV and frozen1e-10 safety allowance.
Every20k case is below.01; every required technical invariant passes.
G02 becomes PASSED within this scope; G03 opens for diversity design only.
Older characterization-only experiments remain non-qualifying history.

| Seed | 5k total TV upper | 10k total TV upper | 20k total TV upper |
|---|---:|---:|---:|
|82029|.03069358|.01444652|.00621782|
|82030|.03178906|.01496496|.00644156|
|82031|.03107064|.01462487|.00629478|
|82032|.03168974|.01491993|.00642254|
|82033|.02926870|.01377285|.00592724|
|82034|.03171597|.01493434|.00642919|

5k and10k fail the sufficient upper-bound certification criterion,6/6 each;
this does not prove their true TV exceeds.01. No attempt or failed component
was removed, and no threshold relaxed.20k passes6/6. No exclusions, execution
failures or retries. Elapsed31.136s. Maximum raw mass error1.5099e-14;
negative mass0. Twelve grid comparisons pass finite/nonnegative/raw mass checks.
Max grid L1=8.92574e-5, diagnostic only: averaging can hide subvoxel differences.
Whole-space coupled bounds drive the scientific criterion.

All22 seals verify. Frozen config equals its predeclaration commit; every listed
source hash matches that commit. All bounds recompute from saved paths. Both
RK4 paths and original/common initial states replay bitwise on declared runtime.
Tracked source tree was clean; dirty provenance records only unrelated untracked
scripts/plot_reconstruction_comparison.py, outside declared computation and
preserved unchanged. This disclosed exception is not a fully clean checkout.

## Scope, counterevidence and restrictions

Kernel-overlap identity and triangle inequality are project derivations;
float64 evaluation plus allowance is numerical evidence, not interval proof.
Widths(4,40/9,40/9), ten-unit windows and finite numerical controls are fixed.
No exact trajectory, continuum occupation measure, invariant-law, universal
initial-state, independent-time-sample or mixing theorem follows. Random
conditional reconstruction is outside this deterministic recipe.

Observed x>0 probabilities span ~.308–.774, but six seeds and that spread alone
cannot pass G03 diversity/coverage. Compare within-law reconstruction uncertainty
with between-law variation; retain difficult cases and avoid a common template.
Regularized density remains distinct from the raw empirical measure; no stronger
posterior or unsmoothed-attractor applicability claim is made.

G01's historical archived pipeline pass is unchanged. Changed bin-free FE
transfer requires explicit checks before expensive new targets. G04/G05 must
qualify target applicability and learning/export fidelity. G04–G17 stay LOCKED;
no training, target campaign, replacement, posterior transfer or DA authorization.

## Durable evidence and research

Portable CONFIG/PROVENANCE/SEAL/REPORT JSON copies with this prefix match original
hashes. Large paths/voxel arrays remain local ignored payloads identified by the
seal; GitHub does not contain them. Original producer status OPEN_PENDING_REVIEW
is immutable; this decision records adjudication without editing that run.

TV convention: Clément Canonne,Lecture11,Definition50.1/Fact50.2,
https://ccanonne.github.io/files/compx270-chap11.pdf. Used for event/TV semantics;
its i.i.d. learning results are not applied to correlated Lorenz samples.
Paired-box/RK4/overlap methods and limits were predeclared in v5; acceptance
tolerance is owner-approved engineering design, not sourced theorem.
