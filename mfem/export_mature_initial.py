#!/usr/bin/env python3
"""Create one frozen, projected mature Q2 state for the MFEM trajectory gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np
from mpi4py import MPI

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lorenz_fpe import Domain, LocalProjectionFokkerPlanckSolver, Lorenz63Model


BOUNDS = ((-30.0, 30.0), (-40.0, 40.0), (-10.0, 70.0))
NOISE = np.array(
    [[1.4142135623730951, 0.0, 0.0],
     [0.5656854249492381, 1.2961481396815722, 0.0],
     [0.28284271247461906, 0.3394673699166024, 1.3434142714594956]],
    dtype=float,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mixture", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--cells", nargs=3, type=int, default=(30, 36, 36))
    args = parser.parse_args()
    comm = MPI.COMM_WORLD
    cells = tuple(args.cells)
    model = Lorenz63Model(B=tuple(tuple(float(v) for v in row) for row in NOISE))
    solver = LocalProjectionFokkerPlanckSolver(
        model, Domain(BOUNDS, cells), 0.00015625, theta=0.5, degree=2,
        ksp_rtol=1.0e-12, ksp_atol=1.0e-15,
        certificate_mode="fixed", certificate_max_depth=4,
        certificate_diagnostics=True, local_optimizer_backend="osqp",
        local_optimizer_ftol=1.0e-10, local_maximum_iterations=10_000,
    )
    payload = json.loads(args.mixture.read_text())
    expression = sum(
        float(weight) * solver.gaussian_expression(mean, np.asarray(covariance))
        for weight, mean, covariance in zip(
            payload["weights"], payload["means"], payload["covariances"]
        )
    )
    raw = solver.project_expression(
        expression, "shared_mature_mixture", quadrature_degree=14,
        normalize=True, apply_limiter=False,
    )
    state, report = solver.local_projector.project_state(
        raw, repair_cell_averages=True, adaptive_skip=True
    )

    shape = cells + (3, 3, 3)
    local = np.zeros(shape, dtype=np.float64)
    widths = np.array([(hi - lo) / n for (lo, hi), n in zip(BOUNDS, cells)])
    coordinates = solver.V.tabulate_dof_coordinates()
    geometry = solver.mesh.geometry.x
    geometry_dofs = solver.mesh.geometry.dofmaps[0]
    nlocal = solver.mesh.topology.index_map(solver.mesh.topology.dim).size_local
    for cell in range(nlocal):
        midpoint = geometry[geometry_dofs[cell]].mean(axis=0)
        index = tuple(
            min(cells[d] - 1, max(0, int(np.floor((midpoint[d] - BOUNDS[d][0]) / widths[d]))))
            for d in range(3)
        )
        origin = np.array([BOUNDS[d][0] + index[d] * widths[d] for d in range(3)])
        for dof in solver.V.dofmap.cell_dofs(cell):
            node = tuple(int(np.clip(np.rint(2.0 * (coordinates[dof] - origin) / widths), 0, 2)[d]) for d in range(3))
            local[index + node] = state.function.x.array[dof]
    global_values = np.zeros_like(local) if comm.rank == 0 else None
    comm.Reduce(local, global_values, op=MPI.SUM, root=0)
    common = solver.structured_export(state, 6)
    represented_mass = solver.mass(state)
    if comm.rank == 0:
        args.output.mkdir(parents=True, exist_ok=True)
        global_values.tofile(args.output / "initial_nodal_q2.bin")
        np.save(args.output / "initial_q2_subcell_averages.npy", common)
        (args.output / "initial_report.json").write_text(json.dumps({
            "mesh": list(cells), "mass": represented_mass,
            "projection": report,
        }, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
