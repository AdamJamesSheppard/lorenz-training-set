# G02 grid-independent finite-control review

2026-10-06, OL-D019. Post-hoc analysis, without scientific pass/fail criteria.
Method: paired_box_l1_bound, project derivation in
../RECONSTRUCTION_QUALIFICATION_PROPOSAL_V3.md; implementation
operator_learning/reconstruction_controls.py. Reproducible read-only audit:

```bash
./scripts/run-in-env python scripts/audit_reconstruction_bounds.py runs/operator-learning/OL-G02_reconstruction_mechanism_v3/20261006T120426434502Z
```

Exact mathematical inequality: mixture L1 is bounded by the mean of
2[1-product_d(1-|a_d-b_d|/w_d)_+]. Its numerical evaluation uses float64;
an interval-certified rounding enclosure is not claimed. Fixed widths
w=(4,40/9,40/9), all six recorded windows, no exclusions. All 21 source seals
verify. Compact numeric/provenance record: G02_BOUND_REVIEW_20261006.json.
Raw paths remain ignored/local, unchanged; this report does not make them portable.

## Findings and interpretation

Over every sampling phase, the largest finite-control whole-space L1 upper
bounds are 0.052142081453 for 5000 versus 20000 points and 0.017535448460
for 10000 versus 20000. Corresponding TV upper bounds are 0.026071040727
and 0.008767724230. These upper bounds can be loose: they do not demonstrate
actual errors of those magnitudes or a failed tolerance.

With identical physical times, dt=.001 versus .0005 has maximum L1 upper
bound 1.747580015e-6. Coarse index j pairs with fine index 2j+1 because
saved paths start at t=dt. Repeating coarse samples to compare with the
complete fine path would conflate integration error with temporal sampling.
This aligned comparison isolates two finite integrations; it cannot bound
the unknown exact trajectory or chaotic burn-in.

The empirical_v4 grid discrepancy (median 5000-point L1 0.0008775) remains
valid within its reported resolution. Conservative averaging contracts L1;
it alone cannot justify a whole-density error budget. The paired bound is
independent of comparison-grid resolution and supplies complementary evidence.

## Next qualification requirements

Retain bin-free reconstruction as the approved candidate with reservations.
Do not increase bandwidth to obtain an easier pass. 5000 and 10000 points
remain competing sampling recipes; selecting one from these development
diagnostics requires a fresh frozen qualification experiment.

Before that experiment, approve the intended downstream full-density TV
accuracy and the fraction allocated to reconstruction, plus statistical
tolerances and finite-control versus continuum scope. No budget is derived
from the current FNO's errors or chosen to accommodate these observed bounds.
Then freeze fresh windows, phases and controls, preserving every attempted law.
Actual posterior smoothing and changed FE/learning transfers remain separate.

Review: implementing-agent self-review under owner's continuation instruction;
no independent assessor. G02 OPEN, later gates LOCKED; no target generation,
training or assimilation authorization.

External research context checked during this review:
[Masry, kernel estimation under weak dependence with sampled data](https://www.sciencedirect.com/science/article/pii/S0378375896001516).
Only publisher abstract/context was inspected: temporal dependence matters.
No mixing hypothesis for the recorded Lorenz paths was verified, and no theorem
from that paper supplies this project's finite-control bound or acceptance budget.
