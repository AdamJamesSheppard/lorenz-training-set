#!/usr/bin/env python3
"""Offline local-positivity isolation study for a saved Q2 state."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
from mpi4py import MPI

from lorenz_fpe import Domain, FokkerPlanckSolver, Lorenz63Model
from lorenz_fpe.core import DensityState, write_json
from lorenz_fpe.local_projection import LocalPolynomialProjector
from lorenz_fpe.validation import covariance_accuracy


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _marginal_tv(
    cell_averages: np.ndarray, particles: np.ndarray, domain: Domain
) -> list[float]:
    probability = cell_averages * domain.volume / np.prod(domain.cells)
    result = []
    for axis, ((lo, hi), count) in enumerate(zip(domain.bounds, domain.cells)):
        other = tuple(index for index in range(3) if index != axis)
        numerical = probability.sum(axis=other)
        sampled = np.histogram(
            particles[:, axis], bins=count, range=(lo, hi)
        )[0] / len(particles)
        result.append(float(0.5 * np.abs(numerical - sampled).sum()))
    return result


def _difference_report(
    solver: FokkerPlanckSolver, raw: DensityState, candidate: DensityState
) -> dict[str, object]:
    l1, l2 = solver.limiter._difference_norms(
        raw.function.x.array, candidate.function.x.array
    )
    raw_diagnostics = solver.diagnostics(raw)
    candidate_diagnostics = solver.diagnostics(candidate)
    raw_mean = np.asarray(raw_diagnostics["mean"])
    candidate_mean = np.asarray(candidate_diagnostics["mean"])
    raw_covariance = np.asarray(raw_diagnostics["covariance"])
    candidate_covariance = np.asarray(candidate_diagnostics["covariance"])
    return {
        "l1": l1,
        "l2": l2,
        "mean_change_l2": float(np.linalg.norm(candidate_mean - raw_mean)),
        "covariance_change_frobenius": float(
            np.linalg.norm(candidate_covariance - raw_covariance)
        ),
    }


def run(args: argparse.Namespace) -> None:
    comm = MPI.COMM_WORLD
    output = args.output.resolve()
    if comm.rank == 0:
        output.mkdir(parents=True, exist_ok=False)
    comm.barrier()

    domain = Domain(cells=tuple(args.cells))
    solver = FokkerPlanckSolver(
        Lorenz63Model(),
        domain,
        args.dt,
        theta=0.5,
        degree=2,
        certificate_mode="adaptive",
        certificate_max_depth=args.certificate_max_depth,
        certificate_diagnostics=True,
        apply_positivity=False,
    )
    source_subcells = np.load(args.input_subcells)
    raw = solver.from_structured(
        source_subcells, time_value=args.final_time, apply_limiter=False
    )
    reconstructed = solver.structured_export(raw, 3)
    if comm.rank == 0:
        reconstruction_error = float(np.max(np.abs(reconstructed - source_subcells)))
    else:
        reconstruction_error = None

    scaled = raw.copy("current_adaptive_global_scaling")
    scaling_report = solver.limiter.apply(scaled)

    projector = LocalPolynomialProjector(
        solver.limiter,
        optimizer_ftol=args.optimizer_ftol,
        feasibility_tolerance=args.feasibility_tolerance,
        normalized_positivity_margin=args.normalized_positivity_margin,
        maximum_iterations=args.maximum_iterations,
    )
    local_only, local_only_report = projector.project_state(
        raw, repair_cell_averages=False, adaptive_skip=True
    )
    repaired_local, repaired_local_report = projector.project_state(
        raw, repair_cell_averages=True, adaptive_skip=True
    )

    branches = {
        "raw_unlimited": (raw, None),
        "current_adaptive_global_scaling": (scaled, asdict(scaling_report)),
        "local_qp_positive_average_cells_only": (local_only, local_only_report),
        "global_average_repair_then_local_qp": (repaired_local, repaired_local_report),
    }
    diagnostics = {name: solver.diagnostics(state) for name, (state, _) in branches.items()}
    differences = {
        name: _difference_report(solver, raw, state)
        for name, (state, _) in branches.items()
        if name != "raw_unlimited"
    }
    cell_averages = {
        name: solver.structured_export(state, 1)
        for name, (state, _) in branches.items()
    }
    subcell_averages = {
        name: solver.structured_export(state, 3)
        for name, (state, _) in branches.items()
    }

    if comm.rank == 0:
        particles = np.load(args.mc_particles)
        comparisons = {
            name: {
                "covariance_accuracy": covariance_accuracy(
                    np.asarray(diagnostics[name]["covariance"]),
                    particles,
                    args.seed,
                    args.bootstrap,
                ),
                "marginal_total_variation_distance": _marginal_tv(
                    cell_averages[name], particles, domain
                ),
            }
            for name in branches
        }
        artifacts = {}
        for name, values in subcell_averages.items():
            path = output / f"{name}_q2_subcell_averages.npy"
            np.save(path, values)
            artifacts[path.name] = {
                "sha256": _sha256(path),
                "bytes": path.stat().st_size,
            }
        report = {
            "evidence_class": "NUMERICAL_DIAGNOSTIC",
            "configuration": {
                "cells": list(args.cells),
                "degree": 2,
                "theta": 0.5,
                "dt": args.dt,
                "final_time": args.final_time,
                "mpi_ranks": comm.size,
                "certificate_mode": "adaptive_skip_then_fixed_2x2x2_constraints",
                "certificate_max_depth": args.certificate_max_depth,
                "optimizer": "SciPy SLSQP",
                "optimizer_ftol": args.optimizer_ftol,
                "feasibility_tolerance": args.feasibility_tolerance,
                "normalized_positivity_margin": args.normalized_positivity_margin,
                "maximum_iterations": args.maximum_iterations,
                "bootstrap_replicates": args.bootstrap,
                "seed": args.seed,
            },
            "source": {
                "q2_subcell_averages": str(args.input_subcells.resolve()),
                "q2_subcell_averages_sha256": _sha256(args.input_subcells),
                "mc_particles": str(args.mc_particles.resolve()),
                "mc_particles_sha256": _sha256(args.mc_particles),
                "maximum_q2_reconstruction_error": reconstruction_error,
            },
            "mathematical_scope": {
                "objective": "cell-local physical L2 distance induced by the DG mass matrix",
                "constraints": "fixed control-subcell Bernstein coefficients non-negative and original cell average preserved",
                "adaptive_use": "raw cells already certified non-negative are unchanged",
                "negative_cell_average_policy": "reported infeasible and retained in the pure-local branch",
                "claim_limit": "offline terminal-state projection; corrections do not feed the trajectory",
            },
            "diagnostics": diagnostics,
            "comparisons_to_common_mc": comparisons,
            "corrections_from_raw": differences,
            "correction_reports": {
                name: correction for name, (_, correction) in branches.items()
                if correction is not None
            },
            "artifacts": artifacts,
        }
        write_json(output / "report.json", report)
        print(output / "report.json", flush=True)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--input-subcells", type=Path, required=True)
    result.add_argument("--mc-particles", type=Path, required=True)
    result.add_argument("--output", type=Path, required=True)
    result.add_argument("--cells", type=int, nargs=3, default=(30, 36, 36))
    result.add_argument("--dt", type=float, required=True)
    result.add_argument("--final-time", type=float, default=0.05)
    result.add_argument("--certificate-max-depth", type=int, default=4)
    result.add_argument("--optimizer-ftol", type=float, default=1.0e-12)
    result.add_argument("--feasibility-tolerance", type=float, default=5.0e-11)
    result.add_argument("--normalized-positivity-margin", type=float, default=1.0e-12)
    result.add_argument("--maximum-iterations", type=int, default=250)
    result.add_argument("--bootstrap", type=int, default=200)
    result.add_argument("--seed", type=int, default=20260910)
    return result


if __name__ == "__main__":
    run(parser().parse_args())
