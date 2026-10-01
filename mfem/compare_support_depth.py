#!/usr/bin/env python3
"""Audit targeted depth sensitivity against the fixed-support comparator."""
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
    result = subprocess.run([sys.executable, "-B", str(args.repo / "mfem/compare_support_test.py"),
                             str(args.repo), str(args.run)], check=False)
    if result.returncode not in (0, 2):
        raise RuntimeError("statistical audit failed")
    report = json.loads((args.run / "support_comparison.json").read_text())
    previous = args.repo / "runs/mfem-support-sensitivity/20261001T144235Z/mfem"
    current = args.run / "mfem"
    for stage in ("initial", "final"):
        a = np.fromfile(current / f"{stage}_q2_subcell_averages.bin", dtype=np.float64)
        b = np.fromfile(previous / f"{stage}_q2_subcell_averages.bin", dtype=np.float64)
        if a.shape != b.shape:
            raise ValueError("common-grid sizes differ")
        report[f"{stage}_density_l1_to_fixed_support"] = float(384000 / a.size * np.abs(a - b).sum())
    report["gates"].pop("support_reproduction")
    report["gates"]["targeted_depth_difference"] = report["final_density_l1_to_fixed_support"] <= 0.007853258960160175
    report["limits"]["maximum_density_l1_to_fixed_support"] = 0.007853258960160175
    report["status"] = "PASSED_TARGETED_DEPTH_GATES" if all(report["gates"].values()) else "FAILED_TARGETED_DEPTH_GATES"
    report["scope"] = "partial third-depth refinement on fixed expanded support; no full-density certification"
    (args.run / "support_depth_comparison.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("status", "final_density_l1_to_fixed_support", "gates")}, indent=2))
    return 0 if all(report["gates"].values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
