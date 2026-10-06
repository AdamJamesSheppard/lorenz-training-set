# Operator-learning current state

Updated: 2026-10-06. Canonical encoding: state.json; this exact mirror is checked.
Historical interpretation: DECISIONS.md. FEM method status is separate.

```json
{
  "schema_version": 1,
  "programme": "OPERATOR_LEARNING_QUALIFICATION",
  "scientific_problem": "FPE_FORECAST_SURROGATE",
  "eventual_application": "DENSITY_BASED_BAYESIAN_DATA_ASSIMILATION",
  "current_scope": "FIXED_PHYSICS_FIXED_HORIZON_ATTRACTOR_DENSITIES",
  "current_six_law_pilot": "COMPLETED_ENGINEERING_AND_RESTRICTED_LEARNING_PILOT",
  "current_model_scientifically_qualified": false,
  "next_required_gate": "OL-G03_INPUT_DIVERSITY",
  "active_blocker": "OL-D023 restores G03 characterization dispatch. Results/review and population coverage remain pending; changed FE transfer and reference/export qualification remain unverified.",
  "authorized": [
    "Commit and dispatch bounded G03 characterization_v1 under OL-D023; no expensive targets, training or DA",
    "Inexpensive labelled diagnostics; no expensive targets, neural retraining or DA"
  ],
  "locked": [
    "Large expensive target campaigns",
    "Qualified surrogate use",
    "Posterior-transfer qualification",
    "Operator-assisted DA",
    "Operator production"
  ],
  "operator_surrogate_authorized_for_da": false,
  "operator_production_authorized": false,
  "last_adjudicated_evidence": "OL-D021; evidence/G02_QUALIFICATION_V5_20261006.md: six20k candidates pass unchanged1% TV finite-control criteria; lower-count failures retained. Historical OL-D009/OL-D013/OL-D015 preserved.",
  "gates": {
    "OL-G00_PROBABILITY_DISTRIBUTION_ALIGNMENT": "PASSED",
    "OL-G01_REPRESENTATION_CONTRACT": "PASSED",
    "OL-G02_RECONSTRUCTION_STABILITY": "PASSED",
    "OL-G03_INPUT_DIVERSITY": "OPEN",
    "OL-G04_REFERENCE_TARGET_APPLICABILITY": "LOCKED",
    "OL-G05_EXPORT_FIDELITY": "LOCKED",
    "OL-G06_DATA_PROVENANCE": "LOCKED",
    "OL-G07_OPERATOR_STRUCTURE": "LOCKED",
    "OL-G08_BASELINE_QUALIFICATION": "LOCKED",
    "OL-G09_FIT_FEASIBILITY": "LOCKED",
    "OL-G10_GENERALIZATION": "LOCKED",
    "OL-G11_STRUCTURAL_GENERALIZATION": "LOCKED",
    "OL-G12_PROBABILITY_STRUCTURE": "LOCKED",
    "OL-G13_SEMIGROUP": "LOCKED",
    "OL-G14_ROLLOUT": "LOCKED",
    "OL-G15_ACCURACY_COST": "LOCKED",
    "OL-G16_POSTERIOR_TRANSFER": "LOCKED",
    "OL-G17_SEQUENTIAL_INTERFACE": "LOCKED"
  },
  "updated": "2026-10-06"
}
```
