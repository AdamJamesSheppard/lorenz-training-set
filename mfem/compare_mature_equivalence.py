#!/usr/bin/env python3
"""Audit the complete MFEM mature trajectory against the frozen DOLFINx run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


BOUNDS = ((-30.0, 30.0), (-40.0, 40.0), (-10.0, 70.0))
SHAPE = (180, 216, 216)
VOLUME = 60.0 * 80.0 * 80.0


def statistics(values: np.ndarray) -> dict[str, object]:
    voxel = VOLUME / values.size
    probability = values * voxel
    mass = float(probability.sum())
    axes = [np.linspace(lo, hi, n, endpoint=False) + (hi - lo) / (2 * n)
            for (lo, hi), n in zip(BOUNDS, values.shape)]
    means = np.array([
        float((probability * axis.reshape((-1 if d == 0 else 1,
                                           -1 if d == 1 else 1,
                                           -1 if d == 2 else 1))).sum() / mass)
        for d, axis in enumerate(axes)
    ])
    covariance = np.empty((3, 3))
    for i in range(3):
        xi = axes[i].reshape((-1 if i == 0 else 1, -1 if i == 1 else 1, -1 if i == 2 else 1))
        for j in range(3):
            xj = axes[j].reshape((-1 if j == 0 else 1, -1 if j == 1 else 1, -1 if j == 2 else 1))
            covariance[i, j] = float((probability * (xi - means[i]) * (xj - means[j])).sum() / mass)
    return {"mass": mass, "mean": means.tolist(), "covariance": covariance.tolist()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_directory", type=Path)
    parser.add_argument("reference_directory", type=Path)
    args = parser.parse_args()
    mfem = args.run_directory / "mfem"
    shared = args.run_directory / "shared_initial"
    initial_reference = np.load(shared / "initial_q2_subcell_averages.npy")
    initial_candidate = np.fromfile(
        mfem / "initial_q2_subcell_averages.bin", dtype=np.float64
    ).reshape(SHAPE)
    final_reference = np.load(args.reference_directory / "final_q2_subcell_averages.npy")
    final_candidate = np.fromfile(
        mfem / "final_q2_subcell_averages.bin", dtype=np.float64
    ).reshape(SHAPE)
    summary = json.loads((mfem / "mature_summary.json").read_text())
    reference_report = json.loads((args.reference_directory / "report.json").read_text())
    voxel = VOLUME / np.prod(SHAPE)
    initial_l1 = float(voxel * np.abs(initial_candidate - initial_reference).sum())
    final_l1 = float(voxel * np.abs(final_candidate - final_reference).sum())
    candidate_stats = statistics(final_candidate)
    reference_stats = statistics(final_reference)
    mean_error = float(np.linalg.norm(
        np.asarray(candidate_stats["mean"]) - np.asarray(reference_stats["mean"])
    ))
    covariance_error = float(np.linalg.norm(
        np.asarray(candidate_stats["covariance"]) - np.asarray(reference_stats["covariance"]), "fro"
    ))
    reference_correction = reference_report["limiter_history"]["relative_l1_correction"]
    correction_differences = {
        "mean": abs(summary["mean_relative_l1_correction"] - reference_correction["mean"]),
        "maximum": abs(summary["maximum_relative_l1_correction"] - reference_correction["maximum"]),
    }
    limits = {
        "initial_density_l1": 1.0e-10, "final_density_l1": 1.0e-3,
        "mass_error": 1.0e-10, "mean_vector_error": 1.0e-3,
        "covariance_frobenius_error": 2.0e-2,
        "mean_correction_difference": 1.0e-4,
        "maximum_correction_difference": 1.0e-4,
    }
    gates = {
        "shared_initial_state": initial_l1 <= limits["initial_density_l1"],
        "final_density": final_l1 <= limits["final_density_l1"],
        "mass": summary["maximum_absolute_mass_error"] <= limits["mass_error"],
        "mean": mean_error <= limits["mean_vector_error"],
        "covariance": covariance_error <= limits["covariance_frobenius_error"],
        "mean_correction": correction_differences["mean"] <= limits["mean_correction_difference"],
        "maximum_correction": correction_differences["maximum"] <= limits["maximum_correction_difference"],
        "optimizer": summary["optimizer_failures"] == 0 and summary["fallbacks"] == 0,
        "positivity": bool(summary["whole_cell_positivity_certified"]),
    }
    passed = all(gates.values())
    report = {
        "status": "PASSED_PREDECLARED_MATURE_EQUIVALENCE_GATES" if passed else "FAILED_PREDECLARED_MATURE_EQUIVALENCE_GATES",
        "initial_density_l1": initial_l1, "final_density_l1": final_l1,
        "mean_vector_error": mean_error,
        "covariance_frobenius_error": covariance_error,
        "correction_differences": correction_differences,
        "mfem": summary, "candidate_statistics": candidate_stats,
        "reference_statistics": reference_stats, "limits": limits, "gates": gates,
        "amr_authorized": passed,
    }
    (args.run_directory / "mature_equivalence_report.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps({"status": report["status"], "final_density_l1": final_l1,
                      "gates": gates}, indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
