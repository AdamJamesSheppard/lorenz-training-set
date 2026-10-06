# G02 characterization adjudication — 2026-10-06

Decision OL-D009: technical characterization COMPLETED; scientific G02 OPEN.
Self-reviewed implementing-agent analysis, not independent scientific review.

Immutable local run: runs/operator-learning/OL-G02_reconstruction_characterization_v1/
20261006T104156003005Z. Source predeclaration: d4b99a14be12a8fc06eed2c764182a3721e70f39.
Run elapsed 7.08784 seconds, CPU only. All 306 comparisons completed. Maximum
raw mass error 2.22e-15, measured negative mass zero. The 15 sealed artifact
hashes and input hashes were checked; six historical paths replay bitwise.
Original report SHA-256:
d7eafd692649ed6b9108fba6c4197cb6920fbd68ecc118b3ec6e2ea426173377.
Portable exact config/provenance/seal copies accompany this document; the full
306-record report remains local, with its hash above and summaries here.
Dense paths and reference arrays remain ignored local evidence; copies of the
JSON do not make those payloads available in Git. The sealed run is unchanged.

## Results and limits

Sampling the same fixed ten-unit window, compared with its 10,000-point
reconstruction (descriptive summaries across laws and sampling phases):

| Samples | Median physical density L1 | Maximum |
|---:|---:|---:|
| 250 | .144690 | .162670 |
| 500 | .072313 | .081532 |
| 1000 | .036409 | .041288 |
| 2000 | .018189 | .020822 |
| 5000 | .006361 | .006874 |

Actual historical endpoint-phase 1000-point inputs differ by L1 .030476–.041150;
maximum relative covariance difference .002481 and marginal TV .004574.
The dense control has the same RK4 dt=.001, not continuum-truth status.
No formal order or population confidence interval follows from these summaries.

At fixed physical top-hat width, histogram60×72×72 differs from historical
45×54×54 by median L1 .074790; histogram30×36×36 differs by .363395.
Vertex lifting remains coupled to histogram size. This is representation
sensitivity, not a pure estimator-order measurement. Kernel1 and kernel5
versus kernel3 produce median L1 .486227 and .455955 respectively. These are
different regularized laws; neither alternative is silently preferred.

Conditional random-time reconstruction median L1 at counts1000/4000/16000:
.172351/.089377/.044598. Random draws are conditional on the same finite path,
not independent Lorenz trajectories. Block-resample discrepancies are large
and alter occupation weights; they are not the time-quadrature error. Heuristic
ESS ranges8.5–24.1 for x and6.5–19.1 for positive-x, not full-density ESS.
Dependent-data resampling limitations:
[Shalizi, resampling over space and time](https://www.stat.cmu.edu/~cshalizi/dst/26/).

## Consequences

Technical invariants pass. No approved scientific reconstruction-error budget
exists, so characterization is neither a scientific gate pass nor a missed
scientific threshold. G02 remains OPEN, G03–G17 LOCKED. Preserve six pilot pairs.
Sampling contraction does not establish histogram adequacy, continuum target
accuracy, stationary-law estimation or neural-surrogate qualification.

Next proposal: RECONSTRUCTION_QUALIFICATION_PROPOSAL_V2.md. No new expensive
target generation, model training, Gaussian replacement or DA authorized.
