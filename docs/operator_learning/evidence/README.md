# Completed six-law pilot: retrospective adjudication, 2026-10-05

Decision: engineering and restricted-learning milestone. **No OL gate passed.**
The current FNO is scientifically unqualified; statistical fidelity and
application-population alignment remain open.

Primary historical run: `runs/neural-pilot/20261004T133438Z`, clean source
`11d222f8090cf0ea263e97bfcd79252262684fb7`.
Read-only-source audit ran at clean control commit
`7cb41a6fac9ed0bb08d1e21c1d3427d58cebcd08`; no target regeneration or retraining.
New local audit: `runs/operator-learning/historical-pilot-audit/20261005TGovernanceAudit01`.
The tracked [complete compact report](PILOT_20261004T133438Z.json) is byte-identical
to that sealed audit. SHA-256:
`ed0f7de946b94c8d768846f0be2486093f3a514fefcf84f11e52d0fdf2c07340`.
Report includes source-artifact/checkpoint/pair hashes, package versions, command,
CPU audit diagnostics and original GPU evaluation. Retrospective hashing cannot
establish that outputs were sealed at original dispatch.

## Operational evidence

Six accepted forecasts; four training laws, one validation law, one original test
law; fixed full-SPD D, T=.05, dt=.00015625, 320 steps/law, 208,787 AMR cells.
Inputs: deterministic finite-window occupation samples, compact smoothing,
positive trilinear density, FE projection; no Gaussian/GMM fit, observations,
assimilation cycles or recurrent rollout. Learning grid 60×72×72.

All configured sample gates passed; all six pair hashes match the manifest.
Zero uncertified accepted cells, optimizer failures or fallbacks. Maximum
absolute mass error 1.01852e-12; mean relative L1 positivity corrections
7.12436e-5–9.28546e-5. This establishes operational target acceptance for these
runs, without continuum certification for the new law family.
Summed forecast time: 28.21366 hours (not a complete campaign wall-time measure).
100 epochs on RTX 4070. The training timer is 5.62780 seconds and excludes
data loading/model initialization; it is not a solver-replacement speed benchmark.

## Recorded GPU evaluation

L1 is the integral of absolute density difference on equal-volume voxels;
the training tensor is u=384000 p, so its mean absolute difference equals this
physical L1. TV is half L1 after probability normalization. Relative L2 uses
the target norm; covariance discrepancy uses the Frobenius norm.

| Case | Neural L1 | Persistence L1 |
|---|---:|---:|
| train 0 | .24394 | .59327 |
| train 1 | .29725 | .59854 |
| train 2 | .26245 | .59934 |
| train 3 | .25205 | .59612 |
| validation | .29367 | .59175 |
| original test | .50713 | .60735 |

| Original test metric | Neural | Persistence |
|---|---:|---:|
| relative L2 | .35189 | .47097 |
| mean-vector error | 2.30196 | .15196 |
| relative covariance error | 27.4824% | 1.7288% |
| x marginal TV | .10522 | .01846 |
| y marginal TV | .10562 | .01516 |
| z marginal TV | .07516 | .01023 |

The normalized test full-density TV is approximately .25357. Density improvement
coexists with severe statistical deterioration. Positivity/normalization do not
provide probability-law fidelity.

## CPU checkpoint diagnostics

CPU recomputation agrees closely, with small floating-point/device differences
explicitly retained rather than replacing recorded GPU values.

| Diagnostic | validation | original test |
|---|---:|---:|
| nearest training input L1 | .21478 | .52071 |
| nearest training target L1 | .20797 | .51034 |
| neural boundary probability | .0045862 | .0152185 |
| FEM boundary probability | 1.7123e-11 | 6.2729e-10 |

Nearest target is selected by nearest INITIAL training density, without inspecting
the query target. It beats the network on validation and nearly matches test;
persistence alone is insufficient. The boundary is the union of outer FOUR
learning-grid voxel layers, wider than the original fine-grid acceptance region.
Artificial boundary probability remains a serious diagnostic under this declared
region; do not conflate the two boundary gates.

Test P(x>0): target .233637, neural .139487. Target mean
(-4.04676,-3.90359,23.79715); neural (-5.84630,-5.05985,24.64786).
Neural mass on exactly-zero recorded target voxels: 2.05793%; zeros are
representation-dependent and do not establish true support boundaries.

Best validation loss is epoch 99 (last of 100): optimization convergence remains
unresolved. More epochs are a hypothesis, not a remedy established by evidence.
Possible causes: incomplete fitting, capacity/loss choices, input coverage,
normalization/background behaviour, Fourier/boundary effects or input-law mismatch.
Separate these by controlled development studies with strong linear/POD baselines.

## Decision and access record

Original law5 test diagnostics were inspected on 2026-10-05. Its original score
remains reportable; tuning against the revealed errors makes reuse development
data. Future generalization requires new untouched independent laws/families.
No distribution alignment, reference applicability, generalization, rollout,
posterior-transfer, DA or production claim follows from this pilot.

Large arrays, raw exports and checkpoint remain ignored local evidence, absent
from GitHub/release source archives. The tracked report is portable; raw
reproduction requires separately archived payloads whose hashes are listed here.
