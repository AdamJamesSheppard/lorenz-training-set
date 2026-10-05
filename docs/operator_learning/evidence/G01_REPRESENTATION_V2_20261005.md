# G01 representation audit — 2026-10-05

Decision: **PASSED_SCOPED_REPRESENTATION_CONTRACT**, technical self-review.
Owner authorized G01 for ATTRACTOR_DENSITY_V1. The implementing agent adjudicates
the frozen technical criteria; no independent review or new owner approval of
broader claims is represented. All six laws and twelve initial/final fields pass
v2, predeclared at9198921. Audit compute time0.91seconds; no new FEM forecast or
neural training was run.

| Maximum diagnostic | Result |
| --- | ---: |
| Fine export mass discrepancy versus FE summary | 2.50e-13 |
| Coarsening mass discrepancy | 2.22e-16 |
| Measured negative mass | 0 |
| Initial reconstruction versus FE export L1 | 2.76e-14 |
| float32 cast L1 | 2.23e-8 |
| Tensor scaling roundtrip L1 | 2.19e-8 |

All six sample-to-trilinear reconstructions are bitwise identical to archived
empirical_prior.bin. All twelve stored pairs are bitwise identical to float32
casts of conservative block averages. Bounds, axes, units and scaling are in
[the representation contract](../REPRESENTATION_CONTRACT_V1.md). Physical voxel
centres differ from historical network index-positional channels; that convention
is explicitly recorded, not silently changed.

v1 failed strict reconstruction identity because the audit helper evaluated the
normalizing volume differently in floating-point arithmetic. Its evidence is
preserved as G01_REPRESENTATION_V1_FAILED_20261005*.json. v2 repairs evaluation
order, leaves every threshold unchanged, and passes a new immutable run.

## Scope and limitations

This is archived-data representation consistency evidence, not continuum
accuracy, reconstruction stability or a resolved spatial-export error budget.
Native FE coefficient states are absent; independent native re-export cannot be
claimed. Source inspection and portable quadrature/axis fixtures complement
mass-summary and initialization checks. All six laws remain development evidence,
including the inspected original test law. Actual posterior transfer, model
statistical fidelity and production remain unqualified.

Only G02 reconstruction stability opens: assess sample number, temporal
dependence/effective sample size, histogram resolution, smoothing width and
independent reconstruction without changing the accepted attractor-law meaning.
No large target campaign, model retraining or DA authorization follows.

## Provenance and storage

Predeclaration: experiments/operator_learning/OL-G01_representation_v2.json.
Evidence: runs/operator-learning/OL-G01_representation_v2/20261005T204321317739Z.
Original arrays remain ignored in runs/neural-pilot/20261004T133438Z; read only.
Git tracks config, compact report, provenance, seals and decisions. GitHub does
not contain full local arrays. The input hash ledger identifies each artifact
and code file. The failed v1 run remains intact locally and in compact evidence.
