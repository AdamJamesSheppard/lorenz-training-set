# Data, run and evaluation contract — version 1

## Dataset identity

An accepted sample records generator metadata, law/family ID, independent
trajectory/ensemble group ID, reconstruction replicate ID, FE configuration,
acceptance diagnostics, domain/units, D/f/T, voxel edges/volumes, axes (x,y,z),
dtype/scaling, initial/final artifact hashes and reference applicability.
Never label unconditioned occupation inputs as posterior densities.
Current pairs are p0→pT; eventual DA pairs are p(k|k)→p(k+1|k).

Grouped splits keep related trajectory windows and reconstruction replicates
together. Record seed STREAMS and independent source identities; seed uniqueness
alone cannot establish independence. Report rejection rates and law properties.
Hold entire families out for G11. Split creation must be reproducible and
test-set access recorded. Training-only preprocessing and checkpoint selection
must exclude final evaluation. Quantile estimates require sample counts and
uncertainty; one held-out law cannot establish population p95.

## Historical pilot status

Original test law 5 was examined on 2026-10-05, including boundary/lobe/coverage
diagnostics. Its original test score remains historical evidence. Further
decisions based on it contaminate it as development data. A NEW untouched
evaluation population is mandatory for serious generalization claims.
Four train/one validation/one original test is not a qualification dataset.

## Immutable new-run contract

Each run is a fresh, nonexisting directory with: experiment_id, gate_id,
kind, frozen config/hash, full Git commit, dirty flag/status, exact command,
package/runtime versions, hardware, seeds, input hashes, output hashes,
checkpoint hashes (empty only if no checkpoint), diagnostics, status.
Do not store secrets or an indiscriminate environment-variable dump.
Commit compact manifests/pointers; retain large payloads locally or on a
declared durable external archive. GitHub alone does not contain ignored arrays.

Phase A commits the experiment and thresholds before execution. Phase B
records adjudication with config/source/evidence hashes and reviewer/approver.
Finish and hash output payloads before sealing a run; a sealed result is never
overwritten. Running progress may be updated inside its own fresh directory.
Interrupted runs remain failures/partials with preserved artifacts.

A placeholder TO_BE_PREDECLARED_BEFORE_RUN is intentionally non-executable.
Validation rejects it for scientific execution. Qualitative gates require
explicit review criteria, documented evidence and signed scoped decisions.
No automatic numeric-to-authorization promotion is implemented.

The preparation command freezes expected runtime/hardware metadata without
executing a process. A future experiment runner must record the observed runtime,
hardware and actual argv, reconcile them against the frozen requirements, and
seal completed outputs. PREPARED_NOT_EXECUTED provides no run evidence.

## Historical provenance limitation

The original pilot recorded input/pair hashes, source revision, config, commands,
packages, device, summaries and checkpoint. It did not initially seal a complete
output/checkpoint hash ledger. The new historical audit hashes existing artifacts
without changing them; retrospective hashing is labelled separately from original
dispatch provenance. It cannot reconstruct missing metrics or undisclosed access.
