# Research, method and gate audit — 2026-10-06

Authority: traceability audit requested by the owner. Scientific state and gate
thresholds remain unchanged. Audit source revision:5262c48, following the FEM
anchor1781b40ad156f01702aeeb16eaf7e0240ede7378 and subsequent OL decisions.

## What is recorded

- [Method register](methods.json): implemented methods, failed alternatives,
  historical fixtures, approved-but-unqualified candidates and future methods;
  implementation/evidence pointers, research-source IDs and applicability limits.
- [Gate and outcome ledger](GATE_RESEARCH_LEDGER.md): all18 OL gates, preserved
  pass/fail history, FEM stage/outcome mapping and research basis.
- [Machine-readable snapshot](snapshot_20261006.json): bibliographic records,
  every URL occurrence in tracked decodable text, reachable Git URL additions
  and removals, document/line/commit provenance, scanned-file hashes, original
  decision sections, current tracked report decision fields, and historical
  decision fields from the original883-record monograph ledger.
- [Gap register](GAPS.md): missing attribution, unverified applicability,
  unavailable local resources and unqualified future methods.

Original authorities remain docs/REFERENCES.md, METHOD_SELECTION_REPORT.md,
docs/solver_monograph/bibliography.tex and its source_ledger.json, with current
OL gates/state/claims/decisions under docs/operator_learning/. This audit links
those sources; it never rewrites historical evidence to create a successful story.
FEM-R01…25 identify existing method-selection footnotes; MONO-* identifies
existing monograph bibliography items; OL-* records OL sources. CHAT-* preserves
unverified user-provided historical links. Full original bibliographic text is
retained in the snapshot rather than paraphrased into invented precision.

## Attribution and verification

An original_recorded source appeared in repository documentation before this
audit. Association at the exact historical time is evidenced only by recorded
document/Git context, not guessed from a relevant paper's existence. The FNO
original paper is explicitly a retrospective addition; the original pilot cited
the official guide. Sources listed for LOCKED gates are prospective support,
not research already used to pass those gates. Project algebraic derivations
and owner decisions have their own attribution; neither needs a fabricated paper.

Primary source records checked in this audit include Liu–Hu–Taitano–Zhang
arXiv2410.19143v2, Carrillo–Liu–Yu arXiv2403.15643, Crisan–Míguez
arXiv1111.5866v8, Itkin arXiv2606.23980/2607.20415/2608.22703, Li et al.
arXiv2010.08895v3, MFEM NC documentation, NumPy/SciPy API descriptions and
REFORMS/leakage metadata. These are bibliographic/abstract/API checks, not a
new full-proof audit. In particular, Crisan–Míguez's v8 retains an explicit
Theorem4.2 erratum; no posterior-kernel theorem is imported into the deterministic
occupation study. Original DG theory and MFEM documentation do not prove the
complete project full-SPD CN/local-QP pipeline correct.

## Coverage and limits

Reachable Git history means refs available locally, including preserved removed
citations; deleted unreachable history, inaccessible chat uploads and references
never written to files cannot be recovered by this audit. URL extraction is
lexical; a software/license/XML URL is retained as an occurrence without being
mislabelled a scientific publication. Sources with only names/DOIs/local paths
remain in original reference documents and the gap register. The method register
covers documented scientific method families, not every routine or dependency.

The existing FEM ledger includes ignored local-run metadata, not distributed raw
arrays; classifications are copied as recorded and are not independently
re-adjudicated. Successful process completion and successful scientific gates
remain separate. No ignored data is silently promoted into available GitHub truth.

## Maintenance and checks

`python3 scripts/audit_research_sources.py` checks method/source links, evidence
paths, all18 gates and adjudication/status consistency, including G01 failure
coverage. This runs in ordinary governance CI without web access or simulation.
`python3 scripts/audit_research_sources.py --write` deliberately refreshes the
dated snapshot after review. Commit a new dated snapshot for a later audit;
do not change a historical scientific outcome or threshold. URL snapshots are
point-in-time inventories; old line/hash pointers are not asserted to remain live.

For every new experiment record method IDs, source versions/DOIs, what was used,
which hypotheses actually apply, config/predeclaration commit, immutable run,
metrics/thresholds, reviewer, pass/fail/open decision and the scope of authority.
An absent external citation is allowed only with explicit attribution such as
project derivation, engineering design, or open citation gap. Retain failures.
