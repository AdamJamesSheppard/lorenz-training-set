# Mandatory research traceability

Requirement: **REQ-RT-001**. Effective 2026-10-06 under direct owner instruction.
Applies to every contributor and agent across FEM/FPE, target generation,
operator learning, forecast/posterior transfer, Bayesian assimilation and
scientific visualization. This is a project requirement, not optional guidance.

## Before implementation or a scientific run

For every new or materially changed method, record in version-controlled files:

1. Method ID/name/version, scientific purpose, mathematical definition and
   implementation/configuration paths.
2. Exact research sources: authors/title, DOI or stable URL, edition/paper or
   software version where relevant, and the portion actually used.
3. Attribution: historical use, current research, retrospective addition,
   original project derivation, engineering design or unresolved citation gap.
4. Assumptions and applicability: hypotheses satisfied, unverified conditions,
   departures from the cited method, dimensional/mesh/flux/boundary/time limits,
   competing explanations and known limitations.
5. Question, evidence class, frozen experiment/metrics/thresholds, their scientific
   rationale, required artifacts, pass/fail consequences and predeclaration commit.

Use docs/research_audit/methods.json and the source/gate ledger, or a linked
versioned method record with the same responsibilities. Add a dated source
inventory when needed; preserve earlier snapshots. Chat-only research attribution
does not meet this requirement. A project derivation must include the derivation;
an engineering choice needs its rationale. Do not invent a paper for either.

## For every outcome

Every PASS, FAIL, OPEN, insufficient-evidence, cancelled or superseded scientific
decision must link the method/source record, frozen config/commit, immutable run
evidence/hashes, measured criteria, reviewer/independence, approval authority,
limitations, resulting claims and what is or remains authorized.
Record technical process completion separately from scientific acceptance.
Failures and individual failed components receive the same traceability as passes.
No retrospective threshold relaxation, deleted failure or citation added after
the result may masquerade as pre-run research or qualification.

## Blocking rule and accountability

Missing traceability blocks scientific qualification, gate promotion and
production authorization. Record the blocker explicitly; leave the decision
OPEN when qualification evidence is incomplete. An unrelated existing failure
remains FAILED and is never rewritten OPEN merely because attribution is missing.
A declared research gap is honest disclosure, not automatic permission to pass.
An imported-theorem claim cannot be accepted until the relevant hypotheses are
verified or the claim is narrowed. Exploratory work with a known gap requires
explicit bounded authority and cannot establish the unsupported claim.

Implementer maintains the records; reviewer checks source relevance, applicability
and outcome correspondence; research owner controls scope and promotion.
Self-review is labelled. A bibliographic record, retrieved abstract or CI pass
does not establish theorem applicability or scientific correctness.

## Historical records

The existing audit in docs/research_audit/ is the retrospective baseline.
Its gap register remains explicit. Historical passes/failures and run payloads
are not rewritten to imply that this requirement existed before its effective
date. New scientific work and requalification must meet the requirement.

## Enforcement and review

Agent entry rules, the integrity policy, mathematical protocol, current-state
entry point and README must link this requirement. Fast governance checks fail
if the requirement or these authority pointers disappear. Existing research
checks enforce source/method resolution and recorded gate-outcome coverage.
These structural controls cannot certify that every scientific action was
recorded or a citation was interpreted correctly; scientific review remains
mandatory before accepting a claim or promoting a gate.

Provenance context, not gate evidence:
[FAIR4RS principles](https://doi.org/10.15497/RDA00068).
