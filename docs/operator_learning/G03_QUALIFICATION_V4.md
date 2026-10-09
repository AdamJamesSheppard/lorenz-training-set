# G03 fresh law-diversity qualification v4 — phase A

2026-10-09, OL-D031. Owner directs completion of G03, following approved
law-diversity scope OL-D030. Implementing-agent prospective engineering design;
self-review, no independent assessor. Methods: WINDOW_LOCAL_RK4_CONTROL_V3,
empirical box reconstruction, and G03_FINITE_CONTROL_NONCOLLAPSE_V4.
Implementation: scripts/run_diversity_qualification.py and
operator_learning/diversity_qualification.py. Exact executable definition:
experiments/operator_learning/OL-G03_diversity_qualification_v4.json.

Question: do retained finite-window occupation laws exhibit differences beyond
declared reconstruction variation? Competing explanations: genuine finite-law
variation, reconstruction artifacts, or collapse toward a common occupation law.
Use fresh seeds83501–83512, two consecutive10-unit windows/source, all24 attempts.
The original uniform initial-state sampling box and20-unit spinup are unchanged;
the common numerical origin is20.001 (the historical extra RK4 step). Generate
one20-unit fine path/source; restart each coarse window at its saved fine start.
Fine dt=.000125, coarse dt=.00025. Each window uses80k fine states, four20k
sampling phases, fixed physical box widths[4,40/9,40/9], no Gaussian/GMM fitting.
Export four conservative60×72×72 fields. Source groups/windows remain dependent.

Frozen criteria: every attempt completes with finite controls, raw mass error
≤1e-10, measured negative mass zero, sufficient combined finite-control TV≤.01
(unchanged G02 budget), all144 within-law and276 between-law pairs recorded.
Every law must have at least one cross-source witness with positive signed
margin TV-e_a-e_b-|m_a-1|-|m_b-1|-1e-10. All duplicates and ambiguous pairs stay.
No quota of separated pairs is chosen from630/630 historical diagnostics.
These criteria define limited non-collapse; repeated laws plus one different
law may satisfy them. Report ambiguity/frequency and all law-level geometric
statistics rather than imply24 independent or uniquely different laws.

Derivation: for normalized finite-grid measures q_i and declared finite controls
r_i with TV(q_i,r_i)≤e_i, the TV triangle inequality gives
TV(r_i,r_j)≥TV(q_i,q_j)-e_i-e_j. Mass allowances and roundoff margin make the
implemented criterion conservative. The sampling/integration controls retain
the exact pairing/coupling derivation and finite-scope limitations documented in
WINDOW_LOCAL_CONTROL_G03_V3.md and RECONSTRUCTION_QUALIFICATION_V5.md.
No continuum error certificate is assumed. Source context: Clément Canonne,
COMPX270 Lecture11 and Solution11 (2025),
https://ccanonne.github.io/files/compx270-chap11.pdf and
https://ccanonne.github.io/files/compx270-tutorial11-solutions.pdf . Only metric
triangle-inequality reasoning is used; i.i.d. learning rates do not apply to
these correlated paths. Operational witness criterion is project engineering.

Record means, covariances, marginals, lobe balance, transition, tail, boundary
and effective volume. These characterize differences; no numeric coverage
threshold or downstream accuracy claim is imported. Relevant assumptions:
OL-A04 training coverage unverified; numerical window conditioning, fixed
regularization, deterministic dependent phases, float64 without interval proof.
G04 reference applicability and G05 export fidelity remain separate.

All paths, local controls, phase fields, reports, exact config, versions, seeds,
hardware, source hashes, commit/dirty state and seals must be saved in a NEW run.
Never rewrite v1/v2/v3 artifacts. Failures/missing evidence block eligibility;
technical completion and review eligibility never automatically change G03.
After complete seal/source/metric review, a scoped pass may unlock G04 design
only. Failure retains G03 OPEN with the failed experiment recorded; thresholds
cannot be relaxed retroactively. No training, targets, DA or production allowed.
Payloads remain ignored locally; compact evidence must be committed on review.

ETA2–4minutes provisional, based on115.8s historical36-law study plus33.1s local
controls. One CPU/BLAS thread, no GPU/MPI. Confirm persistent service and initial
producer progress, then immediately hand back. Commit phase A before dispatch.
