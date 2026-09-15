#!/usr/bin/env python3
"""Export DOLFINx physical Q2 action/CN fields for the MFEM gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np
from mpi4py import MPI
from petsc4py import PETSc

from dolfinx import fem
from dolfinx.fem.petsc import assemble_matrix, assign, create_vector

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lorenz_fpe.core import DensityState, Domain, FokkerPlanckSolver, Lorenz63Model
from lorenz_fpe.local_projection import LocalPolynomialProjector


BOUNDS = ((-30.0, 30.0), (-40.0, 40.0), (-10.0, 70.0))
DT = 0.00015625
SUBCELLS = 3
TEST_COUNT = 4


def test_value(
    test: int, ix: int, iy: int, iz: int, r: float, s: float, t: float
) -> float:
    if test == 0:
        return (
            1.0
            + 0.07 * r
            - 0.04 * s
            + 0.03 * t
            + 0.02 * r * s
            - 0.015 * s * t
            + 0.01 * r * r
        )
    if test == 1:
        parity = 1.0 if (ix + iy + iz) % 2 == 0 else -1.0
        return (1.0 + 0.08 * parity) * (
            1.0 + 0.11 * r + 0.04 * s * s - 0.06 * t + 0.025 * r * t
        )
    if test == 2:
        cell_mode = (
            0.04 * np.sin(0.7 * (ix + 1))
            - 0.03 * np.cos(0.5 * (iy + 2))
            + 0.02 * ((iz % 3) - 1)
        )
        return (
            0.9
            + cell_mode
            + 0.06 * r * r
            - 0.05 * s
            + 0.035 * t * t
            + 0.02 * r * s * t
        )
    return 1.0 + 2.4 * (r - 0.5) + 0.8 * (s - 0.5) - 0.5 * (t - 0.5)


def populate_state(solver: FokkerPlanckSolver, test: int) -> DensityState:
    q = fem.Function(solver.V, name=f"test_state_{test}")
    coordinates = solver.V.tabulate_dof_coordinates()
    geometry = solver.mesh.geometry.x
    geometry_dofs = solver.mesh.geometry.dofmaps[0]
    counts = solver.domain.cells
    widths = np.array(
        [(hi - lo) / count for (lo, hi), count in zip(BOUNDS, counts)], dtype=float
    )
    cells = solver.mesh.topology.index_map(solver.mesh.topology.dim).size_local
    for cell in range(cells):
        vertex_coordinates = geometry[geometry_dofs[cell]]
        midpoint = vertex_coordinates.mean(axis=0)
        index = tuple(
            min(counts[axis] - 1, max(0, int(np.floor((midpoint[axis] - BOUNDS[axis][0]) / widths[axis]))))
            for axis in range(3)
        )
        origin = np.array([BOUNDS[axis][0] + index[axis] * widths[axis] for axis in range(3)])
        for dof in solver.V.dofmap.cell_dofs(cell):
            r, s, t = (coordinates[dof] - origin) / widths
            q.x.array[dof] = test_value(test, *index, r, s, t)
    q.x.scatter_forward()
    return DensityState(q, 0.0, f"test_state_{test}")


def relative_residual(matrix, solution, rhs) -> float:
    residual = rhs.duplicate()
    matrix.mult(solution, residual)
    residual.aypx(-1.0, rhs)
    return float(residual.norm()) / max(float(rhs.norm()), np.finfo(float).tiny)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("nx", type=int)
    parser.add_argument("ny", type=int)
    parser.add_argument("nz", type=int)
    parser.add_argument("output_directory", type=Path)
    args = parser.parse_args()
    comm = MPI.COMM_WORLD
    if comm.rank == 0:
        args.output_directory.mkdir(parents=True, exist_ok=True)
    comm.Barrier()

    diffusion = np.array(
        [[1.0, 0.4, 0.2], [0.4, 1.0, 0.3], [0.2, 0.3, 1.0]], dtype=float
    )
    noise = np.sqrt(2.0) * np.linalg.cholesky(diffusion)
    model = Lorenz63Model(B=tuple(tuple(float(x) for x in row) for row in noise))
    domain = Domain(bounds=BOUNDS, cells=(args.nx, args.ny, args.nz))
    solver = FokkerPlanckSolver(
        model,
        domain,
        dt=DT,
        theta=0.5,
        degree=2,
        penalty=16.0,
        ksp_rtol=1.0e-13,
        ksp_atol=1.0e-15,
        apply_positivity=False,
    )

    mass = assemble_matrix(solver.mass_bilinear_form)
    mass.assemble()
    spatial = assemble_matrix(solver.spatial_bilinear_form)
    spatial.assemble()
    extended_diagnostics = args.nx * args.ny * args.nz <= 1000
    component_matrices = {}
    if extended_diagnostics:
        for name, form in (
            ("advection", solver.advection_bilinear_form),
            ("advection_volume", solver.advection_volume_bilinear_form),
            ("advection_face", solver.advection_face_bilinear_form),
            ("diffusion", solver.diffusion_bilinear_form),
        ):
            component_matrices[name] = assemble_matrix(form)
            component_matrices[name].assemble()
    mass_solver = PETSc.KSP().create(comm)
    mass_solver.setOperators(mass)
    mass_solver.setType("cg")
    mass_solver.setTolerances(rtol=1.0e-14, atol=1.0e-16, max_it=500)
    mass_solver.setErrorIfNotConverged(True)
    mass_solver.getPC().setType("jacobi")
    mass_solver.setUp()
    local_projector = LocalPolynomialProjector(solver.limiter, optimizer_backend="osqp")

    action_residuals: list[float] = []
    cn_residuals: list[float] = []
    qp_reports: list[dict[str, object]] = []
    for test in range(TEST_COUNT):
        state = populate_state(solver, test)
        def physical_action(matrix, name: str):
            action = create_vector(solver.V)
            with action.localForm() as local:
                local.set(0.0)
            matrix.mult(state.function.x.petsc_vec, action)
            action.scale(-1.0)
            derivative_vector = create_vector(solver.V)
            with derivative_vector.localForm() as local:
                local.set(0.0)
            mass_solver.solve(action, derivative_vector)
            derivative_vector.ghostUpdate(
                addv=PETSc.InsertMode.INSERT, mode=PETSc.ScatterMode.FORWARD
            )
            derivative = fem.Function(solver.V, name=f"{name}_{test}")
            assign(derivative_vector, derivative)
            derivative.x.scatter_forward()
            return action, derivative_vector, derivative

        action, derivative_vector, derivative = physical_action(spatial, "action")
        action_residuals.append(relative_residual(mass, derivative_vector, action))

        next_state = solver.step(state)
        cn_residuals.append(float(solver.last_linear["true_relative_residual"]))
        corrected_state, qp_report = local_projector.project_state(
            next_state, repair_cell_averages=True, adaptive_skip=True
        )
        qp_reports.append(qp_report)
        exports: dict[str, np.ndarray] = {
            "state": solver.structured_export(state, SUBCELLS),
            "action": solver.structured_export(
                DensityState(derivative, 0.0, f"action_{test}"), SUBCELLS
            ),
            "cn": solver.structured_export(next_state, SUBCELLS),
            "qp": solver.structured_export(corrected_state, SUBCELLS),
        }
        for name, matrix in component_matrices.items():
            _, _, component_derivative = physical_action(matrix, name)
            exports[name] = solver.structured_export(
                DensityState(component_derivative, 0.0, f"{name}_{test}"), SUBCELLS
            )
        if comm.rank == 0:
            for name, values in exports.items():
                np.save(args.output_directory / f"{name}_{test}.npy", values)

    if comm.rank == 0:
        summary = {
            "mesh": [args.nx, args.ny, args.nz],
            "subcells_per_cell": SUBCELLS,
            "test_count": TEST_COUNT,
            "extended_component_diagnostics": extended_diagnostics,
            "global_q2_dofs": int(np.prod(domain.cells) * 27),
            "mass_inverse_relative_residuals": action_residuals,
            "cn_true_relative_residuals": cn_residuals,
            "qp_reports": qp_reports,
            "diffusion": diffusion.tolist(),
            "dt": DT,
            "penalty_parameter": 16.0,
        }
        (args.output_directory / "dolfinx_summary.json").write_text(
            json.dumps(summary, indent=2) + "\n"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
