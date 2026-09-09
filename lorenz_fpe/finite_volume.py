"""Independent conservative finite-volume reference for selected test cases.

This module is deliberately independent of the UFL/DG spatial operator.  It
uses cell-centred, first-order upwind total fluxes, centred diagonal diffusion,
an explicit SSPRK(3,3) integrator, and a zero total numerical flux at every
outer face.  It is a validator, not a proposed high-order production method.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass

import numpy as np

from .core import Domain, Lorenz63Model


@dataclass
class FiniteVolumeResult:
    density: np.ndarray
    time: float
    steps: int
    minimum: float
    mass: float
    wall_seconds: float


class ConservativeFiniteVolume:
    """Monotone finite volume on the same rectangular truncated domain.

    The independent reference currently supports diagonal constant diffusion.
    Off-diagonal diffusion needs a different monotone flux construction and is
    rejected explicitly instead of being silently discarded.
    """

    def __init__(self, model: Lorenz63Model, domain: Domain, cfl: float = 0.72):
        self.model, self.domain, self.cfl = model, domain, float(cfl)
        self.shape = tuple(int(n) for n in domain.cells)
        self.widths = np.array(
            [(hi - lo) / n for (lo, hi), n in zip(domain.bounds, self.shape)]
        )
        diffusion = np.asarray(model.diffusion, dtype=float)
        off_diagonal = diffusion - np.diag(np.diag(diffusion))
        if np.linalg.norm(off_diagonal, ord=np.inf) > 1.0e-14:
            raise NotImplementedError(
                "The independent finite-volume validator supports diagonal D only"
            )
        self.diffusion = np.diag(diffusion).copy()
        self.centres = [
            np.linspace(lo + self.widths[d] / 2, hi - self.widths[d] / 2, self.shape[d])
            for d, (lo, hi) in enumerate(domain.bounds)
        ]
        self._face_velocities = self._build_face_velocities()
        rate = sum(
            np.max(np.abs(a)) / h + 2.0 * diffusivity / h**2
            for a, h, diffusivity in zip(
                self._face_velocities, self.widths, self.diffusion
            )
        )
        self.maximum_stable_step = self.cfl / rate

    def _build_face_velocities(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        nx, ny, nz = self.shape
        xc, yc, zc = self.centres
        xf = np.linspace(self.domain.bounds[0][0], self.domain.bounds[0][1], nx + 1)
        yf = np.linspace(self.domain.bounds[1][0], self.domain.bounds[1][1], ny + 1)
        zf = np.linspace(self.domain.bounds[2][0], self.domain.bounds[2][1], nz + 1)
        def component(a, b, c, index):
            coordinates = np.stack(
                np.broadcast_arrays(a[:, None, None], b[None, :, None], c[None, None, :]),
                axis=-1,
            )
            return np.asarray(self.model.drift_numpy(coordinates)[..., index], dtype=float)
        return component(xf, yc, zc, 0), component(xc, yf, zc, 1), component(xc, yc, zf, 2)

    def rhs(self, density: np.ndarray) -> np.ndarray:
        p = np.asarray(density, dtype=float)
        if p.shape != self.shape:
            raise ValueError(f"Expected density shape {self.shape}, got {p.shape}")
        hx, hy, hz = self.widths
        ax, ay, az = self._face_velocities
        dx, dy, dz = self.diffusion
        fx = np.zeros((self.shape[0] + 1, self.shape[1], self.shape[2]))
        fy = np.zeros((self.shape[0], self.shape[1] + 1, self.shape[2]))
        fz = np.zeros((self.shape[0], self.shape[1], self.shape[2] + 1))
        vx = ax[1:-1]
        vy = ay[:, 1:-1]
        vz = az[:, :, 1:-1]
        fx[1:-1] = np.where(vx >= 0.0, vx * p[:-1], vx * p[1:]) - dx * (p[1:] - p[:-1]) / hx
        fy[:, 1:-1] = np.where(vy >= 0.0, vy * p[:, :-1], vy * p[:, 1:]) - dy * (p[:, 1:] - p[:, :-1]) / hy
        fz[:, :, 1:-1] = np.where(vz >= 0.0, vz * p[:, :, :-1], vz * p[:, :, 1:]) - dz * (p[:, :, 1:] - p[:, :, :-1]) / hz
        return -(
            (fx[1:] - fx[:-1]) / hx
            + (fy[:, 1:] - fy[:, :-1]) / hy
            + (fz[:, :, 1:] - fz[:, :, :-1]) / hz
        )

    def propagate(self, density: np.ndarray, t0: float, t1: float) -> FiniteVolumeResult:
        """Propagate cell averages with positivity-preserving SSPRK(3,3)."""
        p = np.asarray(density, dtype=float).copy()
        if np.min(p) < -1.0e-13:
            raise ValueError("Finite-volume propagation requires non-negative cell averages")
        volume = float(np.prod(self.widths))
        initial_mass = float(p.sum() * volume)
        duration = float(t1 - t0)
        if duration < 0:
            raise ValueError("t1 must be at least t0")
        steps = max(1, math.ceil(duration / self.maximum_stable_step)) if duration else 0
        dt = duration / steps if steps else 0.0
        started = time.perf_counter()
        for _ in range(steps):
            p1 = p + dt * self.rhs(p)
            p2 = 0.75 * p + 0.25 * (p1 + dt * self.rhs(p1))
            p = (1.0 / 3.0) * p + (2.0 / 3.0) * (p2 + dt * self.rhs(p2))
        mass = float(p.sum() * volume)
        if abs(mass - initial_mass) > 5.0e-12 * max(1.0, abs(initial_mass)):
            raise FloatingPointError("Finite-volume total-flux update lost mass")
        if np.min(p) < -2.0e-13:
            raise FloatingPointError("Finite-volume SSP update lost positivity")
        return FiniteVolumeResult(
            p, t1, steps, float(p.min()), mass, time.perf_counter() - started
        )

    def diagnostics(self, density: np.ndarray) -> dict[str, object]:
        p = np.asarray(density, dtype=float)
        volume = float(np.prod(self.widths))
        probability = p * volume
        mass = float(probability.sum())
        X = np.meshgrid(*self.centres, indexing="ij")
        mean = np.array([(probability * X[d]).sum() / mass for d in range(3)])
        covariance = np.empty((3, 3))
        for i in range(3):
            for j in range(3):
                covariance[i, j] = float(
                    (probability * (X[i] - mean[i]) * (X[j] - mean[j])).sum() / mass
                )
                if i == j:
                    covariance[i, j] += self.widths[i] ** 2 / 12.0
        return {
            "mass": mass,
            "minimum": float(p.min()),
            "mean": mean.tolist(),
            "covariance": covariance.tolist(),
        }
