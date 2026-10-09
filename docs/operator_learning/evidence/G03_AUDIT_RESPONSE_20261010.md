# G03 owner-supplied audit and reporting correction — OL-D033

2026-10-10. Owner supplied an external audit of commit71a902a and accepts the
scoped PASS. Auditor identity, tools and execution environment are not supplied;
independent recalculation is reported by the owner, not independently certified
by this response. Implementing-agent verification/correction is self-review.
Original run/config/report/provenance/seals remain byte-identical. G03 remains
PASSED for finite-window separation only; next gate G04 remains OPEN.

## Confirmed reporting discrepancy

Across the96 recorded phase mass values, max |mass-1| equals
3.1086244689504383e-15 at seed83510_window0, phase1, mass1.000000000000003.
The earlier2.886579864025407e-15 summary came from a separate grid-integral
recomputation and was incorrectly presented without distinguishing that metric
from the producer's recorded raw mass. The difference is2.220446049250313e-16.
The corrected recorded maximum is still below the unchanged1e-10 criterion.
The new summary JSON explicitly names the metric and its source-report hash.
Regression tests recompute the maximum from every recorded phase. This verifies
report-summary arithmetic; it does not independently establish the raw arrays.

## Audit assessment and unresolved work

The prospective v4 definition was frozen after favourable characterization;
its weak witness rule is a replication/non-collapse criterion, not a surprising
generalization result. Actual276 positive margins exceed the frozen criterion;
that stronger observation is not a new retrospective requirement.

Within-source window median TV .296723 and cross-source median .322361 are
descriptive dependent-pair statistics. They demonstrate finite-window variation;
their difference does not identify an independent causal source effect or prove
coverage. No claim of24 fundamentally distinct law classes is warranted.

Track these unresolved issues without treating recommendations as executed:

- Fresh v4 has two windows/source. Earlier v3 retained all three windows on
  historical sources. A fresh three-window robustness study needs its own
  predeclaration and ETA; its result must not replace v4 retrospectively.
- An independent raw-array verifier should integrate voxel fields and compute
  TV/within-phase distances without production metric helpers. Independent
  density reconstruction/export requires separate implementation review.
- The evaluator does not consume within-phase comparisons; count checking and
  finite-control bounds do not independently verify those144 numeric values.
- GitHub holds compact reports and hashes, not all64 sealed payloads. Full
  independent reproduction and preservation require access to the large arrays
  or a versioned archive. No archive/upload or backup is claimed here.
- Shared helpers and mutually consistent canonical documents provide weaker
  verification than independent code plus accessible original artifacts.

These remain limitations rather than a retroactive new failure condition.
G04 design may proceed; no large targets, training, production or DA authorized.
No new experiment starts in this correction task.

Attribution: owner-supplied audit (2026-10-10), local committed report arithmetic,
and existing G03_QUALIFICATION_V4.md method/TV sources. Archival context only:
Klump et al.(2020), Principles and best practices in data versioning for all
datasets big and small, version1.1, https://doi.org/10.15497/RDA00042 . This
supports documenting versioned corrections, not a scientific G03 theorem or
proof that the current payloads are durably archived.
