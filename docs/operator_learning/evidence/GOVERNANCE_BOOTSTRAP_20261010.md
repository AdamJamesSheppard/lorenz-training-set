# Governance bootstrap engineering evidence — 2026-10-10

Decision: OL-D034. Method/source/applicability:
../../../scientific_governance/README.md and CONTROL_REGISTER.md. Scope is
engineering controls and historical arithmetic verification, no gate promotion.

Separate algorithm author: independent_verifier agent; implementing/operator
environment shared with primary agent. Its adversarial review identified and
prompted fixes to criteria/config binding, producer-report binding, approval
timing/signature binding and isolated-script imports. This supplies algorithmic
review, not independently administered scientific adjudication or owner approval.

Read-only raw evidence command:

```
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /home/adam/.local/share/mamba/envs/pde/bin/python -m scientific_governance.independent_g03 runs/operator-learning/OL-G03_diversity_qualification_v4/20261009T222910816221Z
```

Observed exit0, approximately0.68seconds. All64 sealed artifacts verified;
24laws,144within-phase and276between-law distances agree under independent
array arithmetic; minimum signed margin0.07734206307585645. No archive writes.
No producer helpers imported. Limitations: seal authenticity needs external
anchor; finite bounds not reintegrated; densities not regenerated; operator and
credentials remain shared. The large sealed inputs are ignored local evidence,
**not uploaded or independently archived by this change**. Existing historical
reports, seals, source hashes and pass/failure decisions remain unchanged.

First combined test run:138passed,1skipped,3failed in0.84seconds. One failure
correctly detected a proposed edit to historical hashed governance.py; that edit
was removed rather than changing frozen hashes/tests. Two failures detected a
stale research graph after documentation edits; graph regeneration is required.
The second test run recorded145passed,1skipped,1failed: the remaining frozen
hash was AGENTS.md. Its proposed edit was removed; instructions now reside in
the new scientific_governance/AGENTS.md. Historical source hashes/tests were
not changed. Subsequent combined tests:149passed,1skipped in1.11seconds;
whole repository:195passed,1skipped in15.57seconds. Follow-up hardening of
receipt snapshots/archive race checks was included in these results. Additional
small input-validation hardening received a final whole-suite rerun:
**197passed,1skipped in15.51seconds**. This includes standalone unsigned-promotion
rejection, duplicate-gate rejection, synthetic signed-receipt mutations, copied
artifact race rejection, safe paths, source inventories and failure ledgers.
check_operator_learning.py and audit_research_sources.py passed; research graph
rebuilt. The audit script has no --check option: an initial invocation with
that unsupported option returned usage error, followed by its supported default.

Remote protections: applied/read-back main review1, stale-review dismissal,
latest-push approval, code-owner review, resolved conversations, admin enforcement,
strict `governance` check bound to Actions app15368, no force-push/deletion,
signed commits. Owner explicitly chose separate restricted agent identity and
approval from another device; provisioning outside this session remains pending.
No protection bypass, real approval key, scientific owner signature, expensive
scientific run or automatic merge was attempted.
