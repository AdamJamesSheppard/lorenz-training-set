#!/usr/bin/env python3
"""Freeze third-depth marks from the unchanged time-aggregated replay indicator."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.ndimage import binary_dilation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("indicator", type=Path)
    parser.add_argument("axes", type=Path)
    parser.add_argument("second_marks", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    source = np.load(args.indicator)
    edges = json.loads(args.axes.read_text())["edge_indices"]
    if source.shape != tuple(len(edges[axis]) - 1 for axis in "xyz"):
        raise ValueError("indicator and source axes differ")
    parent_shape = (90, 108, 108)
    grandchild_shape = (180, 216, 216)
    second = np.fromfile(args.second_marks, dtype=np.uint8).reshape(parent_shape).astype(bool)
    permitted = second.repeat(2, axis=0).repeat(2, axis=1).repeat(2, axis=2)
    source_to_grandchild = []
    for axis, count in zip("xyz", grandchild_shape):
        edge = np.asarray(edges[axis], dtype=np.float64)
        midpoint = 0.5 * (edge[:-1] + edge[1:])
        source_to_grandchild.append(np.minimum(count - 1, midpoint.astype(int)))
    ix, iy, iz = np.meshgrid(*source_to_grandchild, indexing="ij")
    energy = np.zeros(grandchild_shape, dtype=np.float64)
    np.add.at(energy, (ix, iy, iz), source * source)
    target = 0.95
    if energy[permitted].sum() / energy.sum() < target:
        raise ValueError("second-level mesh excludes the predeclared replay-energy target")
    flat = energy.ravel()
    eligible = np.flatnonzero(permitted.ravel())
    descending = eligible[np.argsort(flat[eligible])[::-1]]
    raw_count = int(np.searchsorted(np.cumsum(flat[descending]),
                                    target * flat.sum()) + 1)
    raw = np.zeros(flat.size, dtype=bool)
    raw[descending[:raw_count]] = True
    marks = binary_dilation(raw.reshape(grandchild_shape), iterations=1) & permitted
    covered = float(energy[marks].sum() / energy.sum())
    second_cells = 163_728
    estimated_cells = int(second_cells + 7 * marks.sum())
    if covered < target or estimated_cells >= 220_864:
        raise ValueError("third-depth marks miss energy or DG-DOF budget")
    marks.astype(np.uint8).tofile(args.output / "grandchild_cell_marks.bin")
    (args.output / "design.json").write_text(json.dumps({
        "grandchild_shape": grandchild_shape,
        "common_export_grid": [180, 216, 216],
        "second_level_marked_cells": int(second.sum()),
        "third_level_raw_marked_cells": raw_count,
        "third_level_buffered_marked_cells": int(marks.sum()),
        "third_level_energy_target": target,
        "third_level_energy_achieved": covered,
        "estimated_cells_before_nc_balance": estimated_cells,
        "estimated_dg_dofs_before_nc_balance": 27 * estimated_cells,
        "fine_graded_dg_dofs": 5_963_328,
        "source_indicator": str(args.indicator),
        "source_axes": str(args.axes),
        "second_level_marks": str(args.second_marks),
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
