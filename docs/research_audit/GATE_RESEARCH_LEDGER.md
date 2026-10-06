# Gate decisions and their research basis

2026-10-06. Source IDs resolve in snapshot_20261006.json and methods.json.
Research informs design; project frozen experiments determine numerical outcomes.
Original decision text, thresholds, configs, runs and adjudications are preserved
in the structured snapshot. No gate is promoted by this audit.

## Operator-learning gates

| Gate | Current outcome | Methods / research basis | Evidence and limitations |
|---|---|---|---|
|G00 probability alignment|PASSED scoped|OCCUPATION/BAYES/GOVERNANCE; MONO-lorenz, OL-BAYES, reporting guidance|OL-D003A/B→D004; alignment_v2 comparison and owner-selected ACCEPTED_POPULATION_V1. Actual posterior representativeness remains open.|
|G01 representation|PASSED scoped; v1 FAILED preserved|REPRESENTATION; OL-NUMPY and project conservative-integration identities|OL-D005 v1 bitwise failure; OL-D006 v2 unchanged thresholds pass. Archived six pairs only; new box FE transfer unqualified.|
|G02 reconstruction|PASSED scoped finite-control v5; historical characterizations retained|OCCUPATION/DEPENDENCE/BOX/BOUND; original overlap derivation; v5 Canonne TV semantics, no i.i.d. theorem transfer|OL-D021; frozen651eec5, six20k cases within1% TV bound.20k max.006441564;5k/10k insufficient certification preserved. No continuum/posterior/changed-FE-transfer guarantee. gate_updates.json preserves later adjudication without editing original snapshot.|
|G03 diversity|OPEN|DEPENDENCE; temporal-resampling context|No scientific run/adjudication; distinct laws versus reconstruction variation unresolved.|
|G04 reference applicability|LOCKED|DG/QP/REFERENCE/AMR; FEM-R01/03/04/21/25 and MFEM sources|Old GMM/mature certification cannot transfer automatically to new laws.|
|G05 export fidelity|LOCKED|REPRESENTATION; conservative integration and OL-NUMPY|Mass conservation alone does not qualify resolution/full-density fidelity.|
|G06 provenance/leakage|LOCKED|GOVERNANCE; FAIR4RS, Datasheets, Model Cards, REFORMS/leakage|Existing hashes are engineering evidence; no dataset qualification pass.|
|G07 numerical linearity|LOCKED|FPE/QP; project linear evolution derivation and correction literature|Continuum linearity known under well-posedness; numerical mixture defect unmeasured as qualified gate.|
|G08 baselines|LOCKED|BASELINES/FNO; original guide, retrospective FNO paper; FPE linearity|Persistence/nearest-target diagnostics exist; linear/POD/CNN qualification missing.|
|G09 fit feasibility|LOCKED|FNO/BASELINES; guide/paper context|100-epoch pilot is historical engineering evidence; convergence unresolved.|
|G10 within-population generalization|LOCKED|GOVERNANCE/BASELINES; leakage/reporting guidance|Original pilot test inspected; fresh untouched evaluation required.|
|G11 structural holdout|LOCKED|GOVERNANCE/BASELINES; same reporting guidance|No family-held-out qualification or universal initial-condition guarantee.|
|G12 probability/statistical structure|LOCKED|FNO/REFERENCE; architecture and statistical diagnostics|Pilot moment/marginal/lobe/boundary failures retained, not a formal gate run.|
|G13 semigroup|LOCKED|FPE; project semigroup reasoning under autonomous well-posed evolution|No independent2T comparison; numerical/neural semigroup remains unqualified.|
|G14 rollout|LOCKED|FPE; evolution-map context|No recurrent forecast qualification.|
|G15 accuracy/cost|LOCKED|BASELINES/MEMORY; operational benchmark design|No matched inference Pareto benchmark; training timer does not prove speedup.|
|G16 posterior transfer|LOCKED|BAYES/BOX; OL-BAYES, OL-FILTER with hypotheses unverified|Actual full posterior inputs needed; proxy scope does not qualify transfer.|
|G17 sequential interface|LOCKED|BAYES/REPRESENTATION; explicit Bayes and conservative interfaces|No separate DA programme authorized; state closure substitutions excluded.|

LOCKED rows are planned research mappings, not evidence of research already used
to pass/fail those gates. Each complete gate schema is copied in the snapshot.

## G01 and G02 preserved events

- G02 qualification_v5: OL-D021 scoped PASS with unchanged owner-approved.01 TV
  budget, all six windows,22 verified seals and bitwise trajectory/bound replay.
  Six5k and six10k sufficient-bound certification failures remain recorded; actual
  TV is not proved above tolerance. Full method/source and portable evidence:
  ../operator_learning/evidence/G02_QUALIFICATION_V5_20261006.md.

- G01 v1: FAILED strict bitwise replay, predeclaration7bfe51a; arithmetic ordering
  diagnosis is project numerical evidence, not a published theorem. The original
  failure JSON remains sealed. G01 v2: PASSED scoped at9198921, recorded OL-D006;
  identical thresholds retained. NumPy machine-limit documentation supplies only
  floating-point terminology/budget context.
- G02 v1:306 comparisons, technical completion, scientific OPEN; Shalizi time
  dependence/resampling and historical histogram recipe supply context.
- G02 refinement_v2:96 comparisons, technical completion, scientific OPEN;
  chaotic burn-in divergence and histogram sensitivity retained. No iid claim.
- G02 mechanism_v3:132 comparisons, technical completion, scientific OPEN;
  common-start replay, exact histogram-box integration, SciPy historical-filter
  semantics and original project integration control. No finite control is truth.
- G02 empirical_v4:120 comparisons, technical completion, scientific OPEN;
  exact empirical-box voxel overlap and KDE context. Crisan–Míguez is posterior
  density literature, with unverified applicability here.
- Paired-box bound: original finite-mixture derivation and unit tests, no empirical
  qualification run. Conservatively averaged grid distances can understate L1;
  the bound may overstate it. Candidate approval retains regularization caveats.

## FEM/reference programme — historical outcome families

The old programme used named experiments rather than OL-G00–17. The full ledger
contains every original decision section plus487 original FEM decision-field
records, preserving per-component booleans as well as aggregate classifications.
The following index locates the main method-selection branches; it does not
replace or compress away their individual original decisions.

| Branch / gate family | Recorded outcome / scope | Research used or context | Primary project evidence |
|---|---|---|---|
|Q1 vs Q2, same mesh and boundary-flux repair|Early comparisons repaired; Q1 comparator retained, Q2 challenger advanced|DG, upwind/SIPG; FEM-R01…06, MONO-arnold; historical local FEM book citation unresolved|METHOD_SELECTION_REPORT.md; same_mesh_q2_* and boundary_flux_report.json|
|BE/CN unlimited and global scaling|Unlimited CN temporal diagnostic improves but negativity inadmissible; global scaling temporal gate fails|TIME project CN algebra; FEM-R02/03 positivity scaling context|unlimited_q2_crank_nicolson_report.json; corrected_q2_crank_nicolson_report.json|
|Terminal local-QP and optimizer diagnostics|Local correction supported scoped; no dynamic certification inferred from terminal checks|QP, OSQP, FEM-R01/25; method differs from publication|local_q2_positivity_projection_report.json; optimizer/performance reports|
|Three-level dynamic projection|INSUFFICIENT_EVIDENCE retained|TIME/QP; project predeclared sequence|local_q2_dynamic_projection_report.json|
|Tighter four-level temporal positivity|Passed frozen gates; observed fine order is numerical evidence|TIME/QP, existing DG/positivity context|local_q2_tight_refinement_report.json|
|Identity spatial hierarchy|Passed startup spatial/positivity; observed rate3.40 is common-grid evidence|DG/QP, conservative comparison design|local_q2_spatial_refinement_report.json|
|Full-SPD control and hierarchy|Passed scoped full-SPD gates|Full tensor SIPG, QP; FEM-R01/03 and MFEM matrix interfaces later|local_q2_full_spd_control_report.json; local_q2_full_spd_spatial_report.json|
|Early mature/GMM hierarchy|Failed original mature gates; fixtures preserved|Historical GMM law, QP; no authority to use GMM as new population|local_q2_mature_bimodal_report.json; mature_da* reports|
|Bernstein subdivision diagnostic|Deeper certificate rejected as remedy for actual negative polynomials|FEM-R19/20, negative witnesses versus sufficient certificates|mature_positivity_certificate_diagnostic_report.json|
|AFC and DOF/subcell alternatives|Scientific failures/fallbacks and diagnostic comparisons retained; successful local-QP runs separate|FEM-R07/08/23/24; hyperbolic theorem transfer unproved|METHOD_SELECTION_REPORT.md; monograph ledger, AFC run fields|
|Uniform60 mature test|Original0.001 correction gate and statistics/positivity pass; density convergence open|QP/DG; spatial refinement project evidence|METHOD_SELECTION_REPORT.md §30; monograph ledger|
|Static graded efficiency|Frozen0.0008 aggregate gate FAILED; efficiency reproduction supported separately|AMR, DOLFINx mesh interface; no retroactive threshold change|mature_graded_efficiency_report.json; §31|
|Fine graded and time-aggregated tensor replay|Density/runtime gates fail; topology/resource limitations retained|AMR project indicators; adaptive links in CHAT-* remain unverified|mature_graded_fine_report.json; §32; docs/DECISIONS.md|
|MFEM physical and uniform trajectory equivalence|Scoped numerical PASS; wrapper failure distinguished|MONO-mfemdiff/mfemnc, physical-basis transforms and project CN/QP|mfem equivalence comparison scripts; §33/34; ignored run ledger|
|NC-face conservation and AMR reproduction|Local structural tests pass; first/second reproduction gates pass within voxel scope|MFEM hanging interfaces; project conservative weak-action probes|§34; docs/DECISIONS.md 2026-09-23; source ledger|
|Third depth/support expansion|Density gates FAILED retained; partial and resource failures distinct|AMR project discrepancy marking; no rigorous a posteriori error theorem|docs/DECISIONS.md 2026-10-01; source ledger|
|Bounded depth / broader support|Sensitivity gates pass; continuum convergence open|AMR project controls and exact voxel integration|docs/DECISIONS.md 2026-10-01/02; source ledger|
|Half timestep|Sensitivity pass; two levels do not establish formal order|TIME, unchanged scheme and fixed initial law|docs/DECISIONS.md 2026-10-03; source ledger|
|Two aligned domain expansions|Scoped mature-law domain gates pass; no arbitrary posterior/horizon guarantee|DOMAIN; frozen physical-resolution and diagnostic tolerances|docs/DECISIONS.md; domain_decision metadata in source ledger|
|Reference statistics / independent tests|Sampling-resolution limits and unresolved full-density truth retained|REFERENCE, MONO-sarkka/FEM-R21; bootstrap citation gap explicit|high_resolution_monte_carlo_report.json; independent_reference*|
|Literature-only challengers|No implementation/pass implied by citation|FEM-R05…18: FD/FV, Hermite, Lagrange–Galerkin, semi-Lagrangian|METHOD_SELECTION_REPORT.md sources and branch descriptions|
|Neural pilot|Operational target/CUDA feasibility; statistical qualification OPEN|OCCUPATION/REPRESENTATION/FNO; original guide plus retrospective paper|docs/operator_learning/evidence/PILOT_20261004T133438Z.json|

Infrastructure documentation certifies available interfaces, not the numerical
result. Historical local arrays remain ignored; this audit does not re-run FEM.
