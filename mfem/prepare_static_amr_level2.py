#!/usr/bin/env python3
"""Freeze second-level marks from the same time-aggregated replay indicator."""

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
    parser.add_argument("first_marks", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    source = np.load(args.indicator)
    edges = json.loads(args.axes.read_text())["edge_indices"]
    if source.shape != tuple(len(edges[axis]) - 1 for axis in "xyz"):
        raise ValueError("indicator and source axes differ")
    base_shape = (45, 54, 54)
    child_shape = tuple(2 * count for count in base_shape)
    first = np.fromfile(args.first_marks, dtype=np.uint8).reshape(base_shape).astype(bool)
    permitted = first.repeat(2, axis=0).repeat(2, axis=1).repeat(2, axis=2)
    source_to_child = []
    for axis, count in zip("xyz", child_shape):
        edge = np.asarray(edges[axis], dtype=np.float64)
        midpoint = 0.5 * (edge[:-1] + edge[1:])
        source_to_child.append(np.minimum(count - 1, (midpoint / 2).astype(int)))
    ix, iy, iz = np.meshgrid(*source_to_child, indexing="ij")
    energy = np.zeros(child_shape, dtype=np.float64)
    np.add.at(energy, (ix, iy, iz), source * source)
    if energy[permitted].sum() < 0.99 * energy.sum():
        raise ValueError("first-level marks exclude more than one percent of replay energy")

    # Target 95% of total replay energy on this already refined background.
    # This is a predeclared second-level cost/coverage compromise, not a
    # retrospective modification of the first-level 99% gate.
    flat = energy.ravel()
    eligible = np.flatnonzero(permitted.ravel())
    descending = eligible[np.argsort(flat[eligible])[::-1]]
    raw_count = int(np.searchsorted(
        np.cumsum(flat[descending]), 0.95 * flat.sum()) + 1)
    raw = np.zeros(flat.size, dtype=bool)
    raw[descending[:raw_count]] = True
    marks = binary_dilation(raw.reshape(child_shape), iterations=1) & permitted
    selected_energy = float(energy[marks].sum() / energy.sum())
    estimated_cells = int(np.prod(base_shape) + 7 * first.sum() + 7 * marks.sum())
    if selected_energy < 0.95 or estimated_cells >= 220_864:
        raise ValueError("second-level design misses coverage or DG-DOF budget")
    marks.astype(np.uint8).tofile(args.output / "child_cell_marks.bin")
    (args.output / "design.json").write_text(json.dumps({
        "base_shape": base_shape,
        "child_shape": child_shape,
        "common_shape": [180, 216, 216],
        "first_level_marked_cells": int(first.sum()),
        "second_level_raw_marked_cells": raw_count,
        "second_level_buffered_marked_cells": int(marks.sum()),
        "second_level_energy_target": 0.95,
        "second_level_energy_achieved": selected_energy,
        "estimated_cells_before_nc_balance": estimated_cells,
        "estimated_dg_dofs_before_nc_balance": 27 * estimated_cells,
        "source_indicator": str(args.indicator),
        "source_axes": str(args.axes),
        "first_level_marks": str(args.first_marks),
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
