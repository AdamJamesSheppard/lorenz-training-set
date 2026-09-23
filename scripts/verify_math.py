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
    full_spd_control = json.loads(
        (ROOT / "local_q2_full_spd_control_report.json").read_text()
    )
    full_spd_spatial = json.loads(
        (ROOT / "local_q2_full_spd_spatial_report.json").read_text()
    )
    mature_bimodal = json.loads(
        (ROOT / "local_q2_mature_bimodal_report.json").read_text()
    )
    mature_certificate = json.loads(
        (ROOT / "mature_positivity_certificate_diagnostic_report.json").read_text()
    )
    mature_graded = json.loads(
        (ROOT / "mature_graded_efficiency_report.json").read_text()
    )
    mature_graded_fine = json.loads(
        (ROOT / "mature_graded_fine_report.json").read_text()
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
                "TEMPORAL_POSITIVITY_CERTIFIED",
                "SPATIAL_POSITIVITY_CERTIFIED",
                "FULL_SPD_DIFFUSION_CERTIFIED",
                "MATURE_STATE_STATISTICAL_AND_POSITIVITY_GATES_PASSED",
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
            and classification in {
                "SPATIAL_POSITIVITY_CERTIFIED", "FULL_SPD_DIFFUSION_CERTIFIED",
                "MATURE_STATE_STATISTICAL_AND_POSITIVITY_GATES_PASSED",
            }
            and decision.get("method_status") in {
                "SPATIAL_POSITIVITY_CERTIFIED", "FULL_SPD_DIFFUSION_CERTIFIED",
                "MATURE_STATE_STATISTICAL_AND_POSITIVITY_GATES_PASSED",
            }
            and decision.get("production_dataset_authorized") is False
            and decision.get("next_required_gate") in {
                "FULL_SPD_DIFFUSION", "MATURE_STATE", "MATURE_DENSITY_CONVERGENCE",
                "LOCALLY_REFINED_MATURE_DENSITY_CONVERGENCE"
            }
        ),
        "full_spd_control_consistent": bool(
            full_spd_control["classification"]
            == "PASSED_PREDECLARED_FULL_SPD_CONTROL_GATES"
            and full_spd_control["all_320_steps_whole_cell_positive"]
            and full_spd_control["maximum_measured_negative_mass"] == 0.0
            and full_spd_control["absolute_mass_error"] <= 1.0e-10
            and full_spd_control["normalized_covariance_error"] <= 0.02
            and full_spd_control["maximum_off_diagonal_covariance_error"] <= 0.05
            and full_spd_control["maximum_off_diagonal_correlation_error"] <= 0.02
            and full_spd_control["mean_relative_l1_correction"] <= 2.5e-4
            and full_spd_control["maximum_relative_l1_correction"] <= 3.0e-3
            and full_spd_control["optimizer_failures"] == 0
            and full_spd_control["fallbacks"] == 0
            and not full_spd_control["production_dataset_authorized"]
        ),
        "full_spd_spatial_consistent": bool(
            full_spd_spatial["classification"]
            == "PASSED_PREDECLARED_FULL_SPD_SPATIAL_GATES"
            and full_spd_spatial["method_status"] == "FULL_SPD_DIFFUSION_CERTIFIED"
            and full_spd_spatial["all_960_steps_whole_cell_positive"]
            and full_spd_spatial["maximum_measured_negative_mass"] == 0.0
            and full_spd_spatial["density_l1_differences"][1]
            < full_spd_spatial["density_l1_differences"][0]
            and full_spd_spatial["observed_common_grid_spatial_rate"] > 0.0
            and all(
                branch["maximum_measured_negative_mass"] == 0.0
                and branch["absolute_mass_error"] <= 1.0e-10
                and branch["normalized_covariance_error"] <= 0.04
                and branch["mean_relative_l1_correction"] <= 1.0e-3
                and branch["maximum_relative_l1_correction"] <= 5.0e-3
                and branch["maximum_off_diagonal_covariance_error"] <= 0.25
                and branch["maximum_off_diagonal_correlation_error"] <= 0.08
                and branch["optimizer_failures"] == 0
                and branch["fallbacks"] == 0
                for branch in full_spd_spatial["branches"]
            )
            and full_spd_spatial["optimizer_failures"] == 0
            and full_spd_spatial["total_fallbacks"] == 0
            and not full_spd_spatial["production_dataset_authorized"]
            and classification in {
                "FULL_SPD_DIFFUSION_CERTIFIED",
                "MATURE_STATE_STATISTICAL_AND_POSITIVITY_GATES_PASSED",
            }
            and decision.get("method_status") == classification
            and decision.get("next_required_gate") in {
                "MATURE_STATE", "MATURE_DENSITY_CONVERGENCE",
                "LOCALLY_REFINED_MATURE_DENSITY_CONVERGENCE"
            }
        ),
        "mature_bimodal_failure_consistent": bool(
            mature_bimodal["classification"]
            == "FAILED_PREDECLARED_MATURE_BIMODAL_GATES"
            and mature_bimodal["all_960_steps_whole_cell_positive"]
            and mature_bimodal["maximum_measured_negative_mass"] == 0.0
            and mature_bimodal["optimizer_failures"] == 0
            and mature_bimodal["total_fallbacks"] == 0
            and mature_bimodal["density_l1_differences"][1]
            < mature_bimodal["density_l1_differences"][0]
            and mature_bimodal["observed_common_grid_spatial_rate"] > 0.0
            and mature_bimodal["decreasing_mean_qp_correction_gate"]
            and all(
                value > mature_bimodal["failed_gate"]["threshold"]
                for value in mature_bimodal["failed_gate"]["observed"]
            )
            and classification in {
                "FULL_SPD_DIFFUSION_CERTIFIED",
                "MATURE_STATE_STATISTICAL_AND_POSITIVITY_GATES_PASSED",
            }
            and decision.get("method_status") == classification
            and decision.get("production_dataset_authorized") is False
            and decision.get("next_required_gate") in {
                "MATURE_STATE", "MATURE_DENSITY_CONVERGENCE",
                "LOCALLY_REFINED_MATURE_DENSITY_CONVERGENCE"
            }
        ),
        "mature_certificate_diagnostic_consistent": bool(
            mature_certificate["classification"]
            == "CERTIFICATE_OVERCONSERVATISM_HYPOTHESIS_REJECTED"
            and mature_certificate["predeclared_rule"]["outcome"] == "REJECT"
            and mature_certificate["aggregate"]
            ["maximum_fraction_of_depth4_noncertified_cells_rescued_by_depth8"]
            < 0.01
            and mature_certificate["aggregate"]
            ["maximum_l1_correction_reduction_from_depth8"] < 0.10
            and mature_certificate["aggregate"]["optimizer_failures"] == 0
            and mature_certificate["aggregate"]["fallbacks"] == 0
            and classification in {
                "FULL_SPD_DIFFUSION_CERTIFIED",
                "MATURE_STATE_STATISTICAL_AND_POSITIVITY_GATES_PASSED",
            }
            and decision.get("production_dataset_authorized") is False
            and decision.get("next_required_gate") in {
                "MATURE_STATE", "MATURE_DENSITY_CONVERGENCE",
                "LOCALLY_REFINED_MATURE_DENSITY_CONVERGENCE"
            }
        ),
        "mature_uniform60_and_graded_efficiency_consistent": bool(
            mature_graded["classification"]
            == "MATURE_STATE_STATISTICAL_AND_POSITIVITY_GATES_PASSED"
            and mature_graded["method_status"] == mature_graded["classification"]
            and mature_graded["mature_density_convergence"] == "OPEN"
            and mature_graded["mature_graded_efficiency"] == "SUPPORTED_NOT_CERTIFIED"
            and mature_graded["uniform60"][
                "mean_relative_l1_correction"
            ] <= 0.001
            and mature_graded["uniform60"]["all_320_steps_whole_cell_positive"]
            and mature_graded["uniform60"]["maximum_measured_negative_mass"] == 0.0
            and mature_graded["graded44x52x46"][
                "formal_classification"
            ] == "FAILED_PREDECLARED_MATURE_GRADED_EFFICIENCY_GATES"
            and mature_graded["graded44x52x46"][
                "mean_relative_l1_correction"
            ] > mature_graded["graded44x52x46"]["correction_threshold"]
            and mature_graded["graded44x52x46"][
                "density_l1_fraction_of_45_to_60_difference"
            ] < 0.01
            and mature_graded["graded44x52x46"]["dof_reduction_fraction"] > 0.5
            and mature_graded["graded44x52x46"]["runtime_reduction_fraction"] > 0.5
            and mature_graded["graded44x52x46"]["memory_reduction_fraction"] > 0.5
            and mature_graded["graded44x52x46"][
                "matched_grid_maximum_marginal_tv_increase"
            ] <= 0.005
            and mature_graded["graded44x52x46"][
                "all_320_steps_whole_cell_positive"
            ]
            and mature_graded["graded44x52x46"]["maximum_measured_negative_mass"] == 0.0
            and mature_graded["graded44x52x46"]["optimizer_failures"] == 0
            and mature_graded["graded44x52x46"]["fallbacks"] == 0
            and classification == mature_graded["classification"]
            and decision.get("method_status") == mature_graded["method_status"]
            and decision.get("mature_density_convergence") == "OPEN"
            and decision.get("mature_graded_efficiency") == "SUPPORTED_NOT_CERTIFIED"
            and decision.get("production_dataset_authorized") is False
            and decision.get("next_required_gate") in {
                "MATURE_DENSITY_CONVERGENCE",
                "LOCALLY_REFINED_MATURE_DENSITY_CONVERGENCE"
            }
        ),
        "mfem_uniform_equivalence_and_nc_face_consistent": bool(
            decision.get("mfem_uniform_equivalence") == "CERTIFIED"
            and decision.get("mfem_static_nc_hex_amr") == "AUTHORIZED"
            and decision["mfem_uniform_mature_equivalence"]["classification"]
            == "PASSED_PREDECLARED_MATURE_EQUIVALENCE_GATES"
            and decision["mfem_uniform_mature_equivalence"]["final_density_l1"] < 1.0e-3
            and decision["mfem_uniform_mature_equivalence"]["counted_certificate_rerun"]
            ["maximum_uncertified_cells"] == 0
            and decision["mfem_uniform_mature_equivalence"]["counted_certificate_rerun"]
            ["comparison_passed_after_wrapper_failure"]
            and decision["mfem_nc_face_probe"]["classification"]
            == "PASSED_NC_FACE_CONSERVATION_AND_EQUIVALENCE_PROBE"
            and decision["mfem_nc_face_probe"]["maximum_relative_action_error"] < 1.0e-9
            and decision.get("production_dataset_authorized") is False
            and decision.get("next_required_gate")
            == "LOCALLY_REFINED_MATURE_DENSITY_CONVERGENCE"
        ),
        "mfem_static_amr_decision_consistent": bool(
            decision["mfem_static_amr_reproduction"]["classification"]
            == "PASSED_STATIC_AMR_REPRODUCTION_GATES"
            and decision["mfem_static_amr_reproduction"]
            ["final_density_l1_to_fine_graded"] < 0.02
            and decision["mfem_static_amr_reproduction"]
            ["resource_efficiency_certified"] is False
            and decision["mfem_second_amr_level"]["classification"]
            == "PASSED_SECOND_AMR_LEVEL_GATES"
            and decision["mfem_second_amr_level"]
            ["final_density_l1_to_first_amr"] < 0.05
            and decision["mfem_second_amr_level"]
            ["final_density_l1_to_fine_graded"]
            >= decision["mfem_static_amr_reproduction"]
            ["final_density_l1_to_fine_graded"]
            and decision["mfem_second_amr_level"]
            ["mature_density_convergence_certified"] is False
            and decision["mfem_second_amr_level"]
            ["production_dataset_authorized"] is False
            and decision.get("next_required_gate")
            == "LOCALLY_REFINED_MATURE_DENSITY_CONVERGENCE"
        ),
        "mature_fine_graded_contraction_consistent": bool(
            mature_graded_fine["classification"]
            == "FAILED_PREDECLARED_MATURE_GRADED_EFFICIENCY_GATES"
            and mature_graded_fine["method_status"]
            == "MATURE_STATE_STATISTICAL_AND_POSITIVITY_GATES_PASSED"
            and mature_graded_fine["mature_density_convergence"] == "OPEN"
            and mature_graded_fine["all_320_steps_whole_cell_positive"]
            and mature_graded_fine["maximum_measured_negative_mass"] == 0.0
            and mature_graded_fine["absolute_mass_error"] <= 1.0e-10
            and mature_graded_fine["optimizer_failures"] == 0
            and mature_graded_fine["fallbacks"] == 0
            and mature_graded_fine["mean_relative_l1_correction"] <= 8.0e-4
            and mature_graded_fine["density_l1_vs_uniform60"] > 0.1
            and mature_graded_fine["density_l1_vs_graded44x52x46"] > 0.1
            and mature_graded_fine["runtime_ratio_vs_uniform60"] > 1.0
            and mature_graded_fine["dof_ratio_vs_uniform60"] < 1.0
            and mature_graded_fine["peak_rank_memory_ratio_vs_uniform60"] < 1.0
            and mature_graded_fine["production_dataset_authorized"] is False
            and decision.get("mature_density_convergence") == "OPEN"
            and decision.get("production_dataset_authorized") is False
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
            "full_spd_control_covariance_error": full_spd_control
            ["normalized_covariance_error"],
            "full_spd_control_mean_relative_l1_correction": full_spd_control
            ["mean_relative_l1_correction"],
            "full_spd_spatial_density_l1": full_spd_spatial
            ["density_l1_differences"],
            "full_spd_spatial_observed_common_grid_rate": full_spd_spatial
            ["observed_common_grid_spatial_rate"],
            "full_spd_spatial_covariance_errors": [
                branch["normalized_covariance_error"]
                for branch in full_spd_spatial["branches"]
            ],
            "mature_bimodal_density_l1": mature_bimodal["density_l1_differences"],
            "mature_bimodal_observed_common_grid_rate": mature_bimodal[
                "observed_common_grid_spatial_rate"
            ],
            "mature_bimodal_mean_relative_l1_corrections": mature_bimodal[
                "failed_gate"
            ]["observed"],
            "mature_certificate_maximum_rescued_fraction": mature_certificate[
                "aggregate"
            ]["maximum_fraction_of_depth4_noncertified_cells_rescued_by_depth8"],
            "mature_certificate_maximum_l1_reduction": mature_certificate[
                "aggregate"
            ]["maximum_l1_correction_reduction_from_depth8"],
            "mature_uniform60_mean_relative_l1_correction": mature_graded[
                "uniform60"
            ]["mean_relative_l1_correction"],
            "mature_graded_density_l1_vs_uniform60": mature_graded[
                "graded44x52x46"
            ]["density_l1_vs_uniform60"],
            "mature_graded_mean_relative_l1_correction": mature_graded[
                "graded44x52x46"
            ]["mean_relative_l1_correction"],
            "mature_fine_graded_density_l1_vs_uniform60": mature_graded_fine[
                "density_l1_vs_uniform60"
            ],
            "mature_fine_graded_density_l1_vs_first_graded": mature_graded_fine[
                "density_l1_vs_graded44x52x46"
            ],
            "mature_fine_graded_mean_relative_l1_correction": mature_graded_fine[
                "mean_relative_l1_correction"
            ],
            "mfem_first_amr_density_l1_to_fine_graded": decision[
                "mfem_static_amr_reproduction"
            ]["final_density_l1_to_fine_graded"],
            "mfem_second_amr_density_l1_to_first": decision[
                "mfem_second_amr_level"
            ]["final_density_l1_to_first_amr"],
            "mfem_second_amr_density_l1_to_fine_graded": decision[
                "mfem_second_amr_level"
            ]["final_density_l1_to_fine_graded"],
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
