#!/usr/bin/env python3
"""Freeze expanded refinement support from the completed AMR2/AMR3 discrepancy."""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.ndimage import binary_dilation


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--coverage", type=float, default=0.95)
    parser.add_argument("--buffer", type=int, default=1)
    args = parser.parse_args()
    if not 0 < args.coverage < 1 or args.buffer < 1:
        raise ValueError("coverage must lie in (0,1) and buffer must be positive")
    runs = args.repo / "runs"
    first = runs / "mfem-static-amr-reproduction/20260916T221235Z"
    second = runs / "mfem-static-amr-level2/20260922T231219Z"
    third = runs / "mfem-static-amr-level3/20260923T181337Z"
    shape = (180, 216, 216)
    a = np.fromfile(second / "mfem/final_q2_subcell_averages.bin", dtype=np.float64).reshape(shape)
    b = np.fromfile(third / "mfem/final_q2_subcell_averages.bin", dtype=np.float64).reshape(shape)
    difference = np.abs(a - b)
    old = np.fromfile(second / "design/child_cell_marks.bin", dtype=np.uint8).reshape(90, 108, 108).astype(bool)
    deep = np.fromfile(third / "design/grandchild_cell_marks.bin", dtype=np.uint8).reshape(shape).astype(bool)
    permitted = old.repeat(2, 0).repeat(2, 1).repeat(2, 2)
    energy = difference.reshape(90, 2, 108, 2, 108, 2).sum(axis=(1, 3, 5))
    order = np.argsort(energy.ravel())[::-1]
    count = int(np.searchsorted(np.cumsum(energy.ravel()[order]), args.coverage * energy.sum()) + 1)
    raw = np.zeros(energy.size, dtype=bool)
    raw[order[:count]] = True
    marks = binary_dilation(raw.reshape(energy.shape), iterations=args.buffer) | old
    if args.coverage > 0.95:
        baseline = runs / "mfem-support-sensitivity/20261001T144235Z/design/child_cell_marks.bin"
        marks |= np.fromfile(baseline, dtype=np.uint8).reshape(energy.shape).astype(bool)
    base = np.fromfile(first / "design/base_cell_marks.bin", dtype=np.uint8).reshape(45, 54, 54).astype(bool)
    parents = marks.reshape(45, 2, 54, 2, 54, 2).any(axis=(1, 3, 5)) | base
    estimated = int(45 * 54 * 54 + 7 * parents.sum() + 7 * marks.sum())
    if estimated >= 220864:
        raise ValueError("expanded support exceeds the predeclared estimated cell budget")
    args.output.mkdir(parents=True, exist_ok=True)
    parents.astype(np.uint8).tofile(args.output / "base_cell_marks.bin")
    marks.astype(np.uint8).tofile(args.output / "child_cell_marks.bin")
    np.save(args.output / "density_difference_indicator.npy", energy)
    report = {
        "diagnostic_density_l1": float(384000 / difference.size * difference.sum()),
        "difference_fraction_outside_third_marks": float(difference[~deep].sum() / difference.sum()),
        "difference_fraction_outside_second_support": float(difference[~permitted].sum() / difference.sum()),
        "indicator": "summed_absolute_AMR2_AMR3_final_voxel_density_difference",
        "dorfler_l1_coverage_target": args.coverage,
        "coverage_after_buffer_and_union": float(energy[marks].sum() / energy.sum()),
        "buffer_child_cells": args.buffer,
        "base_marked_cells": int(parents.sum()),
        "child_marked_cells": int(marks.sum()),
        "estimated_cells_before_nc_balance": estimated,
        "same_finest_cell_size_as_amr2": True,
        "scope": "final-state discrepancy-driven support sensitivity; indicator is not an a posteriori error bound",
    }
    (args.output / "design.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
