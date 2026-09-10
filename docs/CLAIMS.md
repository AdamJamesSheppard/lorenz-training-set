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
| C-008 | Adaptive Bernstein subdivision is a sufficient whole-cell positivity certificate and useful Q2 diagnostic, but is not a necessary condition or a complete decision procedure for non-negativity. | ESTABLISHED | `METHOD_SELECTION_REPORT.md`; cited Bernstein certificate and counterexample literature | Strictly positive polynomials are eventually certifiable; non-negative polynomials with zeros may remain uncertified under subdivision. Its material effect on this Q2 run is still open. |
| C-009 | A repaired Q2 method is the best production target generator. | OPEN | Q2 projection and limiter reports | Controlled mature-state comparisons favour another method on accuracy, invariants, robustness, or feasible cost. |
| C-010 | Directional FCDF or complete-flux methods are preferable when `B` is identity/diagonal. | OPEN | `METHOD_SELECTION_REPORT.md`; primary 2026 preprints | Existing results are 1-D/2-D and recent; 3-D Lorenz/no-flux comparisons may fail or give an inferior error/cost tradeoff. |
| C-011 | The existing equal-DOF Q1/Q2 forecast establishes the effect of polynomial degree. | REJECTED | Q1/Q2 Run 6 reports; `METHOD_SELECTION_REPORT.md` | Q2 used 1.5-times-wider cells in each direction and twice the timestep. |
| C-012 | A same-mesh Q2 method with less conservative positivity handling can meet the production gates. | OPEN | Predeclared experiment in `METHOD_SELECTION_REPORT.md` | Raw or corrected Q2 fails covariance, marginal, positivity, timestep, limiter, memory, or cost gates. |
| C-013 | The production method must support full SPD diffusion induced by a constant general 3 by 3 noise matrix. | ESTABLISHED | User-defined target; `docs/assumptions.yaml` A3 | A later explicit scope change may narrow the production problem; diagonal-only evidence does not cover the present target. |
| C-014 | The implemented adaptive Bernstein classifier has sound three-way outcomes on affine tensor cells: certification uses non-negative leaf coefficients, witnesses use evaluated negative values, and every unresolved cell receives the fixed sufficient correction. | ESTABLISHED | `POSITIVITY_AUDIT.md`; targeted classifier and MPI smoke tests | Floating-point enclosures are not interval arithmetic; classification near roundoff is deliberately conservative, and production accuracy remains unmeasured. |
| C-015 | Same-mesh adaptive-certificate Q2 at `dt=0.000625` is substantially more accurate than Q1 for startup covariance and marginals, but the tested Q2 configuration meets every predeclared gate. | REJECTED | `same_mesh_q2_falsification_report.json` | Covariance and limiter gates passed; the timestep density lower bound `L1=0.01552` and half-step mass error failed their gates. |

Review this table after every material experiment. Classes and wording are
expected to change; preserve old evidence in Git and explain promotions,
rejections, or scope changes in `docs/DECISIONS.md`.
