# Window-local G03 implementation validation — OL-D027

2026-10-08. Working-tree implementation only, no scientific execution/promotion.
Method/source/scope: ../WINDOW_LOCAL_CONTROL_G03_V3.md and linked paired-box
derivation/TV attribution. Runner scripts/run_window_local_control.py; frozen
config experiments/operator_learning/OL-G03_window_local_control_v3.json.

Fast checks forecast under10s combined, observed.84s. Commands:
python3 scripts/research_graph.py --build --check;
python3 scripts/check_operator_learning.py;
python3 scripts/audit_research_sources.py;
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
/home/adam/.local/share/mamba/envs/pde/bin/python -m pytest -q tests/operator_learning;
git diff --check. Outcome: governance/attribution/graph/whitespace checks pass;
83 tests passed,1 skipped in.50s. Tests verify the pre-sample window boundary,
invalid window rejection and exact fine replay for a small deterministic path.
No36-law replay or numerical-control outcome is claimed from these unit tests.

Provisional scientific runtime2–4minutes after future launch, based on v2's
115.8s and new36 local fine/coarse replays, excluding old voxel/pair I/O.
No completion ETA applies now: phase-A commit and launch blocked by current
read-only.git policy. Preserve unrelated plotting script; do not bypass Git
predeclaration or alter the source run. G03 remains OPEN.
