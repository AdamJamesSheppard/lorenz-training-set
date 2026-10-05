# FEM governance reconstruction — inspection on 2026-10-05

Anchor: 1781b40ad156f01702aeeb16eaf7e0240ede7378 (2 GiB resume threshold).
Inspected via git show/log alongside current tracked files and completed pilot.
This document interprets file roles without changing historical run records.

| Historical artifact | Role reproduced for OL |
|---|---|
| AGENTS.md at anchor | Entry/read-first rules, scope, logging, authority and stop boundaries |
| docs/PROJECT_STATE.md | Current method decision, authorization and NEXT_REQUIRED_GATE |
| docs/MATH_PROTOCOL.md | Hypotheses, spaces/norms, proof gaps and evidence distinctions |
| docs/MATHEMATICAL_SPEC.md | PDE, BC, numerical invariants and representation |
| docs/ARCHITECTURE.md | Dependency direction and independent challenger modules |
| docs/RESEARCH_DIRECTIONS.md | Alternatives, falsification and switching conditions |
| docs/CLAIMS.md | IDs, evidence classes, citations and scope limitations |
| docs/DECISIONS.md | Dated reasons and explicit supersession |
| docs/assumptions.yaml | Defaults versus requirements, false assumptions, revision rules |
| METHOD_SELECTION_REPORT.md | Adjudicated comparisons, failed gates and bounded permissions |
| experiments/ | Frozen questions, physical comparators, metrics and thresholds |
| runs/ | Timestamped config/source/command/environment/evidence records |
| scripts/check, verify-math, tests/ | Software checks distinct from scientific experiments |

Subsequent history:
f58b9c3 adds Apache licence; 0a952b1 deletes AGENTS.md. We do not resurrect it
or erase that decision. 7bb7e45 adds monograph and evidence ledger; 84b70ec adds
six-law density-only pilot; 7778cca records initialization failure; 11d222f repairs
nonnegative smoothing and enables CUDA; 8e2532f records fresh dispatch.
8f91ade/d43fad7 publish v0.1.0 preserving remote changes.
Current programme additions are new research decisions, not historical gate passes.

Recovered methodology: define→assume→predeclare→run→adjudicate→update claims/state.
Failed AFC/three-level/AMR and Gaussian-mixture comparisons remain separate
evidence; no later success changes their original thresholds/classification.
The original pilot dispatch is recorded at 11d222f with clean Git state.
Completed artifacts now support a new explicitly retrospective audit.

Known gaps motivating the new namespace: stale snapshot bullets, mixed Q1/Q2
baseline language, p0 versus posterior semantics, configurable-looking hard-coded
pilot settings, no OL gate authority, no formal untouched-test access record.
Root PROJECT_STATE before this transition is archived under docs/history/.
