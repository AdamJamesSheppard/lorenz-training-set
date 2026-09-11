#!/usr/bin/env python3
"""Validate the fixed-matrix OSQP cell solver against the SLSQP oracle."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np

from lorenz_fpe import Domain, FokkerPlanckSolver, Lorenz63Model
from lorenz_fpe.local_projection import LocalPolynomialProjector


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _terminal_problems(
    solver: FokkerPlanckSolver, projector: LocalPolynomialProjector, path: Path
) -> list[np.ndarray]:
    state = solver.from_structured(np.load(path), apply_limiter=False)
    limiter = solver.limiter
    coefficients = state.function.x.array.copy()
    averages = np.array([
        limiter.cell_average(coefficients[dofs]) for dofs in limiter.cell_dofs
    ])
    targets = limiter.project_cell_averages(averages, limiter.cell_volumes)
    for cell, dofs in enumerate(limiter.cell_dofs):
        coefficients[dofs] += targets[cell] - averages[cell]
    problems = []
    for cell, dofs in enumerate(limiter.cell_dofs):
        if targets[cell] <= 0.0:
            continue
        values = coefficients[dofs]
        if limiter.classify_coefficients(values)["status"] != "CERTIFIED_NONNEGATIVE":
            problems.append(values.copy() / targets[cell])
    return problems


def _random_problems(
    projector: LocalPolynomialProjector, count: int, seed: int
) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    problems = []
    while len(problems) < count:
        raw = np.ones(27) + rng.normal(size=27) * rng.uniform(0.1, 5.0)
        raw += (1.0 - projector.average_weights @ raw) * np.ones(27)
        if float((projector.full_constraints @ raw).min()) < 0.0:
            problems.append(raw)
    return problems


def run(args: argparse.Namespace) -> None:
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    solver = FokkerPlanckSolver(
        Lorenz63Model(), Domain(cells=tuple(args.cells)), args.dt,
        theta=0.5, degree=2, certificate_mode="adaptive",
        certificate_max_depth=args.certificate_max_depth, apply_positivity=False,
    )
    specialized = LocalPolynomialProjector(
        solver.limiter, optimizer_backend="osqp",
        optimizer_ftol=args.optimizer_ftol,
        feasibility_tolerance=args.feasibility_tolerance,
        maximum_iterations=args.osqp_maximum_iterations,
    )
    oracle = LocalPolynomialProjector(
        solver.limiter, optimizer_backend="slsqp",
        optimizer_ftol=args.oracle_ftol,
        feasibility_tolerance=args.feasibility_tolerance,
        maximum_iterations=args.oracle_maximum_iterations,
    )

    distributions: dict[str, list[np.ndarray]] = {}
    for path in args.input_subcells:
        distributions[path.parent.name] = _terminal_problems(solver, specialized, path)
    distributions["random_stress"] = _random_problems(
        specialized, args.random_problems, args.seed
    )
    problems = [problem for values in distributions.values() for problem in values]

    started = time.perf_counter()
    specialized_results = [specialized.project_cell(problem) for problem in problems]
    specialized_seconds = time.perf_counter() - started
    started = time.perf_counter()
    oracle_results = [oracle.project_cell(problem) for problem in problems]
    oracle_seconds = time.perf_counter() - started

    oracle_success = np.array([item.status == "PROJECTED" for item in oracle_results])
    objective_relative_differences = []
    coefficient_maximum_differences = []
    for fast, reference in zip(specialized_results, oracle_results):
        if reference.status != "PROJECTED":
            continue
        objective_relative_differences.append(
            abs(fast.objective - reference.objective) / max(1.0, reference.objective)
        )
        coefficient_maximum_differences.append(
            float(np.max(np.abs(fast.coefficients - reference.coefficients)))
        )

    maximum_feasibility_violation = max(
        max(0.0, -item.minimum_constraint) for item in specialized_results
    )
    maximum_average_error = max(abs(item.average_error) for item in specialized_results)
    objective_bound_violations = sum(
        item.objective > item.scaling_objective
        + 1.0e-8 * max(1.0, item.scaling_objective)
        for item in specialized_results
    )
    speedup = oracle_seconds / specialized_seconds
    gates = {
        "all_specialized_problems_solved": all(
            item.status == "PROJECTED" for item in specialized_results
        ),
        "feasibility_at_most_tolerance": (
            maximum_feasibility_violation <= args.feasibility_tolerance
        ),
        "cell_average_error_at_most_tolerance": (
            maximum_average_error <= args.feasibility_tolerance
        ),
        "objective_never_exceeds_scalar_scaling_bound": objective_bound_violations == 0,
        "objective_agrees_with_successful_oracle": (
            max(objective_relative_differences, default=0.0)
            <= args.objective_agreement_tolerance
        ),
        "coefficients_agree_with_successful_oracle": (
            max(coefficient_maximum_differences, default=0.0)
            <= args.coefficient_agreement_tolerance
        ),
        "speedup_at_least_target": speedup >= args.minimum_speedup,
    }
    report = {
        "evidence_class": "EMPIRICAL_OPTIMIZER_VALIDATION",
        "configuration": {
            "cells": list(args.cells),
            "dt": args.dt,
            "certificate_max_depth": args.certificate_max_depth,
            "optimizer_ftol": args.optimizer_ftol,
            "oracle_ftol": args.oracle_ftol,
            "feasibility_tolerance": args.feasibility_tolerance,
            "osqp_maximum_iterations": args.osqp_maximum_iterations,
            "oracle_maximum_iterations": args.oracle_maximum_iterations,
            "random_problems": args.random_problems,
            "seed": args.seed,
        },
        "problem_counts": {
            **{name: len(values) for name, values in distributions.items()},
            "total": len(problems),
        },
        "source_sha256": {str(path.resolve()): _sha256(path) for path in args.input_subcells},
        "specialized": {
            "backend": "OSQP with reduced equality and reused factorization",
            "seconds": specialized_seconds,
            "statuses": {
                status: sum(item.status == status for item in specialized_results)
                for status in sorted({item.status for item in specialized_results})
            },
            "iterations_mean": float(np.mean([item.iterations for item in specialized_results])),
            "iterations_maximum": int(max(item.iterations for item in specialized_results)),
            "maximum_feasibility_violation": maximum_feasibility_violation,
            "maximum_cell_average_error": maximum_average_error,
            "objective_bound_violations": objective_bound_violations,
        },
        "oracle": {
            "backend": "SciPy SLSQP",
            "seconds": oracle_seconds,
            "successful": int(oracle_success.sum()),
            "failed": int((~oracle_success).sum()),
        },
        "comparison_on_successful_oracle_problems": {
            "count": int(oracle_success.sum()),
            "maximum_relative_objective_difference": max(
                objective_relative_differences, default=0.0
            ),
            "maximum_absolute_coefficient_difference": max(
                coefficient_maximum_differences, default=0.0
            ),
            "speedup": speedup,
        },
        "gates": gates,
        "all_gates_passed": all(gates.values()),
        "claim_limit": (
            "Cell-QP solver equivalence and speed on saved terminal and randomized problems; "
            "this does not establish dynamic PDE accuracy."
        ),
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(output / "report.json", flush=True)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--input-subcells", type=Path, nargs="+", required=True)
    result.add_argument("--output", type=Path, required=True)
    result.add_argument("--cells", type=int, nargs=3, default=(30, 36, 36))
    result.add_argument("--dt", type=float, default=0.000625)
    result.add_argument("--certificate-max-depth", type=int, default=4)
    result.add_argument("--optimizer-ftol", type=float, default=1.0e-10)
    result.add_argument("--oracle-ftol", type=float, default=1.0e-12)
    result.add_argument("--feasibility-tolerance", type=float, default=5.0e-11)
    result.add_argument("--osqp-maximum-iterations", type=int, default=10_000)
    result.add_argument("--oracle-maximum-iterations", type=int, default=250)
    result.add_argument("--random-problems", type=int, default=1000)
    result.add_argument("--seed", type=int, default=20260911)
    result.add_argument("--objective-agreement-tolerance", type=float, default=5.0e-7)
    result.add_argument("--coefficient-agreement-tolerance", type=float, default=1.0e-3)
    result.add_argument("--minimum-speedup", type=float, default=10.0)
    return result


if __name__ == "__main__":
    run(parser().parse_args())
