# G03 v3 review — local finite-control diagnostics supported; G03 OPEN

2026-10-08, OL-D029. Implementing-agent self-review under owner continuation;
no independent assessor or coverage qualification authority.
Method/source/limits: ../WINDOW_LOCAL_CONTROL_G03_V3.md,
WINDOW_LOCAL_RK4_CONTROL_V3; paired-box derivation and TV sources linked there.
Predeclaration fd87dd8efa14186fbd157e5f1e888f213f8f6960.
Config hash be3a9402f943083a438e42be6de3b47189ddadc1852fe50628d621cd9ba6fbd7.
Report hash d1812ec5239a82bdc6253016047611b8e8cf9f126ce7f5ac3510a7571cd888ad.
Run runs/operator-learning/OL-G03_window_local_control_v3/20261008T224500015235Z.

## Verified results and diagnostic verdict

All40 seals,15 frozen input hashes and exact config versus predeclaration
verify. All36 bounds independently recompute exactly from archived fine paths
and the new saved coarse paths using the SAME bound implementation. This is
arithmetic/artifact reproduction, not independent integrator verification.
Producer records36 bitwise fine-window replays and no failures/exclusions;
the review does not claim a second full36-window integration replay.
Technical elapsed33.148123s;36/36 local sufficient bounds≤unchanged.01.
Maximum total bound.00679621099. This is NUMERICAL finite-control evidence.

|Window index|Local combined bound maximum|Original combined maximum|Local integration maximum|
|---|---:|---:|---:|
|0|.00669575849|.00669575849|3.68973e-7|
|1|.00679621099|.00734964511|1.86996e-7|
|2|.00673981629|.30658807160|3.90222e-8|

The same recorded laws now satisfy sufficient local bounds, without changing
their kernel, samples, allocations or original accumulated controls. Evidence
supports accumulated integration separation as the earlier third-window
diagnostic's dominant component. It does not prove exact chaotic trajectories
or quantify true errors from the30-unit original state. Local controls condition
on saved numerical starts; old12/36 accumulated sufficient-bound failures remain.

## Relationship to diversity and coverage

V2 retained36 laws,216 within-law phase pairs and630 endpoint pairs. Median TV
.3480732 within-source versus.3832044 cross-source; lobe probability.15447–.97375.
After accounting for local finite-control bounds, raw mass defects and the
declared numerical allowance, every630 pair has a positive separation margin,
minimum approximately.0655424. This is an explicitly POST-HOC diagnostic using
unchanged v2 grids, not a newly predeclared pair quota or qualification pass.
Pair dependence and deterministic phase controls prohibit i.i.d. interpretations.

V2 eight-group candidate pools still leave worst nearest TV.30698–.50388.
Changing pool size also changes query membership; do not advertise these as a
controlled learning curve. Local reconstruction evidence does not resolve
training coverage, family-held-out generalization or posterior relevance.

G03 remains OPEN. The v3 config expressly forbids scientific gate promotion.
Draft criteria in ../G03_QUALIFICATION_SCOPE_PROPOSAL.md require owner review
and future committed predeclaration before any qualification study. No targets,
training, G04 promotion or DA. Older outcomes and run payloads are unchanged.

## Portable evidence

CONFIG.JSON, REPORT.JSON, PROVENANCE.JSON and SEAL.JSON files with this prefix
copy their sealed originals.36 local coarse arrays and v2 fine/grid arrays stay
ignored local payloads with seal/hash pointers. GitHub alone does not include
them. Provenance discloses unrelated untracked plotting script; it is unchanged.
Previous latest-update overlay is preserved verbatim in
G03_RESEARCH_UPDATES_BEFORE_OL_D029.json; the current schema permits one latest
entry per gate. OL-D024 and all earlier decisions remain in Git and DECISIONS.md.
Falsification: seal/config mismatch, replay failure, incorrect bound/phase pairing
or changes to the supposedly frozen law. No imported new theorem or thresholds.
