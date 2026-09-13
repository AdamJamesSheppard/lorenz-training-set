#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lorenz_fpe import Lorenz63Model  # noqa: E402


def main() -> int:
    decision = json.loads((ROOT / "method_selection_report.json").read_text())
    boundary = json.loads((ROOT / "boundary_flux_report.json").read_text())
    local_projection = json.loads(
        (ROOT / "local_q2_positivity_projection_report.json").read_text()
    )
    optimizer_validation = json.loads(
        (ROOT / "local_q2_optimizer_validation_report.json").read_text()
    )
    dynamic_projection = json.loads(
        (ROOT / "local_q2_dynamic_projection_report.json").read_text()
    )
    tight_refinement = json.loads(
        (ROOT / "local_q2_tight_refinement_report.json").read_text()
    )
    spatial_refinement = json.loads(
        (ROOT / "local_q2_spatial_refinement_report.json").read_text()
    )
    diffusion = Lorenz63Model().diffusion

    mass_errors = [abs(float(row["mass_error"])) for row in boundary["rows"]]
    l1_errors = [float(row["l1_error"]) for row in boundary["rows"]]
    observed_orders = [
        np.log(l1_errors[i - 1] / l1_errors[i])
        / np.log(
            boundary["rows"][i]["cells_per_axis"]
            / boundary["rows"][i - 1]["cells_per_axis"]
        )
        for i in range(1, len(l1_errors))
    ]
    classification = str(decision.get("classification", "")).strip()
    dataset_decision = str(decision.get("large_neural_operator_dataset", "")).upper()
    method_certified = classification in {"READY", "CERTIFIED"} and dataset_decision == "YES"

    checks = {
        "diffusion_symmetric": bool(np.allclose(diffusion, diffusion.T, atol=1e-14)),
        "diffusion_positive_semidefinite": bool(np.linalg.eigvalsh(diffusion).min() >= -1e-14),
        "boundary_mass_error_ok": bool(max(mass_errors) <= 1e-9),
        "boundary_l1_decreases": bool(
            all(b < a for a, b in zip(l1_errors, l1_errors[1:]))
        ),
        "boundary_order_ok": bool(min(observed_orders) >= 1.9),
        "classification_present": bool(classification),
        "dataset_decision_valid": dataset_decision in {"YES", "NO"},
        "certification_consistent": bool(
            dataset_decision != "YES" or classification in {"READY", "CERTIFIED"}
        ),
        "local_projection_evidence_consistent": bool(
            np.isclose(
                decision["terminal_local_q2_projection"]
                ["stage1_then_local_qp_covariance_errors"][0],
                local_projection["full_step"]["hybrid_covariance_error"],
            )
            and local_projection["full_step"]["whole_cell_positivity_certified"]
            and local_projection["half_step"]["whole_cell_positivity_certified"]
            and not local_projection["decision"]
            ["pure_cell_local_projection_is_complete_solution"]
        ),
        "local_qp_optimizer_validation_consistent": bool(
            optimizer_validation["result"]["all_predeclared_gates_passed"]
            and optimizer_validation["result"]["osqp_failures"] == 0
            and optimizer_validation["result"]["objective_bound_violations"] == 0
        ),
        "historical_three_level_local_qp_consistent": bool(
            dynamic_projection["classification"] == "FAILED_PREDECLARED_DYNAMIC_GATES"
            and dynamic_projection["trajectory_invariants"]
            ["all_560_steps_whole_cell_positivity_certified"]
            and dynamic_projection["timestep_comparison"]["observed_order"] <= 0.0
            and not dynamic_projection["decision"]["dataset_generation_authorized"]
        ),
        "tight_four_level_local_qp_consistent": bool(
            tight_refinement["classification"] == "PASSED_PREDECLARED_DYNAMIC_GATES"
            and tight_refinement["all_predeclared_gates_passed"]
            and tight_refinement["all_timesteps_whole_cell_positivity_certified"]
            and tight_refinement["maximum_measured_negative_mass"] == 0.0
            and tight_refinement["optimizer_failures"] == 0
            and tight_refinement["scaling_fallbacks"] == 0
            and tight_refinement["consecutive_observed_orders"][-1] > 0.0
            and not tight_refinement["dataset_generation_authorized"]
            and classification in {
                "TEMPORAL_POSITIVITY_CERTIFIED", "SPATIAL_POSITIVITY_CERTIFIED"
            }
        ),
        "spatial_local_qp_consistent": bool(
            spatial_refinement["classification"]
            == "PASSED_PREDECLARED_SPATIAL_GATES"
            and spatial_refinement["method_status"]
            == "SPATIAL_POSITIVITY_CERTIFIED"
            and not spatial_refinement["production_dataset_authorized"]
            and spatial_refinement["next_required_gate"] == "FULL_SPD_DIFFUSION"
            and spatial_refinement["density_l1_differences"][1]
            < spatial_refinement["density_l1_differences"][0]
            and spatial_refinement["observed_common_grid_spatial_rate"] > 0.0
            and all(
                branch["maximum_measured_negative_mass"] == 0.0
                and branch["absolute_mass_error"] <= 1.0e-10
                and branch["optimizer_failures"] == 0
                and branch["fallbacks"] == 0
                for branch in spatial_refinement["branches"]
            )
            and classification == "SPATIAL_POSITIVITY_CERTIFIED"
            and decision.get("method_status") == "SPATIAL_POSITIVITY_CERTIFIED"
            and decision.get("production_dataset_authorized") is False
            and decision.get("next_required_gate") == "FULL_SPD_DIFFUSION"
        ),
    }
    result = {
        "passed": all(checks.values()),
        "method_certified": method_certified,
        "classification": classification,
        "checks": checks,
        "metrics": {
            "diffusion_eigenvalues": np.linalg.eigvalsh(diffusion).tolist(),
            "maximum_boundary_mass_error": max(mass_errors),
            "minimum_observed_boundary_l1_order": min(observed_orders),
            "controlled_q1_covariance_error": decision["same_initial_law_forecast"]
            ["normalized_covariance_error"],
            "unlimited_q2_cn_covariance_error": decision["executed_q2_temporal_diagnostics"]
            ["crank_nicolson_unlimited"]["full_step_covariance_error"],
            "terminal_stage1_local_qp_covariance_error": local_projection["full_step"]
            ["hybrid_covariance_error"],
            "terminal_stage1_local_qp_timestep_l1": local_projection
            ["timestep_comparison"]["hybrid_subcell_average_l1"],
            "dynamic_local_qp_covariance_errors": [
                level["covariance_error"] for level in dynamic_projection["levels"]
            ],
            "dynamic_local_qp_timestep_l1": [
                dynamic_projection["timestep_comparison"]["full_to_half_l1"],
                dynamic_projection["timestep_comparison"]["half_to_quarter_l1"],
            ],
            "dynamic_local_qp_observed_order": dynamic_projection
            ["timestep_comparison"]["observed_order"],
            "tight_local_qp_covariance_errors": tight_refinement["covariance_errors"],
            "tight_local_qp_timestep_l1": tight_refinement["adjacent_density_l1"],
            "tight_local_qp_finest_observed_order": tight_refinement
            ["consecutive_observed_orders"][-1],
            "spatial_local_qp_density_l1": spatial_refinement
            ["density_l1_differences"],
            "spatial_local_qp_observed_common_grid_rate": spatial_refinement
            ["observed_common_grid_spatial_rate"],
            "spatial_local_qp_covariance_errors": [
                branch["covariance_error"] for branch in spatial_refinement["branches"]
            ],
        },
        "interpretation": (
            "The tested invariants and evidence consistency pass. Production certification is "
            "derived from the current method-selection record and must be supported by its evidence."
        ),
    }

    output = ROOT / "results" / "math_checks.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
