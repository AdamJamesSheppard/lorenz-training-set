# Window-local integration control — G03 v3

2026-10-08, OL-D027. Owner requests continuation of the recommended diagnostic.
Implementation pending committed predeclaration; no gate promotion or dispatch.
Method WINDOW_LOCAL_RK4_CONTROL_V3, original project diagnostic design.
Scientific question: does window-local integration account for the12 unresolved
third windows without changing the36 recorded input laws?

Source: sealed G03 v2 run20261006T190016632767Z at commitfdce138.
Retain all12 source groups,36 laws, widths,20k phases and80k fine controls.
For window0 use saved post-spinup initial state; for later windows use the
saved fine state IMMEDIATELY BEFORE the first sample. Restart fine/coarse RK4
from that identical state for10 units. Require bitwise fine replay against
the archived80k samples; failure is recorded, never repaired by replacing them.
Save new coarse paths only in a new immutable run. Recompute the same G02
paired-box sampling/integration bounds, compare side-by-side with original
accumulated controls, preserve old failures and every attempt. No density,
regularization, input allocation, original control or model is changed.

Fixed1% sufficient bound is a diagnostic inherited from G02, not a new G03
coverage threshold. A bound above1% is insufficient certification, not proof
of actual error above1%. Passing local controls does not establish accuracy of
the full30-unit trajectory from its original initial state, invariant measures,
continuum accuracy, posterior coverage or independent samples. It conditions
on the saved numerical window-start state. Coverage remains a separate question.
G03 stays OPEN, later gates LOCKED. No FPE targets, training or DA.

Methods/sources: paired-box triangle/overlap derivation in
RECONSTRUCTION_QUALIFICATION_PROPOSAL_V3.md; RK4/restart implementation in
operator_learning/reconstruction_controls.py; TV conventions and contractivity
in INPUT_DIVERSITY_G03_V1.md with Canonne Lecture11. No new theorem imported.
Competing explanations: accumulated integration separation dominates; some
windows remain sensitive even locally; conservative upper bound is loose.
Report every36 attempts, bitwise replay, sampling/local/global bounds, failures,
runtime, config/source/input/output hashes and seals. Review is implementing-
agent self-review under owner instruction; no independent assessor.

Runner scripts/run_window_local_control.py; tests test_window_local_control.py;
config experiments/operator_learning/OL-G03_window_local_control_v3.json.
Reuses strict grouped-programme preparation; committed config, clean tracked
source, declared untracked exception and matching source hashes required.
All88 v2 source seals are verified before use. Archived observations are
development evidence, not untouched evaluation.
Provisional runtime2–4minutes based on v2's115.8seconds and36 local fine/coarse
replays without voxel reconstruction/pair I/O. Fast tests estimated under10s
cumulatively. Hand back immediately after verified persistent launch.
Earlier session.git was read-only; OL-D028 restores committed dispatch under
the owner's continuation instruction. No predeclaration bypass is permitted.
