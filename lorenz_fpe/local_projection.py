"""Cell-local minimum-change positivity projection for DG tensor polynomials.

This module is an experimental diagnostic.  It does not alter time stepping.
For a cell with non-negative average it computes the mass-matrix projection
onto a fixed convex set of non-negative Bernstein coefficients while preserving
that cell average.  A negative cell average is reported as infeasible because
no non-negative polynomial can have negative integral on the cell.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass

import numpy as np
from mpi4py import MPI
from scipy.optimize import LinearConstraint, minimize

from .core import (
    DensityState,
    FokkerPlanckSolver,
    PositivityLimiter,
    _global_max,
    _global_min,
    _global_sum,
)


@dataclass(frozen=True)
class CellProjectionResult:
    coefficients: np.ndarray
    status: str
    iterations: int
    objective: float
    scaling_objective: float
    minimum_constraint: float
    average_error: float
    optimizer_message: str | None = None


class LocalPolynomialProjector:
    """Mass-matrix projection onto cell-local Bernstein positivity constraints.

    The fixed ``2 x 2 x 2`` Q2 control-subcell Bernstein inequalities are used
    as the convex QP constraints.  Adaptive Bernstein subdivision may skip a
    cell already certified non-negative, but it is not changed while the QP is
    being solved.  This keeps every solved problem convex and auditable.
    """

    def __init__(
        self,
        limiter: PositivityLimiter,
        *,
        optimizer_ftol: float = 1.0e-10,
        feasibility_tolerance: float = 5.0e-11,
        normalized_positivity_margin: float = 1.0e-12,
        maximum_iterations: int = 250,
    ) -> None:
        if limiter.lower != 0.0:
            raise NotImplementedError("The experimental local projection currently requires lower=0")
        self.limiter = limiter
        self.optimizer_ftol = float(optimizer_ftol)
        self.feasibility_tolerance = float(feasibility_tolerance)
        self.normalized_positivity_margin = float(normalized_positivity_margin)
        if not (0.0 <= self.normalized_positivity_margin < 1.0):
            raise ValueError("normalized_positivity_margin must lie in [0,1)")
        self.maximum_iterations = int(maximum_iterations)
        basis = limiter._quadrature_basis
        weights = limiter._quadrature_weights
        self.mass_matrix = basis.T @ (weights[:, None] * basis)
        self.average_weights = limiter.average_weights.copy()
        self.ones = np.ones(self.mass_matrix.shape[0])
        if not np.allclose(self.average_weights @ self.ones, 1.0, atol=2.0e-14):
            raise RuntimeError("Local basis does not represent the constant polynomial exactly")
        full = np.asarray(limiter.to_bernstein, dtype=float)
        # Subcell faces share mathematically identical Bernstein functionals.
        # Deduplicate them for the optimizer, then verify against every original
        # row before accepting a result.
        _, indices = np.unique(np.round(full, decimals=14), axis=0, return_index=True)
        self.constraints = full[np.sort(indices)]
        self.full_constraints = full
        self.linear_constraints = (
            LinearConstraint(
                self.constraints, self.normalized_positivity_margin, np.inf
            ),
            LinearConstraint(self.average_weights[None, :], 1.0, 1.0),
        )
        self._warm_starts: list[np.ndarray | None] = [
            None for _ in range(limiter.n_local_cells)
        ]

    def _objective(self, candidate: np.ndarray, raw: np.ndarray) -> float:
        difference = candidate - raw
        return 0.5 * float(difference @ self.mass_matrix @ difference)

    def _scaling_candidate(self, normalized: np.ndarray) -> np.ndarray:
        minimum = float((self.full_constraints @ normalized).min())
        margin = self.normalized_positivity_margin
        if minimum >= margin:
            return normalized.copy()
        theta = float(np.clip((1.0 - margin) / (1.0 - minimum), 0.0, 1.0))
        return self.ones + theta * (normalized - self.ones)

    def project_cell(
        self,
        coefficients: np.ndarray,
        *,
        prescribed_average: float | None = None,
        initial_guess: np.ndarray | None = None,
    ) -> CellProjectionResult:
        """Project one polynomial or return an explicit infeasibility result."""
        raw = np.asarray(coefficients, dtype=float)
        if raw.shape != self.ones.shape:
            raise ValueError(f"Expected {len(self.ones)} cell coefficients, got {raw.shape}")
        average = (
            float(self.average_weights @ raw)
            if prescribed_average is None else float(prescribed_average)
        )
        if average < 0.0:
            return CellProjectionResult(
                raw.copy(), "NEGATIVE_CELL_AVERAGE", 0, 0.0, 0.0,
                float((self.full_constraints @ raw).min()), 0.0,
            )
        if average == 0.0:
            zero = np.zeros_like(raw)
            return CellProjectionResult(
                zero, "PROJECTED_ZERO_AVERAGE", 0,
                self._objective(zero, raw), self._objective(zero, raw),
                0.0, 0.0,
            )

        # Homogeneous normalization avoids poor conditioning in low-density
        # tail cells.  The normalized polynomial has cell average one.
        normalized = raw / average
        raw_minimum = float((self.full_constraints @ normalized).min())
        if raw_minimum >= self.normalized_positivity_margin:
            return CellProjectionResult(
                raw.copy(), "ALREADY_FEASIBLE", 0, 0.0, 0.0,
                average * raw_minimum, 0.0,
            )
        scaling = self._scaling_candidate(normalized)
        optimizer_start = scaling
        if initial_guess is not None:
            warm = np.asarray(initial_guess, dtype=float)
            warm_feasible = (
                warm.shape == normalized.shape
                and abs(float(self.average_weights @ warm) - 1.0)
                    <= self.feasibility_tolerance
                and float((self.full_constraints @ warm).min())
                    >= self.normalized_positivity_margin - self.feasibility_tolerance
            )
            if warm_feasible and self._objective(warm, normalized) < self._objective(
                scaling, normalized
            ):
                optimizer_start = warm

        result = minimize(
            lambda value: self._objective(value, normalized),
            optimizer_start,
            jac=lambda value: self.mass_matrix @ (value - normalized),
            constraints=self.linear_constraints,
            method="SLSQP",
            options={
                "ftol": self.optimizer_ftol,
                "maxiter": self.maximum_iterations,
                "disp": False,
            },
        )
        candidate = np.asarray(result.x, dtype=float)

        # Remove the equality residual in the constant direction.  If this
        # creates a tiny negative Bernstein residual, contract by the minimum
        # amount toward the unit-average constant polynomial.
        candidate += (1.0 - float(self.average_weights @ candidate)) * self.ones
        minimum = float((self.full_constraints @ candidate).min())
        if minimum < self.normalized_positivity_margin:
            theta = float(np.clip(
                (1.0 - self.normalized_positivity_margin) / (1.0 - minimum),
                0.0,
                1.0,
            ))
            candidate = self.ones + theta * (candidate - self.ones)
        minimum = float((self.full_constraints @ candidate).min())
        average_error = float(self.average_weights @ candidate - 1.0)
        objective = self._objective(candidate, normalized)
        scaling_objective = self._objective(scaling, normalized)
        feasible = minimum >= -self.feasibility_tolerance and abs(average_error) <= self.feasibility_tolerance
        optimal_enough = objective <= scaling_objective + 1.0e-8 * max(1.0, scaling_objective)
        status = "PROJECTED" if result.success and feasible and optimal_enough else "OPTIMIZER_FAILED"
        final = average * candidate if status == "PROJECTED" else raw.copy()
        return CellProjectionResult(
            final,
            status,
            int(result.nit),
            average * average * objective,
            average * average * scaling_objective,
            average * minimum if status == "PROJECTED" else float((self.full_constraints @ raw).min()),
            average * average_error if status == "PROJECTED" else 0.0,
            None if status == "PROJECTED" else str(result.message),
        )

    def scaling_fallback(
        self, coefficients: np.ndarray, *, prescribed_average: float | None = None
    ) -> np.ndarray:
        """Return the feasible scalar-scaling comparator for a positive average."""
        raw = np.asarray(coefficients, dtype=float)
        average = (
            float(self.average_weights @ raw)
            if prescribed_average is None else float(prescribed_average)
        )
        if average < 0.0:
            raise ValueError("Scalar fallback is infeasible for a negative cell average")
        if average == 0.0:
            return np.zeros_like(raw)
        return average * self._scaling_candidate(raw / average)

    def project_state(
        self,
        state: DensityState,
        *,
        repair_cell_averages: bool,
        adaptive_skip: bool = True,
    ) -> tuple[DensityState, dict[str, object]]:
        """Apply the diagnostic independently to every owned cell.

        With ``repair_cell_averages=False``, negative-average cells are retained
        unchanged and explicitly counted.  With it enabled, the incumbent
        global conservative average projection runs first, isolating the effect
        of replacing only completed-polynomial scaling by the local QP.
        """
        started = time.perf_counter()
        limiter = self.limiter
        output = state.copy("local_minimum_change_projection")
        coefficients = output.function.x.array
        raw_coefficients = coefficients.copy()
        local_averages = np.array([
            limiter.cell_average(coefficients[dofs]) for dofs in limiter.cell_dofs
        ])
        raw_negative_average_cells = int(np.count_nonzero(local_averages < 0.0))
        raw_negative_average_mass = float(np.dot(
            limiter.cell_volumes, np.maximum(-local_averages, 0.0)
        ))

        if repair_cell_averages:
            gathered_averages = limiter.comm.gather(local_averages, root=0)
            gathered_volumes = limiter.comm.gather(limiter.cell_volumes, root=0)
            if limiter.comm.rank == 0:
                all_averages = np.concatenate(gathered_averages)
                all_volumes = np.concatenate(gathered_volumes)
                repaired = limiter.project_cell_averages(all_averages, all_volumes)
                chunks = []
                offset = 0
                for values in gathered_averages:
                    chunks.append(repaired[offset:offset + len(values)])
                    offset += len(values)
            else:
                chunks = None
            target_averages = limiter.comm.scatter(chunks, root=0)
            for cell, dofs in enumerate(limiter.cell_dofs):
                coefficients[dofs] += float(target_averages[cell] - local_averages[cell])
        output.function.x.scatter_forward()
        after_average_repair = coefficients.copy()

        counts = {
            "ALREADY_CERTIFIED": 0,
            "ALREADY_FEASIBLE": 0,
            "PROJECTED": 0,
            "PROJECTED_ZERO_AVERAGE": 0,
            "NEGATIVE_CELL_AVERAGE": 0,
            "OPTIMIZER_FAILED": 0,
        }
        iterations: list[int] = []
        objective = 0.0
        scaling_objective = 0.0
        objective_bound_violations = 0
        scaling_fallback_cells = 0
        optimizer_messages: dict[str, int] = {}

        for cell, dofs in enumerate(limiter.cell_dofs):
            values = coefficients[dofs].copy()
            if adaptive_skip:
                classification = limiter.classify_coefficients(values)
                if classification["status"] == "CERTIFIED_NONNEGATIVE":
                    counts["ALREADY_CERTIFIED"] += 1
                    self._warm_starts[cell] = None
                    continue
            prescribed_average = (
                float(target_averages[cell]) if repair_cell_averages else None
            )
            result = self.project_cell(
                values,
                prescribed_average=prescribed_average,
                initial_guess=self._warm_starts[cell],
            )
            counts[result.status] += 1
            if result.status in {"PROJECTED", "PROJECTED_ZERO_AVERAGE"}:
                coefficients[dofs] = result.coefficients
                average = (
                    prescribed_average if prescribed_average is not None
                    else limiter.cell_average(result.coefficients)
                )
                self._warm_starts[cell] = (
                    result.coefficients / average if average > 0.0 else None
                )
                iterations.append(result.iterations)
                volume = float(limiter.cell_volumes[cell])
                objective += volume * result.objective
                scaling_objective += volume * result.scaling_objective
                if result.objective > result.scaling_objective + 1.0e-8 * max(1.0, result.scaling_objective):
                    objective_bound_violations += 1
            elif result.optimizer_message is not None:
                optimizer_messages[result.optimizer_message] = optimizer_messages.get(result.optimizer_message, 0) + 1
                fallback = self.scaling_fallback(
                    values, prescribed_average=prescribed_average
                )
                coefficients[dofs] = fallback
                average = (
                    prescribed_average if prescribed_average is not None
                    else limiter.cell_average(fallback)
                )
                self._warm_starts[cell] = fallback / average if average > 0.0 else None
            elif result.status == "ALREADY_FEASIBLE":
                average = (
                    prescribed_average if prescribed_average is not None
                    else limiter.cell_average(values)
                )
                self._warm_starts[cell] = values / average if average > 0.0 else None
            else:
                self._warm_starts[cell] = None
                scaling_fallback_cells += 1
        output.function.x.scatter_forward()

        final_coefficients = coefficients.copy()
        stage1_l1, stage1_l2 = limiter._difference_norms(raw_coefficients, after_average_repair)
        local_l1, local_l2 = limiter._difference_norms(after_average_repair, final_coefficients)
        total_l1, total_l2 = limiter._difference_norms(raw_coefficients, final_coefficients)
        final_classification = limiter._classification_summary(final_coefficients)
        global_counts = {
            key: int(limiter.comm.allreduce(value, op=MPI.SUM))
            for key, value in counts.items()
        }
        global_raw_negative_cells = int(limiter.comm.allreduce(raw_negative_average_cells, op=MPI.SUM))
        total_cells = int(limiter.comm.allreduce(limiter.n_local_cells, op=MPI.SUM))
        report: dict[str, object] = {
            "method": "cell-local mass-matrix QP with fixed control-subcell Bernstein constraints",
            "average_repair": "global conservative L2 projection" if repair_cell_averages else "disabled",
            "adaptive_certified_cells_skipped": bool(adaptive_skip),
            "total_cells": total_cells,
            "counts": global_counts,
            "raw_negative_cell_average_cells": global_raw_negative_cells,
            "raw_negative_cell_average_mass": _global_sum(limiter.comm, raw_negative_average_mass),
            "minimum_raw_cell_average": _global_min(limiter.comm, float(local_averages.min())),
            "mass_before": _global_sum(limiter.comm, float(np.dot(limiter.cell_volumes, local_averages))),
            "mass_after": _global_sum(limiter.comm, float(sum(
                limiter.cell_volumes[cell] * limiter.cell_average(coefficients[dofs])
                for cell, dofs in enumerate(limiter.cell_dofs)
            ))),
            "stage1_l1_correction": stage1_l1,
            "stage1_l2_correction": stage1_l2,
            "local_qp_l1_correction": local_l1,
            "local_qp_l2_correction": local_l2,
            "raw_to_final_l1_correction": total_l1,
            "raw_to_final_l2_correction": total_l2,
            "relative_l1_correction": total_l1 / max(
                abs(_global_sum(limiter.comm, float(np.dot(limiter.cell_volumes, local_averages)))),
                np.finfo(float).tiny,
            ),
            "mass_matrix_objective": _global_sum(limiter.comm, objective),
            "matched_scalar_scaling_objective": _global_sum(limiter.comm, scaling_objective),
            "objective_bound_violations": int(limiter.comm.allreduce(objective_bound_violations, op=MPI.SUM)),
            "scaling_fallback_cells": int(limiter.comm.allreduce(scaling_fallback_cells, op=MPI.SUM)),
            "optimizer_iterations_mean": float(
                _global_sum(limiter.comm, float(sum(iterations))) /
                max(1, limiter.comm.allreduce(len(iterations), op=MPI.SUM))
            ),
            "optimizer_iterations_maximum": int(limiter.comm.allreduce(max(iterations, default=0), op=MPI.MAX)),
            "optimizer_messages_by_rank": limiter.comm.gather(optimizer_messages, root=0),
            "final_certificate_counts": final_classification["counts"],
            "final_certificate_lower_bound": final_classification["lower_bound"],
            "final_quadrature_negative_mass": final_classification["quadrature_negative_mass"],
            "whole_cell_positivity_certified": (
                final_classification["counts"]["CERTIFIED_NONNEGATIVE"] == total_cells
            ),
            "wall_seconds": _global_max(limiter.comm, time.perf_counter() - started),
        }
        if limiter.comm.rank != 0:
            report["optimizer_messages_by_rank"] = None
        return output, report


class LocalProjectionFokkerPlanckSolver(FokkerPlanckSolver):
    """Experimental Q2 solver feeding the average-repair/local-QP state forward."""

    def __init__(self, *args, **kwargs) -> None:
        local_optimizer_ftol = float(kwargs.pop("local_optimizer_ftol", 1.0e-10))
        local_maximum_iterations = int(kwargs.pop("local_maximum_iterations", 250))
        kwargs["apply_positivity"] = False
        super().__init__(*args, **kwargs)
        if self.degree != 2:
            raise ValueError("LocalProjectionFokkerPlanckSolver currently requires Q2")
        self.local_projector = LocalPolynomialProjector(
            self.limiter,
            optimizer_ftol=local_optimizer_ftol,
            maximum_iterations=local_maximum_iterations,
        )
        self.local_projection_history: list[dict[str, object]] = []
        self.last_local_projection_report: dict[str, object] | None = None
        self.last_unlimited_state: DensityState | None = None
        self.uses_local_projection = True

    def step(self, state: DensityState) -> DensityState:
        started = time.perf_counter()
        unlimited = super().step(state)
        self.last_unlimited_state = unlimited.copy("raw_unlimited")
        corrected, report = self.local_projector.project_state(
            unlimited, repair_cell_averages=True, adaptive_skip=True
        )
        report["step_time"] = corrected.time
        self.last_local_projection_report = report
        self.local_projection_history.append(report)
        self.limiter.last_raw_coefficients = unlimited.function.x.array.copy()
        self.limiter.last_stage1_coefficients = corrected.function.x.array.copy()
        self.limiter.last_final_coefficients = corrected.function.x.array.copy()
        self.last_timing["local_projection_seconds"] = float(report["wall_seconds"])
        self.last_timing["step_seconds"] = _global_max(
            self.comm, time.perf_counter() - started
        )
        return corrected

    def local_projection_history_summary(self) -> dict[str, object]:
        if not self.local_projection_history:
            return {"steps": 0}
        scalar_keys = (
            "relative_l1_correction",
            "raw_to_final_l2_correction",
            "stage1_l1_correction",
            "local_qp_l1_correction",
            "local_qp_l2_correction",
            "raw_negative_cell_average_mass",
            "scaling_fallback_cells",
            "wall_seconds",
        )
        result: dict[str, object] = {"steps": len(self.local_projection_history)}
        for key in scalar_keys:
            values = np.asarray([float(item[key]) for item in self.local_projection_history])
            result[key] = {
                "mean": float(values.mean()),
                "maximum": float(values.max()),
                "p95": float(np.quantile(values, 0.95)),
            }
        result["all_steps_whole_cell_positivity_certified"] = all(
            bool(item["whole_cell_positivity_certified"])
            for item in self.local_projection_history
        )
        result["maximum_objective_bound_violations"] = int(max(
            int(item["objective_bound_violations"])
            for item in self.local_projection_history
        ))
        return result
