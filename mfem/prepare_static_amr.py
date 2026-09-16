#!/usr/bin/env python3
"""Freeze replay-driven marks and Gaussian parameters for one static AMR run."""

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
    parser.add_argument("mixture", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    source = np.load(args.indicator)
    edges = json.loads(args.axes.read_text())["edge_indices"]
    if source.shape != tuple(len(edges[axis]) - 1 for axis in "xyz"):
        raise ValueError("indicator and source axes differ")
    base_shape = (45, 54, 54)
    common_shape = (180, 216, 216)
    source_to_base = []
    for axis, count in zip("xyz", base_shape):
        e = np.asarray(edges[axis], dtype=np.float64)
        midpoints = 0.5 * (e[:-1] + e[1:])
        source_to_base.append(np.minimum(count - 1, (midpoints / 4).astype(int)))
    ix, iy, iz = np.meshgrid(*source_to_base, indexing="ij")
    energy = np.zeros(base_shape, dtype=np.float64)
    np.add.at(energy, (ix, iy, iz), source * source)
    flat = energy.ravel()
    descending = np.argsort(flat)[::-1]
    coverage = 0.99
    raw_count = int(np.searchsorted(np.cumsum(flat[descending]), coverage * flat.sum()) + 1)
    raw_marks = np.zeros(flat.size, dtype=bool)
    raw_marks[descending[:raw_count]] = True
    marks = binary_dilation(raw_marks.reshape(base_shape), iterations=1)
    estimated_cells = int(np.prod(base_shape) + 7 * marks.sum())
    if estimated_cells >= 220_864:
        raise ValueError("AMR marks do not retain a cell-count advantage over g_f")
    marks.astype(np.uint8).tofile(args.output / "base_cell_marks.bin")

    mixture = json.loads(args.mixture.read_text())
    parameters = []
    for weight, mean, covariance in zip(
        mixture["weights"], mixture["means"], mixture["covariances"]
    ):
        matrix = np.asarray(covariance, dtype=np.float64)
        precision = np.linalg.inv(matrix)
        amplitude = float(weight / np.sqrt((2 * np.pi) ** 3 * np.linalg.det(matrix)))
        parameters.extend([amplitude, *mean, *precision.ravel()])
    np.asarray(parameters, dtype=np.float64).tofile(args.output / "mixture_parameters.bin")
    (args.output / "design.json").write_text(json.dumps({
        "base_shape": base_shape,
        "common_shape": common_shape,
        "source_shape": source.shape,
        "indicator_energy_coverage": coverage,
        "raw_marked_cells": raw_count,
        "buffered_marked_cells": int(marks.sum()),
        "estimated_amr_cells": estimated_cells,
        "estimated_dg_dofs": 27 * estimated_cells,
        "fine_graded_cells": 220_864,
        "source_indicator": str(args.indicator),
        "source_axes": str(args.axes),
        "source_mixture": str(args.mixture),
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
