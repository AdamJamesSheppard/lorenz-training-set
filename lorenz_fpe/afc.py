"""Experimental algebraic flux-corrected update for mature Q2 densities.

The high-order target remains the existing Q2 Crank--Nicolson DG update.  A
positive, conservative P0 graph update supplies cell-average bounds, and a
limited antisymmetric correction moves those averages toward the Q2 target.
The existing local QP is then used only to remove remaining within-cell
polynomial negativity while preserving the AFC cell averages.

This is an experiment-specific algebraic comparator, not a claim that the
complete-graph limiter below is identical to a published edge-local AFC
scheme.  Its purpose is to separate average-level update positivity from the
polynomial positivity correction with all other discretisation choices fixed.
"""

from __future__ import annotations

import time

import numpy as np
from mpi4py import MPI

from .core import DensityState, FokkerPlanckSolver, _global_max, _global_sum
from .local_projection import LocalPolynomialProjector


class AFCProjectionFokkerPlanckSolver(FokkerPlanckSolver):
    """Q2--CN target with a positive low-order/AFC cell-average update."""

    def __init__(self, *args, **kwargs) -> None:
        local_optimizer_ftol = float(kwargs.pop("local_optimizer_ftol", 1.0e-10))
        local_maximum_iterations = int(kwargs.pop("local_maximum_iterations", 10_000))
        local_optimizer_backend = str(kwargs.pop("local_optimizer_backend", "osqp"))
        kwargs["apply_positivity"] = False
        super().__init__(*args, **kwargs)
        if self.degree != 2:
            raise ValueError("AFCProjectionFokkerPlanckSolver currently requires Q2")
        self.local_projector = LocalPolynomialProjector(
            self.limiter,
            optimizer_ftol=local_optimizer_ftol,
            maximum_iterations=local_maximum_iterations,
            optimizer_backend=local_optimizer_backend,
        )
        self.local_projection_history: list[dict[str, object]] = []
        self.last_local_projection_report: dict[str, object] | None = None
        self.last_unlimited_state: DensityState | None = None
        self.uses_local_projection = True
        self.uses_afc_update = True
        self._prepare_structured_layout()
        self._prepare_low_order_operator()

    def _prepare_structured_layout(self) -> None:
        _, _, mids = self.cell_averages(DensityState(self.p_old, 0.0, "layout"))
        gathered = self.comm.gather(mids, root=0)
        if self.comm.rank == 0:
            chunks: list[np.ndarray] = []
            for points in gathered:
                flat = []
                for point in points:
                    index = []
                    for value, (lo, hi), count in zip(
                        point, self.domain.bounds, self.domain.cells
                    ):
                        cell = int(np.floor((value - lo) / (hi - lo) * count))
                        index.append(min(count - 1, max(0, cell)))
                    flat.append(np.ravel_multi_index(tuple(index), self.domain.cells))
                chunks.append(np.asarray(flat, dtype=np.int64))
            combined = np.concatenate(chunks)
            if len(np.unique(combined)) != int(np.prod(self.domain.cells)):
                raise RuntimeError("MPI cell ownership did not map bijectively to the Cartesian grid")
            self._flat_indices_by_rank = chunks
        else:
            self._flat_indices_by_rank = None

    @staticmethod
    def _paired_slices(shape: tuple[int, int, int], shift: tuple[int, int, int]):
        left = []
        right = []
        for count, offset in zip(shape, shift):
            if offset > 0:
                left.append(slice(0, count - offset))
                right.append(slice(offset, count))
            elif offset < 0:
                left.append(slice(-offset, count))
                right.append(slice(0, count + offset))
            else:
                left.append(slice(None))
                right.append(slice(None))
        return tuple(left), tuple(right)

    def _prepare_low_order_operator(self) -> None:
        if self.comm.rank != 0:
            self._low_order_data = None
            return
        shape = tuple(int(value) for value in self.domain.cells)
        spacing = np.asarray([
            (hi - lo) / count
            for (lo, hi), count in zip(self.domain.bounds, shape)
        ])
        centers = [
            np.linspace(lo + 0.5 * h, hi - 0.5 * h, count)
            for (lo, hi), count, h in zip(self.domain.bounds, shape, spacing)
        ]
        outgoing = np.zeros(shape, dtype=float)
        advection = []
        for axis in range(3):
            face_axes = [values.copy() for values in centers]
            lo, hi = self.domain.bounds[axis]
            face_axes[axis] = np.linspace(lo + spacing[axis], hi - spacing[axis], shape[axis] - 1)
            xyz = np.stack(np.meshgrid(*face_axes, indexing="ij"), axis=-1)
            velocity = self.model.drift_numpy(xyz)[..., axis]
            left = [slice(None)] * 3
            right = [slice(None)] * 3
            left[axis] = slice(0, shape[axis] - 1)
            right[axis] = slice(1, shape[axis])
            left_t, right_t = tuple(left), tuple(right)
            outgoing[left_t] += np.maximum(velocity, 0.0) / spacing[axis]
            outgoing[right_t] += np.maximum(-velocity, 0.0) / spacing[axis]
            advection.append((left_t, right_t, velocity, float(spacing[axis])))

        diffusion = np.asarray(self.model.diffusion, dtype=float)
        residual = np.diag(diffusion).copy()
        directions: list[tuple[tuple[int, int, int], float]] = []
        for i in range(3):
            for j in range(i + 1, 3):
                cross = float(diffusion[i, j])
                if abs(cross) <= 1.0e-15:
                    continue
                shift = [0, 0, 0]
                shift[i] = 1
                shift[j] = 1 if cross > 0.0 else -1
                rate = abs(cross) / (spacing[i] * spacing[j])
                residual[i] -= abs(cross) * spacing[i] / spacing[j]
                residual[j] -= abs(cross) * spacing[j] / spacing[i]
                directions.append((tuple(shift), float(rate)))
        if residual.min() < -1.0e-12:
            raise ValueError(
                "The requested diffusion/mesh combination has no non-negative "
                "axis-plus-pair-diagonal graph decomposition"
            )
        for axis, value in enumerate(np.maximum(residual, 0.0)):
            shift = [0, 0, 0]
            shift[axis] = 1
            directions.append((tuple(shift), float(value / spacing[axis] ** 2)))
        diffusion_edges = []
        for shift, rate in directions:
            left, right = self._paired_slices(shape, shift)
            outgoing[left] += rate
            outgoing[right] += rate
            diffusion_edges.append((left, right, rate))
        cfl = self.dt * outgoing
        if float(cfl.max()) > 1.0 + 1.0e-12:
            raise ValueError(
                f"Positive explicit low-order update violates its CFL bound: {cfl.max():.6g}"
            )
        self._low_order_data = {
            "shape": shape,
            "spacing": spacing,
            "advection": advection,
            "diffusion": diffusion_edges,
            "maximum_cfl": float(cfl.max()),
            "minimum_diagonal_weight": float(1.0 - cfl.max()),
            "diffusion_residual": residual.tolist(),
        }

    def _gather_averages(self, state: DensityState) -> np.ndarray | None:
        local, _, _ = self.cell_averages(state)
        gathered = self.comm.gather(local, root=0)
        if self.comm.rank != 0:
            return None
        result = np.empty(int(np.prod(self.domain.cells)), dtype=float)
        for indices, values in zip(self._flat_indices_by_rank, gathered):
            result[indices] = values
        return result.reshape(self.domain.cells)

    def _scatter_averages(self, values: np.ndarray | None) -> np.ndarray:
        if self.comm.rank == 0:
            flat = np.asarray(values, dtype=float).reshape(-1)
            chunks = [flat[indices] for indices in self._flat_indices_by_rank]
        else:
            chunks = None
        return np.asarray(self.comm.scatter(chunks, root=0), dtype=float)

    def _positive_low_order_step(self, old: np.ndarray) -> np.ndarray:
        data = self._low_order_data
        updated = old.copy()
        for left, right, velocity, spacing in data["advection"]:
            flux = np.maximum(velocity, 0.0) * old[left] + np.minimum(velocity, 0.0) * old[right]
            updated[left] -= self.dt * flux / spacing
            updated[right] += self.dt * flux / spacing
        for left, right, rate in data["diffusion"]:
            transfer = self.dt * rate * (old[right] - old[left])
            updated[left] += transfer
            updated[right] -= transfer
        return updated

    @staticmethod
    def _limited_antidiffusion(low: np.ndarray, high: np.ndarray) -> tuple[np.ndarray, dict[str, float]]:
        """Limit a conservative complete-graph antidiffusive mass decomposition."""
        low_flat = np.asarray(low, dtype=float).reshape(-1)
        high_flat = np.asarray(high, dtype=float).reshape(-1)
        high_mass_scale = float(low_flat.sum() / high_flat.sum())
        target = high_flat * high_mass_scale
        correction = target - low_flat
        negative = correction < 0.0
        limited = correction.copy()
        limited[negative] = np.maximum(correction[negative], -low_flat[negative])
        allowed_loss = float(-limited[negative].sum())
        requested_gain = float(correction[~negative].sum())
        gain_factor = allowed_loss / requested_gain if requested_gain > 0.0 else 0.0
        limited[~negative] = correction[~negative] * gain_factor
        result = low_flat + limited
        tiny = 128.0 * np.finfo(float).eps * max(1.0, float(np.max(low_flat)))
        result[np.logical_and(result < 0.0, result >= -tiny)] = 0.0
        if float(result.min()) < -tiny:
            raise RuntimeError("AFC limiter produced a negative cell average")
        conservation_error = float(result.sum() - low_flat.sum())
        return result.reshape(low.shape), {
            "high_mass_normalization_factor": high_mass_scale,
            "limited_antidiffusive_gain_fraction": gain_factor,
            "limited_cells": float(np.count_nonzero(limited != correction)),
            "minimum_low_order_average": float(low_flat.min()),
            "minimum_high_order_average": float(high_flat.min()),
            "minimum_afc_average": float(result.min()),
            "average_sum_conservation_error": conservation_error,
        }

    def step(self, state: DensityState) -> DensityState:
        started = time.perf_counter()
        old_averages = self._gather_averages(state)
        unlimited = super().step(state)
        self.last_unlimited_state = unlimited.copy("raw_q2_cn")
        high_averages = self._gather_averages(unlimited)
        if self.comm.rank == 0:
            low = self._positive_low_order_step(old_averages)
            if float(low.min()) < -1.0e-13:
                raise RuntimeError(
                    f"Positive low-order update failed on the supplied state: minimum={low.min():.6g}"
                )
            afc, afc_report = self._limited_antidiffusion(low, high_averages)
        else:
            afc = None
            afc_report = None
        prescribed = self._scatter_averages(afc)

        stage = unlimited.copy("afc_cell_average_update")
        for cell, dofs in enumerate(self.limiter.cell_dofs):
            values = stage.function.x.array[dofs].copy()
            desired = max(
                float(prescribed[cell]),
                1024.0 * np.finfo(float).eps * max(float(np.max(np.abs(values))), 1.0e-300),
            )
            values += desired - self.limiter.cell_average(values)
            values += desired - self.limiter.cell_average(values)
            stage.function.x.array[dofs] = values
        stage.function.x.scatter_forward()
        corrected, report = self.local_projector.project_state(
            stage, repair_cell_averages=False, adaptive_skip=True
        )
        raw = unlimited.function.x.array.copy()
        final = corrected.function.x.array.copy()
        afc_coefficients = stage.function.x.array.copy()
        afc_l1, afc_l2 = self.limiter._difference_norms(raw, afc_coefficients)
        total_l1, total_l2 = self.limiter._difference_norms(raw, final)
        mass_before = self.mass(unlimited)
        report.update({
            "method": "positive P0 graph update plus limited algebraic antidiffusion toward Q2-CN, followed by cell-local QP",
            "average_repair": "positive low-order/AFC update",
            "afc_cell_average_l1_correction": afc_l1,
            "afc_cell_average_l2_correction": afc_l2,
            "raw_to_final_l1_correction": total_l1,
            "raw_to_final_l2_correction": total_l2,
            "relative_l1_correction": total_l1 / max(abs(mass_before), np.finfo(float).tiny),
            "step_time": corrected.time,
            "low_order_maximum_cfl": (
                self._low_order_data["maximum_cfl"] if self.comm.rank == 0 else None
            ),
            "low_order_minimum_diagonal_weight": (
                self._low_order_data["minimum_diagonal_weight"] if self.comm.rank == 0 else None
            ),
            "afc": afc_report,
        })
        report["low_order_maximum_cfl"] = self.comm.bcast(
            report["low_order_maximum_cfl"], root=0
        )
        report["low_order_minimum_diagonal_weight"] = self.comm.bcast(
            report["low_order_minimum_diagonal_weight"], root=0
        )
        report["afc"] = self.comm.bcast(afc_report, root=0)
        report["mass_after"] = self.mass(corrected)
        report["wall_seconds"] = _global_max(self.comm, time.perf_counter() - started)
        self.last_local_projection_report = report
        self.local_projection_history.append(report)
        self.limiter.last_raw_coefficients = raw
        self.limiter.last_stage1_coefficients = afc_coefficients
        self.limiter.last_final_coefficients = final
        self.last_timing["afc_projection_seconds"] = float(report["wall_seconds"])
        self.last_timing["step_seconds"] = _global_max(self.comm, time.perf_counter() - started)
        return corrected

    def local_projection_history_summary(self) -> dict[str, object]:
        if not self.local_projection_history:
            return {"steps": 0}
        scalar_keys = (
            "relative_l1_correction",
            "raw_to_final_l2_correction",
            "afc_cell_average_l1_correction",
            "afc_cell_average_l2_correction",
            "local_qp_l1_correction",
            "local_qp_l2_correction",
            "raw_negative_cell_average_mass",
            "projected_probability_mass",
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
        result["low_order_maximum_cfl"] = float(max(
            float(item["low_order_maximum_cfl"])
            for item in self.local_projection_history
        ))
        result["minimum_antidiffusive_gain_fraction"] = float(min(
            float(item["afc"]["limited_antidiffusive_gain_fraction"])
            for item in self.local_projection_history
        ))
        result["maximum_afc_average_conservation_error"] = float(max(
            abs(float(item["afc"]["average_sum_conservation_error"]))
            for item in self.local_projection_history
        ))
        return result
