#!/usr/bin/env python3
"""Audit second static NC-hex level against AMR1, g_f, and the particle reference."""

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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_directory", type=Path)
    parser.add_argument("first_directory", type=Path)
    parser.add_argument("fine_directory", type=Path)
    parser.add_argument("particles", type=Path)
    args = parser.parse_args()
    candidate = np.fromfile(
        args.run_directory / "mfem/final_q2_subcell_averages.bin",
        dtype=np.float64,
    ).reshape(SHAPE)
    first = np.fromfile(
        args.first_directory / "mfem/final_q2_subcell_averages.bin",
        dtype=np.float64,
    ).reshape(SHAPE)
    fine = np.load(args.fine_directory / "final_q2_subcell_averages.npy")
    summary = json.loads((args.run_directory / "mfem/mature_summary.json").read_text())
    first_report = json.loads(
        (args.first_directory / "static_amr_comparison.json").read_text()
    )
    particles = np.load(args.particles)
    voxel = VOLUME / candidate.size
    density_to_first = float(voxel * np.abs(candidate - first).sum())
    density_to_fine = float(voxel * np.abs(candidate - fine).sum())
    negative_mass = float(voxel * np.maximum(-candidate, 0.0).sum())
    candidate_stats = statistics(candidate)
    mc_covariance = np.cov(particles, rowvar=False)
    covariance_error = float(
        np.linalg.norm(np.asarray(candidate_stats["covariance"]) - mc_covariance, "fro")
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
    lobe_error = max(
        abs(lobes[key] - float(np.mean(particles[:, 0] < 0.0 if key == "negative_x"
                                      else particles[:, 0] > 0.0)))
        for key in lobes
    )
    joint_shape = (20, 24, 24)
    numerical_joint = coarsen(candidate, joint_shape) * VOLUME / np.prod(joint_shape)
    histogram, _ = np.histogramdd(particles, bins=joint_shape, range=BOUNDS)
    joint_tv = float(0.5 * np.abs(
        gaussian_filter(numerical_joint, 0.75, mode="constant")
        - gaussian_filter(histogram / len(particles), 0.75, mode="constant")
    ).sum())
    reference = first_report["comparator_metrics"]
    limits = {
        "maximum_density_l1_to_first": 0.05,
        "maximum_mean_relative_l1_correction": 8.0e-4,
        "maximum_absolute_mass_error": 1.0e-10,
        "maximum_common_grid_negative_mass": 1.0e-13,
        "maximum_statistical_degradation_to_mc_vs_fine": 0.005,
        "maximum_dofs": 5_963_328,
    }
    gates = {
        "density_contraction": density_to_first <= limits["maximum_density_l1_to_first"],
        "correction": summary["mean_relative_l1_correction"]
            < limits["maximum_mean_relative_l1_correction"],
        "mass": summary["maximum_absolute_mass_error"]
            < limits["maximum_absolute_mass_error"],
        "negative_mass": negative_mass <= limits["maximum_common_grid_negative_mass"],
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
        "status": "PASSED_SECOND_AMR_LEVEL_GATES" if all(gates.values())
                  else "FAILED_SECOND_AMR_LEVEL_GATES",
        "density_l1_to_first_amr": density_to_first,
        "density_l1_to_fine_graded": density_to_fine,
        "first_amr_density_l1_to_fine_graded":
            first_report["density_l1_to_fine_graded"],
        "negative_mass_on_common_grid": negative_mass,
        "candidate_statistics": candidate_stats,
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
    (args.run_directory / "static_amr_level2_comparison.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps({
        "status": report["status"],
        "density_l1_to_first_amr": density_to_first,
        "density_l1_to_fine_graded": density_to_fine,
        "gates": gates,
    }, indent=2))
    return 0 if all(gates.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
