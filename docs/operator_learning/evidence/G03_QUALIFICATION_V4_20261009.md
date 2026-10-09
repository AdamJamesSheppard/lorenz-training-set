# G03 v4 adjudication — scoped PASS (OL-D032)

Owner requested completion of G03 and subsequent continuation toward a pass.
Reviewer: implementing Codex agent; self-review, no independent assessor.
Authority: owner-approved law-diversity scope OL-D030, execution instruction
OL-D031, and continuation/adjudication instruction. No assertion of independent
review or owner inspection of every numerical value.

Predeclaration: f94a176f398b34c1ff2d451ef0d7f46fd1b9ebfe.
Method/source/derivation: ../G03_QUALIFICATION_V4.md,
../G03_QUALIFICATION_CODE.md and ../WINDOW_LOCAL_CONTROL_G03_V3.md.
Immutable local run:
`runs/operator-learning/OL-G03_diversity_qualification_v4/20261009T222910816221Z`.
Portable byte-identical copies: G03_QUALIFICATION_V4_20261009_report.json,
G03_QUALIFICATION_V4_20261009_provenance.json,
G03_QUALIFICATION_V4_20261009_config.json and
G03_QUALIFICATION_V4_20261009_seal.json, alongside this review.
The producer correctly leaves gate_status OPEN: adjudication is a separate
phase, never an edit of its report. Original v1/v2/v3 evidence remains unchanged.

## Frozen criteria and outcomes

All24 attempted laws from12 declared sources completed. All144 within-phase
comparisons and276 between-law comparisons are present. No failures, missing
pairs, unresolved laws, exclusions or retries. All24 sufficient finite-control
TV bounds ≤.01: maximum .006730688805759805, minimum .00499766926983549.
Corrected2026-10-10 under OL-D033: maximum recorded raw phase mass error
3.1086244689504383e-15 versus1e-10 gate (seed83510_window0, phase1).
The original2.886579864025407e-15 was the separate grid-integral replay maximum;
see G03_AUDIT_RESPONSE_20261010.md. No sealed numerical evidence was changed;
measured negative mass zero. Every law has22 resolved cross-source witnesses.
All276 pairs have positive signed margins, minimum .07734206307585645;
zero ambiguous pairs. This exceeds the required witness criterion without
changing it into a retrospective all-pairs requirement.

Maximum within-law phase TV .000060017273463730276. Cross-source264 pairs:
TV minimum .08907424631686574, median .3223611613659301, maximum
.682996540140583. Within-source12 pairs: minimum .170029118597211,
median .29672314741880906, maximum .5358923526452575.
Positive-x lobe probabilities range .2248658723505084–.6755646115904872.
Means, covariances, marginal differences, transition/tail/boundary and effective
volume diagnostics remain in the full portable report, without favourable-case
selection. Producer elapsed63.456198239 seconds; systemd exit0, result success.

## Verification and limitations

Read-only audit verified64 artifact seals and10 frozen source hashes, exact
config correspondence with the predeclaration commit, all24 recomputed bound
records using saved fine/local-coarse paths, matching window-start identities,
all96 phase fields finite/nonnegative and conserved, all276 independently
re-evaluated grid TV values (maximum discrepancy0), and exact evaluator replay
after JSON tuple/list normalization. This uses the same mathematical helpers;
no independent numerical implementation or independent integrator is claimed.
Unrelated untracked plotting script was declared in dirty provenance and never
used. Large fine/coarse/field arrays are ignored local evidence, not GitHub
payloads; portable reports/hashes do not replace access to those arrays.

Outcome PASSED for finite-control law diversity/non-collapse on this fixed
population/regularization. Claim class NUMERICAL, not proof. Dependent windows
and phases provide no independence or invariant-measure guarantee. No continuum,
universal initial-condition, training-coverage/optimality, posterior-transfer or
surrogate-accuracy claim. Conditioning on saved numerical window starts remains.
The alternative that phase reconstruction variation alone explains the measured
separation is inconsistent with these finite controls; no broader alternatives
are declared eliminated. Historical accumulated integration failures stay failed.

G04 opens for reference-target applicability design. FE projection of the
bin-free law, h/dt/reference applicability and export fidelity remain unresolved.
No new target campaign, neural training, qualified surrogate, production or DA
is authorized. NEXT_REQUIRED_GATE=OL-G04_REFERENCE_TARGET_APPLICABILITY.

Maintenance: audit_research_sources.py now recognizes explicit versioned gate
adjudications with matching component outcomes after the immutable baseline
snapshot. It continues requiring current-status agreement, valid method/evidence
paths and a recorded decision. No snapshot or failed criterion was changed.
Regression tests verify portable seals, criteria replay and preserved failures.
Final validation: full inexpensive suite156passed/1skipped in15.04s;
operator-learning subset110passed/1skipped in.54s. Governance, traceability,
research-graph and whitespace checks pass. Three older tests assumed G03 would
remain permanently OPEN; they now check canonical catalogue/next-gate consistency
while preserving G02 evidence and authorization assertions. No scientific
threshold or immutable result was altered to satisfy these software checks.

Research attribution: prospective project engineering witness rule plus the TV
triangle inequality, as recorded before execution in G03_QUALIFICATION_V4.md;
https://ccanonne.github.io/files/compx270-tutorial11-solutions.pdf supplies metric
context only. No i.i.d. sample-complexity theorem is applied to Lorenz paths.
