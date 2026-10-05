# Research-control protocol

All dimensions are required: problem scope, targets, assumptions, competing
hypotheses, architecture/contracts, validation, provenance, accountability,
change control, resources and reporting. No dimension substitutes for another.

## History → new programme

FEM_GOVERNANCE_RECONSTRUCTION.md identifies source commits and file roles.
Use the existing MATH_PROTOCOL reasoning rules while keeping OL status separate
from FEM method-selection decisions. Preserve failures and superseded configs.
FEM verification passing cannot promote any OL gate.

## Two-phase gate control

A: commit question, hypotheses, assumptions, frozen config, metrics, thresholds,
required evidence and consequences. Require a clean source tree, committed
config and source hash. An amended threshold needs a NEW config/experiment ID,
a recorded justification and a new run; retain the old failure.
Run: immutable fresh instance with DATA_CONTRACT provenance. Cheap CI does not
execute scientific experiments. Historical diagnostics are explicitly non-gates.
B: independently inspect available artifacts, seal hashes, record PASS/FAIL/OPEN,
update claims/decisions/assumptions/state and NEXT_REQUIRED_GATE together.
A GitHub review should compare the Phase A config with the run copy and Phase B
decision. No force-push or moved released tag is part of this protocol.

## Roles and authority

Research owner: Adam James Sheppard (approval of scientific scope and promotion).
Implementer: named commit author/run producer. Reviewer: named evidence assessor;
record whether independent or self-review (do not invent independent review).
A signed decision records approver, date, limitations, config and evidence.
Agents may implement authorized bounded work; they may not authorize DA or
production by inference. Expensive campaigns require explicit scope and cost.
Blocked/missing evidence leaves a gate OPEN/FAILED, never presumed passed.

G00 review can establish a restricted proxy role without certifying all posterior
coverage; record exactly which family is accepted and what remains excluded.
Small law-alignment comparisons do not constitute complete DA implementation.

## Change and accountability

Git is the tracked change log. Evidence pointers cover ignored arrays.
One OL state authority: state.json with exact checked PROJECT_STATE.md mirror.
Top-level state links here and separately records FEM status. Historical snapshots
are marked archival and excluded from current-status checks.
Automated checks detect selected structural contradictions, not all scientific
semantic errors; human mathematical review remains necessary.

Cheap development studies may use existing pairs before G00, but cannot pass
downstream qualification gates, become final evaluation, or justify a large
campaign. Release notes state milestone, failed behaviours and forbidden uses.

Sources informing documentation/provenance (not scientific gate evidence):
FAIR4RS https://doi.org/10.15497/RDA00068;
Datasheets https://arxiv.org/abs/1803.09010;
Model Cards https://arxiv.org/abs/1810.03993.
