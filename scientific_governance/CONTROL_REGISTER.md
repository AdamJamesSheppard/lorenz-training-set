# Audit recommendation implementation register — 2026-10-10

Status vocabulary: LIVE = remotely applied/read back; CANDIDATE = implemented
in this PR but awaiting protected owner review; BLOCKED = requires an externally
administered resource/identity. CANDIDATE is never an assurance of independence.

| Audit recommendation | Implementation / evidence | Remaining deployment or limitation |
|---|---|---|
| Protect main; prohibit force pushes/deletion | LIVE: GitHub branch protection, admin enforcement, review/latest-push/code-owner/conversation requirements, strict `governance` check, signed commits | Owner admin credentials still available here; separate restricted agent identity required |
| Protect acceptance rules and tests | CANDIDATE: CODEOWNERS covers authority, workflow, scientific tests and canonical records; base-revision transition verifier | Owner bootstrap merge, distinct PR author, then require scientific-transition; independently administered required workflow preferred |
| Explicit externally authenticated approval | CANDIDATE: four signed receipts bind owner claim, spec, executor, verifier, source/config/goal/archive | External three-role keys, owner device and approved-spec registry not provisioned |
| Separate implementation and adjudication | CANDIDATE: protocol rejects absent/wrong-role signatures; no agent promotion command | Separate operators/credentials/services remain BLOCKED; two agents sharing this host do not satisfy this |
| Prospective meaningful criteria | CANDIDATE: schema requires question/population/hypotheses/metric/acceptance/failure/budget/allocation/artifacts/limits/three propositions; full criteria hash | Independent scientific scope review and timestamped approval required before execution |
| Complete attempt accounting | CANDIDATE: runner records ordered STARTED/final attempts, failures and fresh outputs; v1 rejects retries/exclusions | Isolated trusted execution required; internal retries in submitted commands require independent review |
| Trusted execution and provenance | CANDIDATE: all tracked files, commit/dirty/environment hashes, source checked before/after; installed-service template | External executor identity, frozen build/image/OS dependencies, read-only source and service attestation BLOCKED |
| Immutable complete artifacts | CANDIDATE: safe sealed export, fresh destination, no overwrite, byte verification | Independent append-only archive, retention, upload identity and restore test BLOCKED; existing64 payloads remain local ignored evidence |
| Independent raw numerical checks | CANDIDATE implemented and exercised: G03 raw-array verifier, no producer imports; all64 hashes/24laws/144within/276between agree | Independent operator/archive trust roots and full trajectory/reconstruction replication OUTSTANDING |
| Adversarial verification and mutations | CANDIDATE: separate algorithm author reviewed authority; tests mutate hashes, samples, values, margins, approvals, retries and timing | Shared host/credentials disclosed; outside-administered acceptance copy still required |
| Protected goal; no objective substitution | CANDIDATE: GOAL.md, signed goal hash, all18 three-proposition boundaries; G04 design-only plan | Owner goal approval and externally protected verifier required |
| Evaluation isolation | CANDIDATE: protocol below; final evaluation disallowed in implementation environment | Actual inaccessible evaluation service, grouped population and access log BLOCKED |
| Five evidence levels | CANDIDATE: README and current claim registry distinguish software/numerical/scoped/replication/application | Historical PASS remains scoped, no fabricated independent/application qualification |
| G04 accuracy and independent acceptance | CANDIDATE: G04_INDEPENDENT_QUALIFICATION_DESIGN.md states question, hypotheses, raw diagnostics and independent validation | No arbitrary threshold: owner-reviewed signed spec and external execution pending |
| Source integrity / prompt injection | CANDIDATE: reference material is evidence only; executor has no owner/verifier secrets or final-data access by design | Enforce restricted identities, read-only mounts/network/secret permissions outside this session |

## Untouched evaluation release protocol

The independent evaluator owns source IDs, seeds, raw fields and final targets.
Train/development data remain accessible and labelled. Stress-test access is
recorded. All windows and reconstructions from a common trajectory/source stay
in the same split; mixture/derived laws retain ancestry to prevent cross-split
leakage. The owner approves a frozen split protocol and candidate method hashes
before the evaluator runs. Candidate code receives no final targets and cannot
modify the evaluator, metric implementation or approval rules.

Each request records method/config/source/checkpoint digests, access purpose,
timestamp and released information. A result inspected for development becomes
development evidence, even if it was originally called test. Tuning requires a
new untouched evaluation population. No technical isolation is claimed for the
current locally readable six-law arrays; the original inspected test is historical.

## Bootstrap acceptance versus scientific acceptance

This PR's ordinary CI establishes engineering behavior only. It deliberately
cannot authenticate its own bootstrap verifier from a base lacking that verifier.
The owner must review/merge through protected controls under separate identity,
then activate the required scientific check and external roots. Do not weaken
historical tests to hide source mismatches. A proposed modification to a source
hashed in the G03 predeclaration was removed; its historical file remains unchanged.

All listed blocked items must remain visible in canonical current state. This
register is a deployment checklist and supplies no automatic gate approval.
