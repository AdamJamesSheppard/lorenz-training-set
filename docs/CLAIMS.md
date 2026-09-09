# Claim registry

Evidence classes: `ESTABLISHED` (supported by derivation and targeted tests),
`NUMERICAL`, `EMPIRICAL`, `HEURISTIC`, `CONJECTURE`, `OPEN`, `REJECTED`.

| ID | Claim | Class | Evidence | Falsification / limitation |
|---|---|---|---|---|
| C-001 | The implemented split DG form represents zero total boundary flux. | ESTABLISHED | `NUMERICAL_METHOD.md`; `boundary_flux_report.json` | A manufactured total-flux case fails convergence or mass conservation. |
| C-002 | The Q1 limiter preserves global mass and produces a non-negative polynomial on affine cells. | ESTABLISHED | `POSITIVITY_AUDIT.md`; limiter and smoke tests | Curved/non-affine cells or a failed coefficient/mass invariant are outside or refute the claim. |
| C-003 | The current best Q1 configuration is accurate enough for production dataset generation. | REJECTED | `method_selection_report.json` | Current covariance error is 13.62 times the MC noise p95. |
| C-004 | Fixed-subcell Q2 Bernstein limiting demonstrates that Q2 is intrinsically inferior. | REJECTED | `METHOD_SELECTION_REPORT.md`; Q2 reports | The certificate is sufficient, not necessary, and may over-limit. |
| C-005 | Q1 can meet all mature-state acceptance gates at a finer aligned mesh. | OPEN | `experiments/mature-state-decision.yaml` | Any predeclared covariance, limiter, boundary, temporal, or reference gate fails. |
| C-006 | Existing Monte Carlo output defines a stable full 3-D density target. | REJECTED | `method_selection_report.json` | Histogram/KDE reconstruction remains sample- and bandwidth-sensitive. |

