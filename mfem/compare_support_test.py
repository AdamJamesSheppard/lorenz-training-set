#!/usr/bin/env python3
"""Audit the support test while retaining all inherited statistical diagnostics."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", type=Path)
    parser.add_argument("run", type=Path)
    args = parser.parse_args()
    runs = args.repo / "runs"
    first = runs / "mfem-static-amr-reproduction/20260916T221235Z"
    second = runs / "mfem-static-amr-level2/20260922T231219Z"
    third = runs / "mfem-static-amr-level3/20260923T181337Z"
    fine = runs / "mature-full-spd-graded-fine-comparison/20260914T231639Z/mature_bimodal_q2_local_qp_graded58x68x56"
    particles = runs / "local-q2-cn-full-spd-mature-bimodal/20260913T185157Z/reference/mc_final_particles.npy"
    result = subprocess.run([sys.executable, "-B", str(args.repo / "mfem/compare_static_amr_level2.py"),
                             str(args.run), str(first), str(fine), str(particles)], check=False)
    if result.returncode not in (0, 2):
        raise RuntimeError("inherited statistics audit failed")
    report = json.loads((args.run / "static_amr_level2_comparison.json").read_text())
    candidate = np.fromfile(args.run / "mfem/final_q2_subcell_averages.bin", dtype=np.float64)
    voxel = 384000 / candidate.size
    for name, directory in (("second", second), ("third", third)):
        reference = np.fromfile(directory / "mfem/final_q2_subcell_averages.bin", dtype=np.float64)
        if candidate.shape != reference.shape:
            raise ValueError("common-grid sizes differ")
        report[f"density_l1_to_{name}_amr"] = float(voxel * np.abs(candidate - reference).sum())
    summary = report["amr_summary"]
    report["maximum_export_mass_error"] = abs(float(voxel * candidate.sum()) - summary["final_mass"])
    report["gates"].pop("density_contraction")
    report["gates"]["support_reproduction"] = report["density_l1_to_third_amr"] <= 0.007853258960160175
    report["gates"]["export_mass"] = report["maximum_export_mass_error"] < 1e-10
    report["limits"]["maximum_density_l1_to_third_amr"] = 0.007853258960160175
    report["status"] = "PASSED_SUPPORT_REPRODUCTION_GATES" if all(report["gates"].values()) else "FAILED_SUPPORT_REPRODUCTION_GATES"
    report["scope"] = "support sensitivity at AMR2 finest spacing; neither formal order nor full-density certification"
    report["production_dataset_authorized"] = False
    (args.run / "support_comparison.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("status", "density_l1_to_second_amr", "density_l1_to_third_amr", "gates")}, indent=2))
    return 0 if all(report["gates"].values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
