# Risks and falsification programme

| Risk | Consequence | Control / gate |
|---|---|---|
| Occupation law confused with posterior | Wrong input population despite attractor-shaped plots | G00 generator meaning and application coverage |
| Sampling dependence and bandwidth bias | Reconstruction noise masquerades as law diversity | G02/G03 replicates, ESS and sensitivity |
| GMM-derived mesh reused without applicability | Biased targets for new structures | G04 per-family refinement/error budget |
| Conservative export mistaken for accuracy | Lost subvoxel structure dominates target | G05 grid and dtype comparisons |
| Inspected test reused as untouched | Optimistic generalization claims | G06 access log, new sealed evaluation |
| FNO preferred in advance | Weak or irrelevant benchmark | G07/G08 linear/POD and CNN candidates |
| L2 improves while statistics worsen | Harmful probability redistribution | G12 moments, marginals, lobes, boundary |
| Softplus background/global normalization | Artificial probability near empty boundaries | Output ablations, fixed physical regions |
| Last epoch best | Optimization unresolved | G09 fit/learning-curve controls |
| Tiny evaluation count | Invalid tail quantiles/coverage claims | G10/G11 independent population and uncertainty |
| Discrete fit called continuum accuracy | False physical certainty | G04/G05 reference uncertainty |
| One-step score called DA readiness | Rollout/filter failure | G13–G17 plus separate DA programme |
| Resource pause called checkpoint recovery | Incorrect restart assumptions | Explicit per-component execution policy |
| Threshold edited after failure | Outcome-driven certification | Phase A/B hashes and immutable versions |
| Documentation drifts | Wrong scientific authorization | Checked state/catalogue plus human scope review |

Current causes are competing hypotheses, not settled diagnoses: fit/capacity,
loss, sparse coverage, normalization/background, spectral boundary interaction
and population mismatch. Isolate them on existing data before expensive expansion.
