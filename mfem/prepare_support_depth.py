#!/usr/bin/env python3
"""Freeze a bounded third depth on the expanded, fixed support."""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.ndimage import binary_dilation


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    runs = args.repo / "runs"
    support = runs / "mfem-support-sensitivity/20261001T144235Z"
    shape = (180, 216, 216)
    a = np.fromfile(runs / "mfem-static-amr-level2/20260922T231219Z/mfem/final_q2_subcell_averages.bin", dtype=np.float64).reshape(shape)
    b = np.fromfile(runs / "mfem-static-amr-level3/20260923T181337Z/mfem/final_q2_subcell_averages.bin", dtype=np.float64).reshape(shape)
    score = np.abs(a - b)
    parent = np.fromfile(support / "design/child_cell_marks.bin", dtype=np.uint8).reshape(90, 108, 108).astype(bool)
    permitted = parent.repeat(2, 0).repeat(2, 1).repeat(2, 2)
    eligible = np.flatnonzero(permitted.ravel())
    order = eligible[np.argsort(score.ravel()[eligible])[::-1]]
    raw = np.zeros(score.size, dtype=bool)
    raw[order[:512]] = True
    marks = binary_dilation(raw.reshape(shape), iterations=1) & permitted
    if marks.sum() > 2048:
        raise ValueError("third-depth buffered marks exceed prospective memory budget")
    args.output.mkdir(parents=True, exist_ok=True)
    marks.astype(np.uint8).tofile(args.output / "grandchild_cell_marks.bin")
    report = {
        "fixed_support_run": str(support),
        "raw_marked_cells": 512,
        "buffered_marked_cells": int(marks.sum()),
        "covered_final_difference_fraction": float(score[marks].sum() / score.sum()),
        "estimated_cells_before_balance": int(189460 + 7 * marks.sum()),
        "marking_score": "saved_absolute_AMR2_AMR3_density_difference",
        "scope": "bounded_targeted_depth_sensitivity_on_fixed_expanded_support",
    }
    (args.output / "design.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
