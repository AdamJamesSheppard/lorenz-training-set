# G03 hierarchical implementation validation — OL-D025

2026-10-06. No scientific execution or gate promotion.
Runner scripts/run_input_coverage.py; experiment
experiments/operator_learning/OL-G03_input_coverage_characterization_v2.json;
method/source record INPUT_COVERAGE_G03_V2_PROPOSAL.md (engineering design with
TV project derivation and prospective Rolf et al.2021 context/applicability gaps).

Fast checks predicted under10seconds cumulatively; observed combined shell
runtime.84seconds. Governance, research attribution, graph and diff-whitespace
checks pass. Operator-learning suite81passed/1skipped in.49seconds.
New tests exercise group isolation, missing-query denominators, conditional
reconstruction eligibility, boundary fractional overlap on different grids and
frozen config/order validation. These are inexpensive software checks, not a
36-law scientific run or evidence that population coverage passes.

Full-run provisional ETA5–15minutes, extrapolating G02 six-law31.1seconds,
G03 six-law21.7seconds and larger path generation/630 compressed-array pair I/O.
No measured new-run timing is claimed. AGENTS.md requires immediate handoff
after a verified persistent launch when individual OR cumulative related-job
ETA exceeds one minute. No sub-minute job-chain workaround.

Run launch blocked until committed predeclaration: session.git is read-only.
No staging/commit/launch attempted under this restriction. Implementation and
prior adjudication remain working-tree changes; original ignored scientific
payloads unchanged and unrelated plotting script preserved.

After write access is available, review/commit all intentional phase-A changes,
then prepare via the frozen config and launch its recorded argv persistently.
The runner rejects uncommitted config, tracked dirt, undeclared untracked files,
source-hash or runtime/thread mismatch, and reuse of a started run.
