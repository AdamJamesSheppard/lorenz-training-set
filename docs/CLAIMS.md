# Claim registry

Evidence classes: `ESTABLISHED` (supported by derivation and targeted tests),
`NUMERICAL`, `EMPIRICAL`, `HEURISTIC`, `CONJECTURE`, `OPEN`, `REJECTED`.

| ID | Claim | Class | Evidence | Falsification / limitation |
|---|---|---|---|---|
| C-001 | The implemented split DG form represents zero total boundary flux. | ESTABLISHED | `NUMERICAL_METHOD.md`; `boundary_flux_report.json` | A manufactured total-flux case fails convergence or mass conservation. |
| C-002 | The Q1 limiter preserves global mass and produces a non-negative polynomial on affine cells. | ESTABLISHED | `POSITIVITY_AUDIT.md`; limiter and smoke tests | Curved/non-affine cells or a failed coefficient/mass invariant are outside or refute the claim. |
| C-003 | The current best Q1 configuration is accurate enough for production dataset generation. | REJECTED | `method_selection_report.json` | Current covariance error is 13.62 times the MC noise p95. |
| C-004 | Fixed-subcell Q2 Bernstein limiting demonstrates that Q2 is intrinsically inferior. | REJECTED | `METHOD_SELECTION_REPORT.md`; Q2 reports | The certificate is sufficient, not necessary, and may over-limit. |
| C-005 | At least one tested deterministic or hybrid candidate can meet all mature-state acceptance gates at feasible cost. | OPEN | `experiments/method-selection-research.yaml`; `experiments/mature-state-decision.yaml` | Every suitable candidate fails a predeclared accuracy, invariant, reference, or cost gate. |
| C-006 | Existing Monte Carlo output defines a stable full 3-D density target. | REJECTED | `method_selection_report.json` | Histogram/KDE reconstruction remains sample- and bandwidth-sensitive. |
| C-007 | Spatial transport diffusion and positivity enforcement are the dominant remaining errors in the corrected Run 6 comparison. | NUMERICAL | `method_selection_report.json`; saved chat review | A controlled decomposition attributes comparable or larger error to time, boundary, analysis, initialization, export, or reference uncertainty. |
| C-008 | Adaptive Bernstein certification will materially reduce unnecessary Q2 limiting. | CONJECTURE | `docs/RESEARCH_DIRECTIONS.md` | Rigorous subdivision still certifies substantial true negativity or leaves Q2 accuracy/correction essentially unchanged. |
| C-009 | A repaired Q2 method is the best production target generator. | OPEN | Q2 projection and limiter reports | Controlled mature-state comparisons favour another method on accuracy, invariants, robustness, or feasible cost. |
| C-010 | Directional FCDF or complete-flux methods are preferable when `B` is identity/diagonal. | OPEN | Saved chat review; future literature audit | Assumptions fail in 3-D Lorenz/no-flux use, or controlled comparisons do not improve the error/cost tradeoff. |

Review this table after every material experiment. Classes and wording are
expected to change; preserve old evidence in Git and explain promotions,
rejections, or scope changes in `docs/DECISIONS.md`.
