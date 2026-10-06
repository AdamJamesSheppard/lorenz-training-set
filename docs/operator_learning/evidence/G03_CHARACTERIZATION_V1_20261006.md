# G03 characterization review — OPEN, resolved finite-law variation

2026-10-06, OL-D024. Owner asks to continue G03. Implementing-agent self-review;
no independent assessor and no population-coverage promotion.
Predeclaration: abd8d14cef4f1f5a3a1ce737980150c3400be1f4.
Config: experiments/operator_learning/OL-G03_input_diversity_characterization_v1.json.
Immutable run: runs/operator-learning/OL-G03_input_diversity_characterization_v1/20261006T135528033588Z.
Method, derivation, sources and applicability: ../INPUT_DIVERSITY_G03_V1.md,
DIVERSITY_TV_MARGIN_V1; G02 paired-box bounds and conservative export.

## Verified outcomes

All16 seals, frozen config versus predeclaration commit and18 input hashes
verify. All72 within-law and30 between-law TV values independently recompute
from saved phase arrays within1e-12. This is a same-artifact numerical check,
not an independent implementation of the density estimator or an interval proof.
All12 law/grid attempts completed; no exclusions, retries or execution failures.
Raw mass maximum error5.773159728050814e-15; negative mass0. Elapsed21.745659s.
The producer records G03 OPEN; that immutable status is retained.

| Diagnostic | 60×72×72 | 120×144×144 |
|---|---:|---:|
|Within-law phase TV median|3.94854863e-5|6.04571230e-5|
|Within-law phase TV worst|5.61934922e-5|7.71642065e-5|
|Between-law TV median|.2399249694|.2475716352|
|Between-law TV minimum|.1187086584|.1245050594|
|Between-law TV worst|.6711384698|.6750150309|
|Minimum finite-control lower margin|.1060682971|.1118646982|
|Resolved pairs / attempted pairs|15/15|15/15|

The finest-grid between-law p90/p95 are.6409272248/.6735142943 (15 pairs,
descriptive quantiles, not population tail estimates). All phase/grid x>0
probabilities range.3080924337–.7735488766. Boundary regions have different
physical thickness on the two grids; their probabilities must not be treated
as a common-region convergence test.

## Decision and falsification

OL-C017: NUMERICAL. The six retained regularized finite occupation laws are
pairwise distinguishable against the declared finite-control reconstruction
bounds. Phase replicates are deterministic quadrature controls, not independent
laws. This addresses the hypothesis that these particular separations arise
solely from the measured reconstruction errors. It does not exclude unmeasured
law-generation error or establish continuum trajectory fidelity.

G03 remains OPEN: no population-coverage threshold was frozen. No arbitrary
quota or threshold is inferred from a successful-looking characterization.
Six laws cannot establish optimal dataset allocation, universal initial-condition
coverage, distinct attractors, posterior relevance or learned forecast accuracy.
Falsification includes seal mismatch, failed replay, invalid bounds or exporter,
and source/config correspondence failure. Genuine duplicates in a wider study
are retained evidence; no demand for all candidate laws to be separated.

## Provenance and next work

Portable CONFIG.JSON, PROVENANCE.JSON and SEAL.JSON copies with this prefix
match the originals. The complete report and12 phase-array archives remain
ignored local evidence, identified by the copied seal; GitHub alone cannot
reproduce all metrics without these payloads. Dirty provenance discloses only
the preserved unrelated untracked scripts/plot_reconstruction_comparison.py.

Next design: ../INPUT_COVERAGE_G03_V2_PROPOSAL.md. It is a proposed broader
characterization, not an executed or committed predeclaration. No FPE targets,
training or DA. REQ-RT-001 applies to its method/source/outcome records.
Current session exposes.git read-only, preventing a new Git predeclaration;
do not bypass that control or launch a working-tree-only experiment.
