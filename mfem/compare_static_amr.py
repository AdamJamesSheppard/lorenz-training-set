#!/usr/bin/env python3
"""Audit static NC-hex reproduction against the frozen fine graded run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np
from scipy.ndimage import gaussian_filter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compare_mature_equivalence import BOUNDS, SHAPE, VOLUME, statistics


def coarsen(values: np.ndarray, shape: tuple[int, int, int]) -> np.ndarray:
    factors = tuple(a // b for a, b in zip(values.shape, shape))
    if any(a != b * factor for a, b, factor in zip(values.shape, shape, factors)):
        raise ValueError("common grid does not coarsen exactly")
    return values.reshape(
        shape[0], factors[0], shape[1], factors[1], shape[2], factors[2]
    ).mean(axis=(1, 3, 5))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_directory", type=Path)
    parser.add_argument("fine_directory", type=Path)
    parser.add_argument("particles", type=Path)
    args = parser.parse_args()
    mfem = args.run_directory / "mfem"
    if not mfem.is_dir():
        mfem = args.run_directory
    candidate = np.fromfile(
        mfem / "final_q2_subcell_averages.bin", dtype=np.float64
    ).reshape(SHAPE)
    fine = np.load(args.fine_directory / "final_q2_subcell_averages.npy")
    summary = json.loads((mfem / "mature_summary.json").read_text())
    fine_report = json.loads((args.fine_directory / "report.json").read_text())
    comparator = fine_report["comparisons_to_common_mc"]["final"]
    particles = np.load(args.particles)
    voxel = VOLUME / candidate.size
    density_l1 = float(voxel * np.abs(candidate - fine).sum())
    negative_mass = float(voxel * np.maximum(-candidate, 0.0).sum())
    stats = statistics(candidate)
    numerical_probability = candidate * voxel
    mc_covariance = np.cov(particles, rowvar=False)
    covariance_error = float(np.linalg.norm(
        np.asarray(stats["covariance"]) - mc_covariance, "fro"
    ) / np.linalg.norm(mc_covariance, "fro"))
    marginal_tv = []
    for axis, (bounds, count) in enumerate(zip(BOUNDS, SHAPE)):
        numerical = numerical_probability.sum(axis=tuple(i for i in range(3) if i != axis))
        empirical = np.histogram(particles[:, axis], bins=count, range=bounds)[0]
        empirical = empirical / len(particles)
        marginal_tv.append(float(0.5 * np.abs(numerical - empirical).sum()))
    half = SHAPE[0] // 2
    lobes = {
        "negative_x": float(numerical_probability[:half].sum()),
        "positive_x": float(numerical_probability[half:].sum()),
    }
    mc_lobes = {
        "negative_x": float(np.mean(particles[:, 0] < 0.0)),
        "positive_x": float(np.mean(particles[:, 0] > 0.0)),
    }
    lobe_error = max(abs(lobes[key] - mc_lobes[key]) for key in lobes)
    joint_shape = (20, 24, 24)
    numerical_joint = coarsen(candidate, joint_shape) * VOLUME / np.prod(joint_shape)
    histogram, _ = np.histogramdd(particles, bins=joint_shape, range=BOUNDS)
    mc_joint = histogram / len(particles)
    joint_tv = float(0.5 * np.abs(
        gaussian_filter(numerical_joint, 0.75, mode="constant")
        - gaussian_filter(mc_joint, 0.75, mode="constant")
    ).sum())
    limits = {
        "density_l1_to_fine_graded": 0.02,
        "mean_correction": 8.0e-4,
        "mass_error": 1.0e-10,
        "negative_mass": 1.0e-13,
        "statistical_degradation": 0.005,
        "fine_graded_dofs": 5_963_328,
    }
    gf_covariance = comparator["covariance_accuracy"]["normalized_frobenius_error"]
    gf_joint = comparator["joint_density"]["smoothed_total_variation"]
    gf_marginal = max(comparator["marginal_total_variation_distance"])
    gf_lobe = comparator["maximum_lobe_probability_error"]
    gates = {
        "density_reproduction": density_l1 < limits["density_l1_to_fine_graded"],
        "correction": summary["mean_relative_l1_correction"] < limits["mean_correction"],
        "mass": summary["maximum_absolute_mass_error"] < limits["mass_error"],
        "negative_mass": negative_mass <= limits["negative_mass"],
        "whole_cell_positivity": summary["whole_cell_positivity_certified"]
            and summary["maximum_uncertified_cells"] == 0
            and summary["initial_uncertified_cells"] == 0,
        "optimizer": summary["optimizer_failures"] == 0 and summary["fallbacks"] == 0,
        "covariance": covariance_error <= gf_covariance + limits["statistical_degradation"],
        "joint_tv": joint_tv <= gf_joint + limits["statistical_degradation"],
        "marginals": max(marginal_tv) <= gf_marginal + limits["statistical_degradation"],
        "lobes": lobe_error <= gf_lobe + limits["statistical_degradation"],
        "dofs": summary["cells"] * 27 < limits["fine_graded_dofs"],
    }
    report = {
        "status": "PASSED_STATIC_AMR_REPRODUCTION_GATES" if all(gates.values())
                  else "FAILED_STATIC_AMR_REPRODUCTION_GATES",
        "density_l1_to_fine_graded": density_l1,
        "negative_mass_on_common_grid": negative_mass,
        "candidate_statistics": stats,
        "normalized_covariance_error_to_mc": covariance_error,
        "marginal_tv_to_mc": marginal_tv,
        "joint_tv_to_mc": joint_tv,
        "lobe_probabilities": lobes,
        "maximum_lobe_error_to_mc": lobe_error,
        "comparator_metrics": {
            "normalized_covariance_error_to_mc": gf_covariance,
            "maximum_marginal_tv_to_mc": gf_marginal,
            "joint_tv_to_mc": gf_joint,
            "maximum_lobe_error_to_mc": gf_lobe,
        },
        "limits": limits,
        "gates": gates,
        "amr_summary": summary,
        "mature_density_convergence_certified": False,
        "second_amr_level_required": all(gates.values()),
        "production_dataset_authorized": False,
    }
    (args.run_directory / "static_amr_comparison.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps({"status": report["status"],
                      "density_l1_to_fine_graded": density_l1,
                      "gates": gates}, indent=2))
    return 0 if all(gates.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
