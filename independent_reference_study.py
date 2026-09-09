#!/usr/bin/env python3
"""Run the independent finite-volume / DG / MC triangulation study."""

from __future__ import annotations

import argparse
from pathlib import Path

from lorenz_fpe.core import write_json
from lorenz_fpe.validation import independent_reference_and_mc_density_study


parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, default=Path("independent_reference_report.json"))
parser.add_argument("--particles", type=int, default=200000)
parser.add_argument("--bootstrap", type=int, default=200)
parser.add_argument("--base-cells", nargs=3, type=int, default=(30, 36, 36))
parser.add_argument("--factors", nargs="+", type=int, default=(1, 2))
args = parser.parse_args()

report = independent_reference_and_mc_density_study(
    base_cells=tuple(args.base_cells), factors=tuple(args.factors),
    n_particles=args.particles, bootstrap_replicates=args.bootstrap,
)
write_json(args.output, report)
