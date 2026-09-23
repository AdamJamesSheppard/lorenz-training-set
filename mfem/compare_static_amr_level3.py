#!/usr/bin/env python3
"""Audit third-depth AMR contraction on the frozen conservative common grid."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np
from scipy.ndimage import gaussian_filter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compare_mature_equivalence import BOUNDS, SHAPE, VOLUME, statistics
from compare_static_amr import coarsen


def read_grid(path: Path) -> np.ndarray:
    values = np.fromfile(path, dtype=np.float64)
    if values.size != int(np.prod(SHAPE)):
        raise ValueError(f"unexpected conservative-grid size: {path}")
    return values.reshape(SHAPE)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_directory", type=Path)
    parser.add_argument("first_directory", type=Path)
    parser.add_argument("second_directory", type=Path)
    parser.add_argument("fine_directory", type=Path)
    parser.add_argument("particles", type=Path)
    args = parser.parse_args()
    candidate_dir = args.run_directory / "mfem"
    if not candidate_dir.is_dir():
        candidate_dir = args.run_directory
    candidate = read_grid(candidate_dir / "final_q2_subcell_averages.bin")
    initial = read_grid(candidate_dir / "initial_q2_subcell_averages.bin")
    second_dir = args.second_directory / "mfem"
    second = read_grid(second_dir / "final_q2_subcell_averages.bin")
    second_initial = read_grid(second_dir / "initial_q2_subcell_averages.bin")
    fine = np.load(args.fine_directory / "final_q2_subcell_averages.npy")
    summary = json.loads((candidate_dir / "mature_summary.json").read_text())
    first_report = json.loads(
        (args.first_directory / "static_amr_comparison.json").read_text()
    )
    second_report = json.loads(
        (args.second_directory / "static_amr_level2_comparison.json").read_text()
    )
    particles = np.load(args.particles)
    voxel = VOLUME / candidate.size
    density_to_second = float(voxel * np.abs(candidate - second).sum())
    initial_to_second = float(voxel * np.abs(initial - second_initial).sum())
    density_to_fine = float(voxel * np.abs(candidate - fine).sum())
    negative_mass = float(voxel * np.maximum(-candidate, 0.0).sum())
    initial_negative_mass = float(voxel * np.maximum(-initial, 0.0).sum())
    exported_mass_error = max(
        abs(float(voxel * candidate.sum()) - summary["final_mass"]),
        abs(float(voxel * initial.sum()) - summary["initial_mass"]),
    )
    stats = statistics(candidate)
    mc_covariance = np.cov(particles, rowvar=False)
    covariance_error = float(
        np.linalg.norm(np.asarray(stats["covariance"]) - mc_covariance, "fro")
        / np.linalg.norm(mc_covariance, "fro")
    )
    probability = candidate * voxel
    marginal_tv = []
    for axis, (bounds, count) in enumerate(zip(BOUNDS, SHAPE)):
        numerical = probability.sum(axis=tuple(i for i in range(3) if i != axis))
        empirical = np.histogram(particles[:, axis], bins=count, range=bounds)[0]
        marginal_tv.append(float(0.5 * np.abs(numerical - empirical / len(particles)).sum()))
    half = SHAPE[0] // 2
    lobes = {
        "negative_x": float(probability[:half].sum()),
        "positive_x": float(probability[half:].sum()),
    }
    mc_lobes = {
        "negative_x": float(np.mean(particles[:, 0] < 0.0)),
        "positive_x": float(np.mean(particles[:, 0] > 0.0)),
    }
    lobe_error = max(abs(lobes[key] - mc_lobes[key]) for key in lobes)
    joint_shape = (20, 24, 24)
    numerical_joint = coarsen(candidate, joint_shape) * VOLUME / np.prod(joint_shape)
    histogram, _ = np.histogramdd(particles, bins=joint_shape, range=BOUNDS)
    joint_tv = float(0.5 * np.abs(
        gaussian_filter(numerical_joint, 0.75, mode="constant")
        - gaussian_filter(histogram / len(particles), 0.75, mode="constant")
    ).sum())
    reference = first_report["comparator_metrics"]
    limits = {
        "maximum_final_density_l1_to_second": 0.007853258960160175,
        "maximum_mean_relative_l1_correction": 8.0e-4,
        "maximum_absolute_mass_error": 1.0e-10,
        "maximum_common_grid_negative_mass": 1.0e-13,
        "maximum_export_mass_error": 1.0e-10,
        "maximum_statistical_degradation_to_mc_vs_fine": 0.005,
        "maximum_dofs": 5_963_328,
    }
    gates = {
        "voxel_density_contraction": density_to_second
            <= limits["maximum_final_density_l1_to_second"],
        "correction": summary["mean_relative_l1_correction"]
            < limits["maximum_mean_relative_l1_correction"],
        "mass": summary["maximum_absolute_mass_error"]
            < limits["maximum_absolute_mass_error"],
        "negative_mass": max(negative_mass, initial_negative_mass)
            <= limits["maximum_common_grid_negative_mass"],
        "export_mass": exported_mass_error < limits["maximum_export_mass_error"],
        "whole_cell_positivity": summary["whole_cell_positivity_certified"]
            and summary["maximum_uncertified_cells"] == 0
            and summary["initial_uncertified_cells"] == 0,
        "optimizer": summary["optimizer_failures"] == 0 and summary["fallbacks"] == 0,
        "covariance": covariance_error <=
            reference["normalized_covariance_error_to_mc"]
            + limits["maximum_statistical_degradation_to_mc_vs_fine"],
        "joint_tv": joint_tv <= reference["joint_tv_to_mc"]
            + limits["maximum_statistical_degradation_to_mc_vs_fine"],
        "marginals": max(marginal_tv) <= reference["maximum_marginal_tv_to_mc"]
            + limits["maximum_statistical_degradation_to_mc_vs_fine"],
        "lobes": lobe_error <= reference["maximum_lobe_error_to_mc"]
            + limits["maximum_statistical_degradation_to_mc_vs_fine"],
        "dofs": 27 * summary["cells"] < limits["maximum_dofs"],
    }
    report = {
        "status": "PASSED_THIRD_DEPTH_VOXEL_GATES" if all(gates.values())
                  else "FAILED_THIRD_DEPTH_VOXEL_GATES",
        "comparison_representation": "conservative_180x216x216_voxel_averages",
        "subvoxel_q2_convergence_tested": False,
        "density_l1_to_second_amr": density_to_second,
        "previous_density_l1_first_to_second":
            second_report["density_l1_to_first_amr"],
        "density_difference_ratio": density_to_second
            / second_report["density_l1_to_first_amr"],
        "initial_density_l1_to_second_amr": initial_to_second,
        "density_l1_to_fine_graded": density_to_fine,
        "negative_mass_on_common_grid": negative_mass,
        "initial_negative_mass_on_common_grid": initial_negative_mass,
        "maximum_export_mass_error": exported_mass_error,
        "candidate_statistics": stats,
        "normalized_covariance_error_to_mc": covariance_error,
        "marginal_tv_to_mc": marginal_tv,
        "joint_tv_to_mc": joint_tv,
        "lobe_probabilities": lobes,
        "maximum_lobe_error_to_mc": lobe_error,
        "limits": limits,
        "gates": gates,
        "amr_summary": summary,
        "mature_density_convergence_certified": False,
        "production_dataset_authorized": False,
    }
    (args.run_directory / "static_amr_level3_comparison.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps({
        "status": report["status"],
        "density_l1_to_second_amr": density_to_second,
        "density_difference_ratio": report["density_difference_ratio"],
        "gates": gates,
    }, indent=2))
    return 0 if all(gates.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
