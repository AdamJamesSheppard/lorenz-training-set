"""Core modern-FEniCSx Lorenz-63 Fokker--Planck implementation.

The spatial method is tensor-product DG(Qk) with upwind advection and symmetric interior
penalty diffusion.  Backward Euler is followed by the two-stage conservative
positivity post-processing of Liu, Hu, Taitano & Zhang (2025): a constrained
L2 projection of cell averages and a Zhang--Shu scaling of higher modes.

On the affine, axis-aligned hexahedra created here, Q1 vertex positivity is a
whole-cell guarantee.  For Q2/Q3, the implementation instead enforces
non-negative Bernstein coefficients on tensor-product subcells, which is a
sufficient (but not necessary) whole-cell positivity condition.
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable

import numpy as np
from mpi4py import MPI
from petsc4py import PETSc

import basix.ufl
import dolfinx
import ufl
from dolfinx import fem, mesh
from dolfinx.fem.petsc import LinearProblem, assemble_matrix, assemble_vector, create_vector, assign


def _global_sum(comm: MPI.Comm, value: float) -> float:
    return float(comm.allreduce(float(value), op=MPI.SUM))


def _global_min(comm: MPI.Comm, value: float) -> float:
    return float(comm.allreduce(float(value), op=MPI.MIN))


def _global_max(comm: MPI.Comm, value: float) -> float:
    return float(comm.allreduce(float(value), op=MPI.MAX))


@dataclass(frozen=True)
class Domain:
    bounds: tuple[tuple[float, float], tuple[float, float], tuple[float, float]] = (
        (-30.0, 30.0), (-40.0, 40.0), (-10.0, 70.0)
    )
    cells: tuple[int, int, int] = (12, 16, 16)

    @property
    def volume(self) -> float:
        return float(np.prod([b - a for a, b in self.bounds]))


@dataclass(frozen=True)
class Lorenz63Model:
    sigma: float = 10.0
    rho: float = 28.0
    beta: float = 8.0 / 3.0
    B: tuple[tuple[float, float, float], ...] = (
        (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)
    )

    @property
    def diffusion(self) -> np.ndarray:
        B = np.asarray(self.B, dtype=float)
        return 0.5 * B @ B.T

    def drift_numpy(self, x: np.ndarray) -> np.ndarray:
        out = np.empty_like(x, dtype=float)
        out[..., 0] = self.sigma * (x[..., 1] - x[..., 0])
        out[..., 1] = x[..., 0] * (self.rho - x[..., 2]) - x[..., 1]
        out[..., 2] = x[..., 0] * x[..., 1] - self.beta * x[..., 2]
        return out

    def drift_ufl(self, x: ufl.core.expr.Expr) -> ufl.core.expr.Expr:
        return ufl.as_vector((
            self.sigma * (x[1] - x[0]),
            x[0] * (self.rho - x[2]) - x[1],
            x[0] * x[1] - self.beta * x[2],
        ))


@dataclass
class DensityState:
    function: fem.Function
    time: float = 0.0
    label: str = "density"

    def copy(self, label: str | None = None) -> "DensityState":
        q = fem.Function(self.function.function_space)
        q.x.array[:] = self.function.x.array
        q.x.scatter_forward()
        return DensityState(q, self.time, label or self.label)

    def save_native(self, path: Path) -> None:
        """Lossless serial checkpoint of DG coefficients and minimal metadata."""
        comm = self.function.function_space.mesh.comm
        if comm.size != 1:
            raise NotImplementedError("Native NumPy checkpoints currently require serial execution")
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(path, coefficients=self.function.x.array, time=self.time, label=self.label)


@dataclass(frozen=True)
class LimiterReport:
    activated: bool
    corrected_cell_averages: int
    scaled_cells: int
    touched_cells: int
    corrected_fraction: float
    corrected_cell_average_fraction: float
    scaled_cell_fraction: float
    l2_cell_average_correction: float
    minimum_before: float
    minimum_after: float
    minimum_cell_average: float
    mass_before: float
    mass_after_stage1: float
    mass_after: float
    raw_negative_cell_averages: int
    raw_negative_cell_average_fraction: float
    minimum_raw_cell_average: float
    stage1_l1_correction: float
    stage1_l2_correction: float
    scaling_l1_correction: float
    scaling_l2_correction: float
    raw_to_final_l1_correction: float
    raw_to_final_l2_correction: float
    relative_l1_correction: float
    minimum_scaling_factor: float
    mean_scaling_factor: float
    projection_iterations: int
    projection_seconds: float
    scaling_seconds: float
    certificate_mode: str
    raw_certificate_counts: dict[str, int] | None
    raw_certificate_max_depth: int | None
    raw_certificate_lower_bound: float | None
    raw_certificate_upper_bound: float | None
    raw_witness_minimum: float | None
    raw_quadrature_negative_mass: float | None
    stage1_certificate_counts: dict[str, int] | None
    stage1_certificate_max_depth: int | None


class PositivityLimiter:
    """Conservative cell-average projection plus Bernstein scaling.

    Stage 1 solves exactly (to bisection tolerance)

      min 1/2 sum_K |K| (x_K-w_K)^2
      subject to x_K >= lower and sum_K |K|x_K = sum_K |K|w_K.

    KKT gives x_K=max(lower,w_K-lambda); lambda is found by bisection.
    Stage 2 scales each tensor-product polynomial about its corrected cell
    average until all Bernstein coefficients are non-negative.  This is a
    sufficient whole-cell positivity condition because the Bernstein basis is
    non-negative and forms a partition of unity.
    """

    def __init__(self, V: fem.FunctionSpace, cell_volumes: np.ndarray,
                 degree: int = 1, lower: float = 0.0,
                 certificate_mode: str = "fixed", certificate_max_depth: int = 4,
                 certificate_diagnostics: bool = False):
        self.V = V
        self.comm = V.mesh.comm
        self.degree = int(degree)
        self.lower = float(lower)
        if certificate_mode not in {"fixed", "adaptive"}:
            raise ValueError("certificate_mode must be 'fixed' or 'adaptive'")
        if certificate_max_depth < 0:
            raise ValueError("certificate_max_depth must be non-negative")
        self.certificate_mode = certificate_mode
        self.certificate_max_depth = int(certificate_max_depth)
        self.certificate_diagnostics = bool(certificate_diagnostics or certificate_mode == "adaptive")
        self.n_local_cells = V.mesh.topology.index_map(V.mesh.topology.dim).size_local
        self.cell_volumes = np.asarray(cell_volumes[: self.n_local_cells], dtype=float)
        self.cell_dofs = [V.dofmap.cell_dofs(c).copy() for c in range(self.n_local_cells)]
        n = {len(d) for d in self.cell_dofs}; expected=(self.degree+1)**3
        if n != {expected}:
            raise ValueError(f"Q{self.degree} hexahedra require {expected} local dofs per cell; got {sorted(n)}")
        gp, gw = np.polynomial.legendre.leggauss(self.degree+2)
        gp = 0.5 * (gp + 1.0); gw = 0.5 * gw
        points=[]; weights=[]
        for i in range(len(gp)):
            for j in range(len(gp)):
                for k in range(len(gp)):
                    points.append((gp[i],gp[j],gp[k]))
                    weights.append(gw[i]*gw[j]*gw[k])
        tab = V.element.basix_element.tabulate(0, np.asarray(points,dtype=np.float64))
        self._quadrature_basis=np.asarray(tab[0,:,:,0])
        self._quadrature_weights=np.asarray(weights)
        self.average_weights=self._quadrature_weights@self._quadrature_basis

        # Convert Basix's nodal coefficients to tensor-product Bernstein
        # coefficients.  The transformation is computed from polynomial
        # values and is independent of Basix's internal dof ordering.
        def bernstein_1d(i,t):
            return math.comb(self.degree,i)*t**i*(1.-t)**(self.degree-i)
        local_points=np.array([(i/self.degree,j/self.degree,k/self.degree)
            for i in range(self.degree+1) for j in range(self.degree+1)
            for k in range(self.degree+1)],dtype=np.float64)
        bernstein=np.array([[bernstein_1d(i,p[0])*bernstein_1d(j,p[1])*bernstein_1d(k,p[2])
            for i in range(self.degree+1) for j in range(self.degree+1) for k in range(self.degree+1)]
            for p in local_points])
        self.control_subdivisions=1 if self.degree==1 else 2
        whole_lagrange=np.asarray(
            V.element.basix_element.tabulate(0,local_points)[0,:,:,0]
        )
        self.to_whole_bernstein=np.linalg.solve(bernstein,whole_lagrange)
        transforms=[]
        for a in range(self.control_subdivisions):
            for b in range(self.control_subdivisions):
                for c in range(self.control_subdivisions):
                    global_points=(local_points+np.array([a,b,c]))/self.control_subdivisions
                    lagrange_values=np.asarray(V.element.basix_element.tabulate(0,global_points)[0,:,:,0])
                    transforms.append(np.linalg.solve(bernstein,lagrange_values))
        self.to_bernstein=np.vstack(transforms)

    @staticmethod
    def _split_bernstein_axis(values: np.ndarray, axis: int) -> tuple[np.ndarray,np.ndarray]:
        """Split a tensor Bernstein polynomial at one half along one axis."""
        moved=np.moveaxis(np.asarray(values,dtype=float),axis,0)
        degree=moved.shape[0]-1
        left=np.empty_like(moved); right=np.empty_like(moved)
        work=moved.copy(); left[0]=work[0]; right[degree]=work[degree]
        for level in range(1,degree+1):
            work[:degree-level+1]=.5*(work[:degree-level+1]+work[1:degree-level+2])
            left[level]=work[0]
            right[degree-level]=work[degree-level]
        return np.moveaxis(left,0,axis),np.moveaxis(right,0,axis)

    @classmethod
    def _split_bernstein_box(cls, values: np.ndarray) -> list[np.ndarray]:
        boxes=[np.asarray(values,dtype=float)]
        for axis in range(3):
            boxes=[child for box in boxes for child in cls._split_bernstein_axis(box,axis)]
        return boxes

    def classify_coefficients(self, coefficients: np.ndarray,
                              max_depth: int | None = None) -> dict[str,object]:
        """Classify tensor-polynomial non-negativity by Bernstein subdivision.

        Non-negative control coefficients certify the polynomial on a box.
        A negative point evaluation is a witness.  Bounds that still straddle
        zero at ``max_depth`` are reported as unresolved.
        """
        depth_limit=self.certificate_max_depth if max_depth is None else int(max_depth)
        if depth_limit < 0:
            raise ValueError("max_depth must be non-negative")
        shape=(self.degree+1,)*3
        root=(self.to_whole_bernstein@np.asarray(coefficients,dtype=float)).reshape(shape)
        stack=[(root,0)]; leaf_lower=math.inf; leaf_upper=-math.inf; reached=0
        unresolved=False; witness_value=math.inf
        weights=np.array([math.comb(self.degree,i) for i in range(self.degree+1)],dtype=float)
        weights/=2.0**self.degree
        while stack:
            box,depth=stack.pop(); reached=max(reached,depth)
            lower=float(box.min()); upper=float(box.max())
            scale=max(float(np.max(np.abs(box))),np.finfo(float).tiny)
            witness_tolerance=128.0*np.finfo(float).eps*scale
            corner_min=float(min(box[i,j,k] for i in (0,-1) for j in (0,-1) for k in (0,-1)))
            centre=float(np.einsum("i,j,k,ijk->",weights,weights,weights,box))
            candidate=min(corner_min,centre)
            witness_value=min(witness_value,candidate)
            if candidate < -witness_tolerance:
                return {"status":"WITNESSED_NEGATIVE","depth":depth,
                    "lower_bound":lower,"upper_bound":upper,
                    "witness_value":candidate,"witness_tolerance":witness_tolerance}
            if lower >= self.lower:
                leaf_lower=min(leaf_lower,lower); leaf_upper=max(leaf_upper,upper)
                continue
            if depth >= depth_limit:
                leaf_lower=min(leaf_lower,lower); leaf_upper=max(leaf_upper,upper)
                unresolved=True
                continue
            stack.extend((child,depth+1) for child in self._split_bernstein_box(box))
        return {"status":"UNRESOLVED" if unresolved else "CERTIFIED_NONNEGATIVE",
            "depth":reached,"lower_bound":leaf_lower,"upper_bound":leaf_upper,
            "witness_value":None if math.isinf(witness_value) else witness_value,
            "witness_tolerance":None}

    def _classification_summary(self, coefficients: np.ndarray) -> dict[str,object]:
        counts={name:0 for name in ("CERTIFIED_NONNEGATIVE","WITNESSED_NEGATIVE","UNRESOLVED")}
        max_depth=0; lower=math.inf; upper=-math.inf; witness=math.inf; negative_mass=0.0
        records=[]
        for c,dofs in enumerate(self.cell_dofs):
            cell_coefficients=coefficients[dofs]
            result=self.classify_coefficients(cell_coefficients)
            records.append(result); counts[str(result["status"])]+=1
            max_depth=max(max_depth,int(result["depth"]))
            lower=min(lower,float(result["lower_bound"])); upper=max(upper,float(result["upper_bound"]))
            if result["status"]=="WITNESSED_NEGATIVE":
                witness=min(witness,float(result["witness_value"]))
            values=self._quadrature_basis@cell_coefficients
            negative_mass+=self.cell_volumes[c]*float(self._quadrature_weights@np.maximum(-values,0.0))
        global_counts={name:int(self.comm.allreduce(value,op=MPI.SUM)) for name,value in counts.items()}
        global_witness=_global_min(self.comm,witness)
        return {"counts":global_counts,
            "max_depth":int(self.comm.allreduce(max_depth,op=MPI.MAX)),
            "lower_bound":_global_min(self.comm,lower),"upper_bound":_global_max(self.comm,upper),
            "witness_minimum":None if math.isinf(global_witness) else global_witness,
            "quadrature_negative_mass":_global_sum(self.comm,negative_mass),
            "local_records":records}

    def classification_records(self, coefficients: np.ndarray) -> list[dict[str,object]]:
        """Return auditable local cell records for an adaptive classification."""
        records=[]
        geom=self.V.mesh.geometry.x; gdmap=self.V.mesh.geometry.dofmaps[0]
        for c,dofs in enumerate(self.cell_dofs):
            cell_coefficients=np.asarray(coefficients[dofs],dtype=float)
            result=dict(self.classify_coefficients(cell_coefficients))
            values=self._quadrature_basis@cell_coefficients
            midpoint=geom[gdmap[c]].mean(axis=0)
            average=self.cell_average(cell_coefficients)
            result.update({"local_cell":c,"midpoint":midpoint.tolist(),
                "cell_average":average,"cell_mass":average*self.cell_volumes[c],
                "quadrature_negative_mass":self.cell_volumes[c]*float(
                    self._quadrature_weights@np.maximum(-values,0.0)
                )})
            records.append(result)
        return records

    def cell_average(self, coefficients: np.ndarray) -> float:
        return float(self.average_weights@coefficients)

    def control_coefficients(self, coefficients: np.ndarray) -> np.ndarray:
        return self.to_bernstein@coefficients

    def subcell_average_matrix(self, subdivisions: int) -> np.ndarray:
        """Exact isotropic reference-subcell average map for Qk coefficients."""
        s=int(subdivisions)
        return self.subcell_average_matrix_anisotropic((s, s, s))

    def subcell_average_matrix_anisotropic(
        self, subdivisions: tuple[int, int, int]
    ) -> np.ndarray:
        """Exact average map on an anisotropic tensor partition of a cell."""
        counts=tuple(int(value) for value in subdivisions)
        if any(value < 1 for value in counts):
            raise ValueError("subdivision counts must all be positive")
        gp,gw=np.polynomial.legendre.leggauss(self.degree+1)
        gp=.5*(gp+1.); gw=.5*gw; rows=[]
        sx,sy,sz=counts
        for i in range(sx):
            for j in range(sy):
                for k in range(sz):
                    points=np.array([((i+gp[a])/sx,(j+gp[b])/sy,(k+gp[c])/sz)
                        for a in range(len(gp)) for b in range(len(gp)) for c in range(len(gp))])
                    weights=np.array([gw[a]*gw[b]*gw[c]
                        for a in range(len(gp)) for b in range(len(gp)) for c in range(len(gp))])
                    basis=np.asarray(self.V.element.basix_element.tabulate(0,points)[0,:,:,0])
                    rows.append(weights@basis)
        return np.asarray(rows)

    def _difference_norms(self, before: np.ndarray, after: np.ndarray) -> tuple[float,float]:
        """Quadrature L1/L2 norms of a DG1 coefficient difference."""
        l1_local=0.0; l2sq_local=0.0
        for c,dofs in enumerate(self.cell_dofs):
            values=self._quadrature_basis @ (after[dofs]-before[dofs])
            l1_local += self.cell_volumes[c]*float(self._quadrature_weights@np.abs(values))
            l2sq_local += self.cell_volumes[c]*float(self._quadrature_weights@(values*values))
        l1=_global_sum(self.comm,l1_local)
        l2=math.sqrt(max(0.0,_global_sum(self.comm,l2sq_local)))
        return l1,l2

    @staticmethod
    def project_cell_averages(w: np.ndarray, volumes: np.ndarray, lower: float = 0.0) -> np.ndarray:
        w = np.asarray(w, dtype=float)
        volumes = np.asarray(volumes, dtype=float)
        target = float(np.dot(volumes, w))
        floor_mass = float(lower * volumes.sum())
        if target < floor_mass - 1e-13 * max(1.0, abs(target)):
            raise ValueError("Positivity constraint infeasible: total mass lies below lower*volume")
        if np.min(w) >= lower:
            return w.copy()
        # Projection is max(lower,w-lambda). Unequal cell volumes cancel in
        # the KKT stationarity equation because the L2 objective and mass
        # constraint carry the same |K| factor.
        lo = float(np.min(w - lower) - max(1.0, np.ptp(w)))
        hi = float(np.max(w - lower))
        for _ in range(100):
            lam = 0.5 * (lo + hi)
            x = np.maximum(lower, w - lam)
            mass = float(np.dot(volumes, x))
            if mass > target:
                lo = lam
            else:
                hi = lam
        x = np.maximum(lower, w - 0.5 * (lo + hi))
        # Remove the last few ulps without crossing the lower bound.  A
        # uniform additive repair can make tiny active entries negative when
        # the residual is negative, so contract their non-negative slacks
        # proportionally instead.
        err = target - float(np.dot(volumes, x))
        if err < 0.0:
            slack = x - lower
            slack_mass = float(np.dot(volumes, slack))
            if slack_mass > 0.0:
                x = lower + np.clip(1.0 + err / slack_mass, 0.0, 1.0) * slack
        elif err > 0.0:
            x[int(np.argmax(volumes))] += err / float(np.max(volumes))
        x = np.maximum(x, lower)

        # A final one-cell repair addresses roundoff from the proportional
        # contraction.  For a negative residual choose a cell with enough
        # slack, and for a positive residual any positive-volume cell works.
        err = target - float(np.dot(volumes, x))
        if err < 0.0:
            capacities = volumes * (x - lower)
            index = int(np.argmax(capacities))
            x[index] += err / float(volumes[index])
        elif err > 0.0:
            index = int(np.argmax(volumes))
            x[index] += err / float(volumes[index])
        x = np.maximum(x, lower)
        return x

    def apply(self, state: DensityState) -> LimiterReport:
        u = state.function
        coeff = u.x.array
        raw_coeff=coeff.copy()
        local_avgs = np.array([self.cell_average(coeff[d]) for d in self.cell_dofs])
        local_min = min(float(self.control_coefficients(coeff[d]).min()) for d in self.cell_dofs)
        raw_negative_local=int(np.count_nonzero(local_avgs < self.lower))
        raw_min_avg_local=float(local_avgs.min())
        raw_certificate=(self._classification_summary(raw_coeff)
                         if self.certificate_diagnostics and self.degree >= 2 else None)
        projection_started=time.perf_counter()
        gathered_w = self.comm.gather(local_avgs, root=0)
        gathered_v = self.comm.gather(self.cell_volumes, root=0)
        if self.comm.rank == 0:
            w = np.concatenate(gathered_w)
            volumes = np.concatenate(gathered_v)
            x = self.project_cell_averages(w, volumes, self.lower)
            chunks = []
            offset = 0
            for a in gathered_w:
                chunks.append(x[offset:offset + len(a)])
                offset += len(a)
            mass_before = float(np.dot(volumes, w))
            mass_after_stage1 = float(np.dot(volumes, x))
            n_corrected = int(np.count_nonzero(np.abs(x - w) > 5e-15 * np.maximum(1.0, np.abs(w))))
            correction = float(np.sqrt(np.dot(volumes, (x - w) ** 2)))
            projection_iterations=100 if np.min(w)<self.lower else 0
        else:
            chunks = None
            mass_before = mass_after_stage1 = n_corrected = correction = projection_iterations = None
        corrected = self.comm.scatter(chunks, root=0)
        stage1_changed = np.abs(corrected - local_avgs) > (
            5e-15 * np.maximum(1.0, np.abs(local_avgs))
        )

        # Stage 1 changes only the cell constant modes.
        for c, dofs in enumerate(self.cell_dofs):
            old_avg = self.cell_average(coeff[dofs])
            new_avg = float(corrected[c])
            coeff[dofs] += new_avg-old_avg
        stage1_coeff=coeff.copy()
        projection_seconds=_global_max(self.comm,time.perf_counter()-projection_started)
        stage1_certificate=(self._classification_summary(stage1_coeff)
                            if self.certificate_mode=="adaptive" and self.degree >= 2 else None)

        # Stage 2 scales higher modes around the corrected cell average.
        scaling_started=time.perf_counter(); scaled=0; theta_sum=0.0; theta_min=1.0
        touched = stage1_changed.copy()
        certified_lower=math.inf
        for c,dofs in enumerate(self.cell_dofs):
            new_avg=float(corrected[c]); values=coeff[dofs].copy()
            vmin = float(self.control_coefficients(values).min())
            theta=1.0
            certified=(stage1_certificate is not None and
                       stage1_certificate["local_records"][c]["status"]=="CERTIFIED_NONNEGATIVE")
            if vmin < self.lower and not certified:
                denom = new_avg - vmin
                theta = 0.0 if denom <= 0.0 else float(np.clip(
                    (new_avg - self.lower) / denom, 0.0, 1.0
                ))
                values = new_avg + theta * (values - new_avg)
                scaled += 1
                touched[c] = True
            if certified:
                certified_lower=min(certified_lower,float(
                    stage1_certificate["local_records"][c]["lower_bound"]
                ))
            else:
                certified_lower=min(certified_lower,float(self.control_coefficients(values).min()))
            theta_sum += theta; theta_min=min(theta_min,theta)
            coeff[dofs] = values
        u.x.scatter_forward()
        scaling_seconds=_global_max(self.comm,time.perf_counter()-scaling_started)
        final_coeff=coeff.copy()
        self.last_raw_coefficients=raw_coeff
        self.last_stage1_coefficients=stage1_coeff
        self.last_final_coefficients=final_coeff
        stage1_l1,stage1_l2=self._difference_norms(raw_coeff,stage1_coeff)
        scaling_l1,scaling_l2=self._difference_norms(stage1_coeff,final_coeff)
        final_l1,final_l2=self._difference_norms(raw_coeff,final_coeff)

        minimum_after = _global_min(self.comm,certified_lower)
        minimum_before = _global_min(self.comm, local_min)
        scaled_global = int(self.comm.allreduce(scaled, op=MPI.SUM))
        touched_global = int(self.comm.allreduce(
            int(np.count_nonzero(touched)), op=MPI.SUM
        ))
        total_cells = int(self.comm.allreduce(self.n_local_cells, op=MPI.SUM))
        mass_before = self.comm.bcast(mass_before, root=0)
        mass_after_stage1 = self.comm.bcast(mass_after_stage1, root=0)
        n_corrected = int(self.comm.bcast(n_corrected, root=0))
        correction = float(self.comm.bcast(correction, root=0))
        projection_iterations=int(self.comm.bcast(projection_iterations,root=0))
        min_avg = _global_min(self.comm, min(self.cell_average(coeff[d]) for d in self.cell_dofs))
        raw_negative=int(self.comm.allreduce(raw_negative_local,op=MPI.SUM))
        raw_min_avg=_global_min(self.comm,raw_min_avg_local)
        theta_sum_global=_global_sum(self.comm,theta_sum)
        theta_min_global=_global_min(self.comm,theta_min)
        mass_after_final=_global_sum(self.comm,float(sum(self.cell_volumes[c]*self.cell_average(coeff[d]) for c,d in enumerate(self.cell_dofs))))
        return LimiterReport(
            activated=touched_global > 0,
            corrected_cell_averages=n_corrected,
            scaled_cells=scaled_global,
            touched_cells=touched_global,
            corrected_fraction=touched_global / max(1, total_cells),
            corrected_cell_average_fraction=n_corrected / max(1, total_cells),
            scaled_cell_fraction=scaled_global / max(1, total_cells),
            l2_cell_average_correction=correction,
            minimum_before=minimum_before,
            minimum_after=minimum_after,
            minimum_cell_average=min_avg,
            mass_before=float(mass_before),
            mass_after_stage1=float(mass_after_stage1),
            mass_after=float(mass_after_final),
            raw_negative_cell_averages=raw_negative,
            raw_negative_cell_average_fraction=raw_negative/max(1,total_cells),
            minimum_raw_cell_average=raw_min_avg,
            stage1_l1_correction=stage1_l1,
            stage1_l2_correction=stage1_l2,
            scaling_l1_correction=scaling_l1,
            scaling_l2_correction=scaling_l2,
            raw_to_final_l1_correction=final_l1,
            raw_to_final_l2_correction=final_l2,
            relative_l1_correction=final_l1/max(abs(float(mass_after_final)),np.finfo(float).tiny),
            minimum_scaling_factor=theta_min_global,
            mean_scaling_factor=theta_sum_global/max(1,total_cells),
            projection_iterations=projection_iterations,
            projection_seconds=projection_seconds,
            scaling_seconds=scaling_seconds,
            certificate_mode=self.certificate_mode,
            raw_certificate_counts=(raw_certificate["counts"] if raw_certificate else None),
            raw_certificate_max_depth=(raw_certificate["max_depth"] if raw_certificate else None),
            raw_certificate_lower_bound=(raw_certificate["lower_bound"] if raw_certificate else None),
            raw_certificate_upper_bound=(raw_certificate["upper_bound"] if raw_certificate else None),
            raw_witness_minimum=(raw_certificate["witness_minimum"] if raw_certificate else None),
            raw_quadrature_negative_mass=(raw_certificate["quadrature_negative_mass"] if raw_certificate else None),
            stage1_certificate_counts=(stage1_certificate["counts"] if stage1_certificate else None),
            stage1_certificate_max_depth=(stage1_certificate["max_depth"] if stage1_certificate else None),
        )


class FokkerPlanckSolver:
    """Conservative DG(Qk)/SIPG forecast solver with a reusable PETSc matrix."""

    def __init__(
        self,
        model: Lorenz63Model,
        domain: Domain = Domain(),
        dt: float = 0.0025,
        theta: float = 1.0,
        degree: int = 1,
        penalty: float = 16.0,
        limiter_lower: float = 0.0,
        ksp_rtol: float = 1e-10,
        ksp_atol: float = 1e-13,
        certificate_mode: str = "fixed",
        certificate_max_depth: int = 4,
        certificate_diagnostics: bool = False,
        apply_positivity: bool = True,
        axis_coordinates: tuple[np.ndarray, np.ndarray, np.ndarray] | None = None,
    ):
        self.model, self.domain, self.dt, self.theta = model, domain, float(dt), float(theta)
        self.ksp_rtol, self.ksp_atol = float(ksp_rtol), float(ksp_atol)
        self.degree = int(degree)
        self.apply_positivity = bool(apply_positivity)
        if not (0.5 <= self.theta <= 1.0): raise ValueError("theta must lie in [0.5,1]")
        if self.degree not in (1,2,3): raise ValueError("degree must be 1, 2, or 3")
        if self.ksp_rtol <= 0.0 or self.ksp_atol < 0.0:
            raise ValueError("KSP tolerances require ksp_rtol > 0 and ksp_atol >= 0")
        self.comm = MPI.COMM_WORLD
        a = [b[0] for b in domain.bounds]
        b = [b[1] for b in domain.bounds]
        self.mesh = mesh.create_box(
            self.comm, [np.asarray(a), np.asarray(b)], list(domain.cells),
            cell_type=mesh.CellType.hexahedron,
        )
        if axis_coordinates is None:
            self.axis_coordinates=tuple(
                np.linspace(lo,hi,count+1,dtype=float)
                for (lo,hi),count in zip(domain.bounds,domain.cells)
            )
        else:
            coordinates=tuple(np.asarray(values,dtype=float) for values in axis_coordinates)
            for axis,(values,(lo,hi),count) in enumerate(zip(
                coordinates,domain.bounds,domain.cells
            )):
                if values.shape != (count+1,):
                    raise ValueError(
                        f"axis {axis} requires {count+1} coordinates, got {values.shape}"
                    )
                if not np.all(np.diff(values)>0.0):
                    raise ValueError(f"axis {axis} coordinates must be strictly increasing")
                if not np.allclose(values[[0,-1]],[lo,hi],rtol=0.0,atol=1.0e-12):
                    raise ValueError(f"axis {axis} coordinates must match domain bounds")
            self.axis_coordinates=coordinates
            # create_box provides the required conforming hexahedral topology.
            # Moving its vertices along each Cartesian axis produces affine,
            # axis-aligned graded hexes without changing connectivity.
            geometry=self.mesh.geometry.x
            for axis,(values,(lo,hi),count) in enumerate(zip(
                self.axis_coordinates,domain.bounds,domain.cells
            )):
                uniform_index=np.rint((geometry[:,axis]-lo)*count/(hi-lo)).astype(int)
                if np.any((uniform_index<0)|(uniform_index>count)):
                    raise RuntimeError("structured mesh vertex could not be mapped to graded axis")
                geometry[:,axis]=values[uniform_index]
        element = basix.ufl.element("DG", self.mesh.basix_cell(), self.degree)
        self.V = fem.functionspace(self.mesh, element)
        q0e = basix.ufl.element("DG", self.mesh.basix_cell(), 0)
        self.Q0 = fem.functionspace(self.mesh, q0e)
        self.cell_volumes = self._cell_volumes()
        self.limiter = PositivityLimiter(
            self.V,self.cell_volumes,self.degree,limiter_lower,certificate_mode,
            certificate_max_depth,certificate_diagnostics,
        )

        self.p_old = fem.Function(self.V, name="density_old")
        self.p_new = fem.Function(self.V, name="density")
        u, v = ufl.TrialFunction(self.V), ufl.TestFunction(self.V)
        x = ufl.SpatialCoordinate(self.mesh)
        n = ufl.FacetNormal(self.mesh)
        h = ufl.CellDiameter(self.mesh)
        f = model.drift_ufl(x)
        D_np = model.diffusion
        D = ufl.as_matrix(D_np.tolist())

        # Conservative upwind advective flux on interior facets.
        beta_n = ufl.dot(ufl.avg(f), n("+"))
        u_up = ufl.conditional(ufl.ge(beta_n, 0.0), u("+"), u("-"))
        adv_volume = -ufl.dot(f * u, ufl.grad(v)) * ufl.dx
        adv_face = beta_n * u_up * (v("+") - v("-")) * ufl.dS
        adv = adv_volume + adv_face

        # Symmetric interior penalty for the full constant diffusion tensor.
        Du = ufl.dot(D, ufl.grad(u))
        Dv = ufl.dot(D, ufl.grad(v))
        jump_u_n = ufl.jump(u, n)
        jump_v_n = ufl.jump(v, n)
        normal_diff = ufl.avg(ufl.dot(n, ufl.dot(D, n)))
        sipg = ufl.dot(Du, ufl.grad(v)) * ufl.dx
        sipg += -ufl.dot(ufl.avg(Du), jump_v_n) * ufl.dS
        sipg += -ufl.dot(ufl.avg(Dv), jump_u_n) * ufl.dS
        sipg += penalty*self.degree**2 * normal_diff / ufl.avg(h) * ufl.dot(jump_u_n, jump_v_n) * ufl.dS

        mass = u * v * ufl.dx
        spatial=adv+sipg
        # Retain the method-defining bilinear forms for controlled
        # cross-framework action comparisons.  The production step still
        # assembles the combined theta-method matrix below.
        self.mass_bilinear_form = fem.form(mass)
        self.advection_volume_bilinear_form = fem.form(adv_volume)
        self.advection_face_bilinear_form = fem.form(adv_face)
        self.advection_bilinear_form = fem.form(adv)
        self.diffusion_bilinear_form = fem.form(sipg)
        self.spatial_bilinear_form = fem.form(spatial)
        old_spatial=ufl.replace(spatial,{u:self.p_old})
        self.a_form = fem.form(mass + self.theta*self.dt*spatial)
        self.L_form = fem.form(self.p_old*v*ufl.dx-(1.0-self.theta)*self.dt*old_spatial)
        assembly_started=time.perf_counter()
        self.A = assemble_matrix(self.a_form)
        self.A.assemble()
        self.matrix_assembly_seconds=_global_max(self.comm,time.perf_counter()-assembly_started)
        self.b = create_vector(self.V)
        self.x = create_vector(self.V)
        self.r = create_vector(self.V)
        self.ksp = PETSc.KSP().create(self.comm)
        self.ksp.setOperators(self.A)
        self.ksp.setType("gmres")
        self.ksp.setTolerances(rtol=self.ksp_rtol, atol=self.ksp_atol, max_it=1000)
        self.ksp.setErrorIfNotConverged(True)
        pc = self.ksp.getPC()
        pc.setType("bjacobi" if self.comm.size > 1 else "ilu")
        self.ksp.setFromOptions()
        self.ksp.setUp()
        self.last_linear: dict[str, float | int] = {}
        self.last_timing: dict[str,float] = {}
        self.last_limiter: LimiterReport | None = None
        self.limiter_history: list[LimiterReport] = []
        self.last_projection_report: dict[str, object] = {}
        self.last_initialization_report: dict[str, object] = {}
        self.last_sampling_report: dict[str, object] = {}
        self._projection_counter = 0
        self._mass_form_new = fem.form(self.p_new * ufl.dx)

    def _cell_volumes(self) -> np.ndarray:
        q = ufl.TestFunction(self.Q0)
        vec = assemble_vector(fem.form(q * ufl.dx))
        vec.ghostUpdate(addv=PETSc.InsertMode.ADD, mode=PETSc.ScatterMode.REVERSE)
        n = self.mesh.topology.index_map(self.mesh.topology.dim).size_local
        return np.asarray(vec.array[:n], dtype=float).copy()

    def _integral(self, expr: ufl.core.expr.Expr, quadrature_degree: int | None = None) -> float:
        measure = ufl.dx if quadrature_degree is None else ufl.Measure(
            "dx", domain=self.mesh, metadata={"quadrature_degree": int(quadrature_degree)}
        )
        return _global_sum(self.comm, fem.assemble_scalar(fem.form(expr * measure)))

    def gaussian_expression(self, mean: Iterable[float], covariance: np.ndarray):
        """Return the analytic whole-space Gaussian as a UFL expression."""
        mean = np.asarray(tuple(mean), dtype=float)
        cov = np.asarray(covariance, dtype=float)
        inv = np.linalg.inv(cov)
        x = ufl.SpatialCoordinate(self.mesh)
        delta = ufl.as_vector([x[i] - float(mean[i]) for i in range(3)])
        norm = (2.0 * np.pi) ** -1.5 / math.sqrt(float(np.linalg.det(cov)))
        return norm * ufl.exp(-0.5 * ufl.dot(delta, ufl.dot(ufl.as_matrix(inv.tolist()), delta)))

    def project_expression(
        self,
        expression,
        label: str = "l2_projection",
        quadrature_degree: int = 10,
        normalize: bool = True,
        apply_limiter: bool = True,
    ) -> DensityState:
        """Quadrature-controlled L2 projection into the solver's DG space."""
        trial, test = ufl.TrialFunction(self.V), ufl.TestFunction(self.V)
        dxq = ufl.Measure("dx", domain=self.mesh, metadata={"quadrature_degree": int(quadrature_degree)})
        q = fem.Function(self.V, name="density")
        self._projection_counter += 1
        started = time.perf_counter()
        problem = LinearProblem(
            trial * test * dxq,
            expression * test * dxq,
            u=q,
            petsc_options_prefix=f"density_l2_projection_{self._projection_counter}_",
            petsc_options={
                "ksp_type": "cg", "pc_type": "jacobi", "ksp_rtol": 1.0e-13,
                "ksp_atol": 1.0e-15, "ksp_error_if_not_converged": None,
            },
        )
        problem.solve()
        q.x.scatter_forward()
        state = DensityState(q, 0.0, label)
        mass_before = self.mass(state)
        if normalize:
            self.normalize(state)
        minimum_before = _global_min(self.comm, float(q.x.array[: self.V.dofmap.index_map.size_local].min()))
        limiter_report = self.limiter.apply(state) if apply_limiter else None
        self.last_projection_report = {
            "quadrature_degree": int(quadrature_degree),
            "mass_before_normalization": mass_before,
            "normalized": bool(normalize),
            "minimum_coefficient_before_limiter": minimum_before,
            "limiter": asdict(limiter_report) if limiter_report else None,
            "wall_seconds": _global_max(self.comm, time.perf_counter() - started),
        }
        return state

    def gaussian_interpolated(self, mean: Iterable[float], covariance: np.ndarray,
                              label: str = "gaussian_interpolated") -> DensityState:
        """Nodal Q1 interpolation retained as an explicitly labelled baseline."""
        mean = np.asarray(tuple(mean), dtype=float)
        cov = np.asarray(covariance, dtype=float)
        inv = np.linalg.inv(cov)
        norm = (2.0 * np.pi) ** -1.5 / math.sqrt(float(np.linalg.det(cov)))
        q = fem.Function(self.V, name="density")
        def values(x: np.ndarray) -> np.ndarray:
            d = x.T - mean
            return norm * np.exp(-0.5 * np.einsum("ni,ij,nj->n", d, inv, d))
        q.interpolate(values)
        state = DensityState(q, 0.0, label)
        self.normalize(state)
        limiter_report=self.limiter.apply(state)
        self.last_initialization_report={"method":"nodal_interpolation","limiter":asdict(limiter_report)}
        return state

    def gaussian_projected(self, mean: Iterable[float], covariance: np.ndarray,
                           label: str = "gaussian_l2_projected", quadrature_degree: int = 10,
                           apply_limiter: bool = True) -> DensityState:
        """L2 projection of a Gaussian, normalized on the finite domain."""
        state=self.project_expression(self.gaussian_expression(mean, covariance), label,
                                      quadrature_degree, True, apply_limiter)
        self.last_initialization_report={"method":"l2_projection",**self.last_projection_report}
        return state

    def gaussian(self, mean: Iterable[float], covariance: np.ndarray, label: str = "gaussian") -> DensityState:
        """Backward-compatible nodal-interpolation initializer.

        New accuracy-sensitive experiments should choose explicitly between
        :meth:`gaussian_interpolated` and :meth:`gaussian_projected`.
        """
        return self.gaussian_interpolated(mean, covariance, label)

    def sample_density(self, state: DensityState, count: int,
                       rng: np.random.Generator) -> np.ndarray:
        """Draw exact rejection samples from a Bernstein-positive DG density.

        Cells are selected by exact polynomial mass. Conditional samples use
        uniform cell proposals and the largest Bernstein coefficient as a
        rigorous envelope.
        """
        if self.comm.size != 1:
            raise NotImplementedError("Native polynomial sampling currently requires a serial solver")
        if count < 1:
            raise ValueError("count must be positive")
        av, volumes, _ = self.cell_averages(state)
        masses = av * volumes
        if masses.min() < -1.0e-13 or masses.sum() <= 0:
            raise ValueError("Sampling requires a Bernstein-positive density with positive mass")
        probabilities = np.maximum(masses, 0.0); probabilities /= probabilities.sum()
        selected = rng.choice(len(av), size=int(count), p=probabilities)
        samples = np.empty((int(count), 3), dtype=float)
        gdmap = self.mesh.geometry.dofmaps[0]
        geometry = self.mesh.geometry.x
        proposed = 0
        for cell in np.unique(selected):
            targets = np.flatnonzero(selected == cell)
            coefficients = state.function.x.array[self.V.dofmap.cell_dofs(int(cell))]
            maximum = float(self.limiter.control_coefficients(coefficients).max())
            if maximum <= 0:
                raise RuntimeError("A zero-density cell was selected")
            accepted: list[np.ndarray] = []
            have = 0
            while have < len(targets):
                batch = max(64, 2 * (len(targets) - have))
                points = rng.random((batch, 3))
                phi = self.V.element.basix_element.tabulate(0, points)[0, :, :, 0]
                values = np.asarray(phi) @ coefficients
                keep = points[rng.random(batch) < np.clip(values / maximum, 0.0, 1.0)]
                accepted.append(keep); have += len(keep); proposed += batch
            reference = np.concatenate(accepted)[: len(targets)]
            xyz = geometry[gdmap[int(cell)]]
            lo, hi = xyz.min(axis=0), xyz.max(axis=0)
            samples[targets] = lo + reference * (hi - lo)
        self.last_sampling_report = {
            "method": f"exact_cell_mass_plus_q{self.degree}_bernstein_envelope_rejection",
            "samples": int(count), "proposals": int(proposed),
            "acceptance_rate": float(count / proposed),
        }
        return samples

    def sample_q1_density(self, state: DensityState, count: int,
                          rng: np.random.Generator) -> np.ndarray:
        """Compatibility wrapper for exact Q1 sampling."""
        if self.degree != 1:
            raise ValueError("sample_q1_density requires degree=1; use sample_density")
        return self.sample_density(state,count,rng)

    def load_native(self, path: Path) -> DensityState:
        """Reload a lossless serial DG checkpoint without Gaussianisation."""
        if self.comm.size != 1:
            raise NotImplementedError("Native NumPy checkpoints currently require serial execution")
        data = np.load(path)
        coeff = np.asarray(data["coefficients"])
        q = fem.Function(self.V, name="density")
        if coeff.shape != q.x.array.shape:
            raise ValueError(f"Checkpoint has {coeff.shape} coefficients, expected {q.x.array.shape}")
        q.x.array[:] = coeff; q.x.scatter_forward()
        return DensityState(q, float(data["time"]), str(data["label"]))

    def from_structured(self, density: np.ndarray, time_value: float = 0.0,
                        apply_limiter: bool = True) -> DensityState:
        """Conservatively reconstruct DG Qk from refined voxel averages.

        Full polynomial reconstruction requires the subcell-average map to
        have full column rank (normally ``s >= degree+1`` per axis).  Otherwise
        only the cellwise constant mode is reconstructed.  A constant
        correction retains input cell mass before optional positivity limiting.
        The same global array may be supplied on every MPI rank; each rank
        reconstructs only its owned cells.
        """
        arr = np.asarray(density, dtype=float)
        factors=[]
        for got,native in zip(arr.shape,self.domain.cells):
            if got % native: raise ValueError(f"Structured shape {arr.shape} is not an integer refinement of {self.domain.cells}")
            factors.append(got//native)
        if len(set(factors))!=1: raise ValueError("Structured refinement factor must be identical on all axes")
        s=factors[0]
        average_matrix=self.limiter.subcell_average_matrix(s)
        reconstruction=(np.linalg.pinv(average_matrix)
            if np.linalg.matrix_rank(average_matrix)==average_matrix.shape[1] else None)
        q = fem.Function(self.V, name="density")
        n = self.mesh.topology.index_map(self.mesh.topology.dim).size_local
        gdmap = self.mesh.geometry.dofmaps[0]
        for c in range(n):
            point = self.mesh.geometry.x[gdmap[c]].mean(axis=0)
            idx=[]
            for d, ((lo,hi), count) in enumerate(zip(self.domain.bounds,self.domain.cells)):
                idx.append(min(count-1,max(0,int(math.floor((point[d]-lo)/(hi-lo)*count)))))
            values=np.array([arr[idx[0]*s+i,idx[1]*s+j,idx[2]*s+k]
                             for i in range(s) for j in range(s) for k in range(s)])
            if reconstruction is None:
                coefficients=np.full((self.degree+1)**3,float(values.mean()))
            else:
                coefficients=reconstruction@values
                # Retain the input voxel mass in this cell exactly.
                coefficients += float(values.mean()-self.limiter.cell_average(coefficients))
            q.x.array[self.V.dofmap.cell_dofs(c)] = coefficients
        q.x.scatter_forward()
        state=DensityState(q,time_value,"structured_reconstruction")
        if apply_limiter:
            self.limiter.apply(state)
        return state

    def mixture(self, means: list[Iterable[float]], covariances: list[np.ndarray], weights: Iterable[float]) -> DensityState:
        means_a = [np.asarray(m, dtype=float) for m in means]
        covs = [np.asarray(c, dtype=float) for c in covariances]
        ws = np.asarray(tuple(weights), dtype=float); ws /= ws.sum()
        invs = [np.linalg.inv(c) for c in covs]
        norms = [(2*np.pi)**-1.5 / math.sqrt(float(np.linalg.det(c))) for c in covs]
        q = fem.Function(self.V, name="density")
        def values(x: np.ndarray) -> np.ndarray:
            xt = x.T; out = np.zeros(xt.shape[0])
            for w, m, inv, norm in zip(ws, means_a, invs, norms):
                d = xt - m; out += w*norm*np.exp(-0.5*np.einsum("ni,ij,nj->n", d, inv, d))
            return out
        q.interpolate(values)
        state = DensityState(q, 0.0, "mixture")
        self.normalize(state); self.limiter.apply(state)
        return state

    def normalize(self, state: DensityState) -> float:
        mass = self.mass(state)
        if not np.isfinite(mass) or mass <= 0:
            raise ValueError(f"Cannot normalize density with mass {mass}")
        state.function.x.array[:] /= mass
        state.function.x.scatter_forward()
        return mass

    def mass(self, state: DensityState) -> float:
        return self._integral(state.function)

    def step(self, state: DensityState) -> DensityState:
        step_started=time.perf_counter(); rhs_started=time.perf_counter()
        self.p_old.x.array[:] = state.function.x.array
        self.p_old.x.scatter_forward()
        with self.b.localForm() as loc: loc.set(0.0)
        assemble_vector(self.b, self.L_form)
        self.b.ghostUpdate(addv=PETSc.InsertMode.ADD, mode=PETSc.ScatterMode.REVERSE)
        rhs_seconds=_global_max(self.comm,time.perf_counter()-rhs_started)
        with self.x.localForm() as loc: loc.set(0.0)
        t0 = time.perf_counter(); self.ksp.solve(self.b, self.x); elapsed = time.perf_counter()-t0
        self.x.ghostUpdate(addv=PETSc.InsertMode.INSERT, mode=PETSc.ScatterMode.FORWARD)
        assign(self.x, self.p_new); self.p_new.x.scatter_forward()
        residual_started=time.perf_counter()
        self.A.mult(self.x, self.r); self.r.scale(-1); self.r.axpy(1, self.b)
        rel = float(self.r.norm()) / max(float(self.b.norm()), np.finfo(float).tiny)
        residual_seconds=_global_max(self.comm,time.perf_counter()-residual_started)
        self.last_linear = {
            "ksp_reason": int(self.ksp.getConvergedReason()),
            "ksp_iterations": int(self.ksp.getIterationNumber()),
            "true_relative_residual": rel,
            "solve_seconds": elapsed,
        }
        out = DensityState(self.p_new, state.time + self.dt, "forecast")
        limiter_started=time.perf_counter()
        if self.apply_positivity:
            self.last_limiter = self.limiter.apply(out)
            self.limiter_history.append(self.last_limiter)
        else:
            self.last_limiter=None
            self.limiter.last_raw_coefficients=out.function.x.array.copy()
            self.limiter.last_stage1_coefficients=out.function.x.array.copy()
            self.limiter.last_final_coefficients=out.function.x.array.copy()
        self.last_timing={"rhs_seconds":rhs_seconds,"solve_seconds":_global_max(self.comm,elapsed),
            "residual_seconds":residual_seconds,
            "limiter_seconds":_global_max(self.comm,time.perf_counter()-limiter_started),
            "step_seconds":_global_max(self.comm,time.perf_counter()-step_started)}
        # Detach because p_new is reused.
        return out.copy()

    def limiter_stage_states(self, time_value: float) -> dict[str,DensityState]:
        """Return raw, cell-average-corrected, and fully limited last-step states."""
        result={}
        for name,attr in (("raw","last_raw_coefficients"),("stage1","last_stage1_coefficients"),
                          ("final","last_final_coefficients")):
            if not hasattr(self.limiter,attr):
                raise RuntimeError("No limiter stage data are available before the first completed step")
            q=fem.Function(self.V,name=f"density_{name}")
            q.x.array[:]=getattr(self.limiter,attr); q.x.scatter_forward()
            result[name]=DensityState(q,time_value,name)
        return result

    def limiter_history_summary(self) -> dict[str,object]:
        if not self.limiter_history: return {"steps":0}
        keys=("relative_l1_correction","raw_to_final_l2_correction","raw_negative_cell_average_fraction",
              "corrected_fraction","corrected_cell_average_fraction",
              "scaled_cell_fraction","projection_seconds","scaling_seconds")
        result={"steps":len(self.limiter_history)}
        for key in keys:
            values=np.array([getattr(r,key) for r in self.limiter_history])
            result[key]={"mean":float(values.mean()),"maximum":float(values.max()),"p95":float(np.quantile(values,.95))}
        result["steps_with_negative_raw_average"]=int(sum(r.raw_negative_cell_averages>0 for r in self.limiter_history))
        result["steps_with_scaling"]=int(sum(r.scaled_cells>0 for r in self.limiter_history))
        if any(r.raw_certificate_counts is not None for r in self.limiter_history):
            names=("CERTIFIED_NONNEGATIVE","WITNESSED_NEGATIVE","UNRESOLVED")
            result["raw_certificate_counts_by_status"]={name:{
                "mean":float(np.mean([r.raw_certificate_counts[name] for r in self.limiter_history])),
                "maximum":int(max(r.raw_certificate_counts[name] for r in self.limiter_history)),
                "final":int(self.limiter_history[-1].raw_certificate_counts[name]),
            } for name in names}
            result["maximum_certificate_depth"]=int(max(
                r.raw_certificate_max_depth or 0 for r in self.limiter_history
            ))
            result["raw_quadrature_negative_mass"]={
                "mean":float(np.mean([r.raw_quadrature_negative_mass or 0.0 for r in self.limiter_history])),
                "maximum":float(max(r.raw_quadrature_negative_mass or 0.0 for r in self.limiter_history)),
                "final":float(self.limiter_history[-1].raw_quadrature_negative_mass or 0.0),
            }
        return result

    def forecast(self, posterior: DensityState, t0: float, t1: float, progress: bool = False) -> DensityState:
        n_float = (t1-t0)/self.dt; n = round(n_float)
        if n < 0 or not math.isclose(n_float, n, abs_tol=1e-10):
            raise ValueError("Forecast interval must be a non-negative integer multiple of dt")
        state = posterior.copy("posterior")
        state.time = t0
        self.limiter_history=[]
        forecast_started=time.perf_counter()
        for k in range(n):
            state = self.step(state)
            if progress and (k == n-1 or (k+1) % max(1,n//10) == 0):
                d = self.diagnostics(state)
                if self.comm.rank == 0:
                    elapsed=time.perf_counter()-forecast_started
                    eta=elapsed/(k+1)*(n-k-1)
                    lim=d["limiter"] or {}
                    print(
                        f"step {k+1:5d}/{n} | t={state.time:.4f} | mass={d['mass']:.12f} | "
                        f"negative_mass={d['negative_mass']:.2e} | limiter={lim.get('corrected_fraction',0):.3f} | "
                        f"boundary={d['boundary_mass_fraction']:.2e} | KSP={self.last_linear['ksp_iterations']} | "
                        f"residual={self.last_linear['true_relative_residual']:.2e} | elapsed={elapsed:.1f}s | ETA={eta:.1f}s",
                        flush=True,
                    )
        return state

    def cell_averages(self, state: DensityState) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        n = self.mesh.topology.index_map(self.mesh.topology.dim).size_local
        avgs = np.array([self.limiter.cell_average(
            state.function.x.array[self.V.dofmap.cell_dofs(c)]) for c in range(n)])
        geom = self.mesh.geometry.x
        gdmap = self.mesh.geometry.dofmaps[0]
        mids = np.array([geom[gdmap[c]].mean(axis=0) for c in range(n)])
        return avgs, self.cell_volumes.copy(), mids

    def structured_export(self, state: DensityState, subcells_per_cell: int = 1) -> np.ndarray:
        """Export exact polynomial averages on a Cartesian voxel refinement.

        Tensor Gauss quadrature exactly integrates Qk on each affine subcell.
        Sufficient subcells retain the full within-cell polynomial through the
        inverse map while preserving mass conservatively.
        """
        s=int(subcells_per_cell)
        if s<1: raise ValueError("subcells_per_cell must be >= 1")
        av, vol, mids = self.cell_averages(state)
        average_matrix=self.limiter.subcell_average_matrix(s)
        local_values=np.stack([average_matrix@state.function.x.array[self.V.dofmap.cell_dofs(c)]
                               for c in range(len(av))])
        offsets=[(i,j,k) for i in range(s) for j in range(s) for k in range(s)]
        all_values = self.comm.gather(local_values, root=0); all_mid = self.comm.gather(mids, root=0)
        if self.comm.rank != 0:
            return np.empty((0,0,0))
        values = np.concatenate(all_values); xyz = np.concatenate(all_mid)
        nx, ny, nz = self.domain.cells
        arr = np.empty((nx*s,ny*s,nz*s), dtype=float)
        for cell_values, point in zip(values, xyz):
            idx=[]
            for d,(coordinates,count) in enumerate(zip(self.axis_coordinates,self.domain.cells)):
                idx.append(min(count-1,max(0,int(np.searchsorted(
                    coordinates,point[d],side="right"
                )-1))))
            for value,offset in zip(cell_values,offsets):
                arr[tuple(idx[d]*s+offset[d] for d in range(3))] = value
        return arr

    def common_grid_export(
        self, state: DensityState, common_shape: tuple[int, int, int]
    ) -> np.ndarray:
        """Export exact Qk averages to one aligned uniform comparison grid.

        Every graded cell edge must coincide with an edge of ``common_shape``.
        This makes the export conservative and avoids interpolation error in a
        graded-versus-uniform density comparison.
        """
        shape=tuple(int(value) for value in common_shape)
        if any(value<1 for value in shape):
            raise ValueError("common grid counts must all be positive")
        edge_indices=[]
        for axis,(coordinates,(lo,hi),count) in enumerate(zip(
            self.axis_coordinates,self.domain.bounds,shape
        )):
            indices=np.rint((coordinates-lo)*count/(hi-lo)).astype(int)
            reconstructed=lo+(hi-lo)*indices/count
            if not np.allclose(coordinates,reconstructed,rtol=0.0,atol=2.0e-12):
                raise ValueError(f"graded axis {axis} is not aligned to the common grid")
            if indices[0]!=0 or indices[-1]!=count or np.any(np.diff(indices)<1):
                raise ValueError(f"graded axis {axis} does not partition the common grid")
            edge_indices.append(indices)

        _,_,mids=self.cell_averages(state)
        matrix_cache: dict[tuple[int,int,int],np.ndarray]={}
        local=[]
        coefficients=state.function.x.array
        for cell,point in enumerate(mids):
            coarse=tuple(min(self.domain.cells[d]-1,max(0,int(np.searchsorted(
                self.axis_coordinates[d],point[d],side="right"
            )-1))) for d in range(3))
            starts=tuple(int(edge_indices[d][coarse[d]]) for d in range(3))
            spans=tuple(int(edge_indices[d][coarse[d]+1]-starts[d]) for d in range(3))
            matrix=matrix_cache.get(spans)
            if matrix is None:
                matrix=self.limiter.subcell_average_matrix_anisotropic(spans)
                matrix_cache[spans]=matrix
            values=(matrix@coefficients[self.V.dofmap.cell_dofs(cell)]).reshape(spans)
            local.append((starts,spans,values))
        gathered=self.comm.gather(local,root=0)
        if self.comm.rank!=0:
            return np.empty((0,0,0))
        result=np.empty(shape,dtype=float)
        for group in gathered:
            for starts,spans,values in group:
                slices=tuple(slice(starts[d],starts[d]+spans[d]) for d in range(3))
                result[slices]=values
        return result

    def diagnostics(self, state: DensityState) -> dict[str, object]:
        p = state.function; x = ufl.SpatialCoordinate(self.mesh)
        mass = self._integral(p)
        neg_mass = self._integral(ufl.max_value(-p, 0.0))
        l1 = self._integral(abs(p)); l2 = math.sqrt(max(0.0,self._integral(p*p)))
        mean = np.array([self._integral(x[i]*p)/mass for i in range(3)])
        cov = np.empty((3,3))
        for i in range(3):
            for j in range(3): cov[i,j]=self._integral((x[i]-mean[i])*(x[j]-mean[j])*p)/mass
        local_owned = p.x.array[: self.V.dofmap.index_map.size_local * self.V.dofmap.index_map_bs]
        av, _, mids = self.cell_averages(state)
        boundary = np.zeros(len(av),dtype=bool)
        for d,coordinates in enumerate(self.axis_coordinates):
            indices=np.searchsorted(coordinates,mids[:,d],side="right")-1
            boundary |= (indices==0)|(indices==len(coordinates)-2)
        boundary_mass = _global_sum(self.comm, float(np.dot(av[boundary], self.cell_volumes[boundary])))
        local_boundary_max=float(av[boundary].max()) if boundary.any() else 0.0
        boundary_max=_global_max(self.comm,local_boundary_max)
        cell_mass=np.maximum(av,0.0)*self.cell_volumes
        entropy_local=-float(np.sum(np.where(cell_mass>0,cell_mass*np.log(np.maximum(av,np.finfo(float).tiny)),0.0)))
        entropy=_global_sum(self.comm,entropy_local)/mass
        skew=[]; kurt=[]
        for i in range(3):
            # An unconstrained experimental projection can have a non-positive
            # second central moment.  Avoid underflowing the diagnostic
            # denominator while leaving the signed covariance itself visible.
            variance=max(cov[i,i],np.finfo(float).eps)
            skew.append(self._integral((x[i]-mean[i])**3*p)/mass/variance**1.5)
            kurt.append(self._integral((x[i]-mean[i])**4*p)/mass/variance**2-3.0)
        return {
            "time": state.time, "mass": mass, "negative_mass": neg_mass,
            "minimum": _global_min(self.comm,float(local_owned.min())),
            "maximum": _global_max(self.comm,float(local_owned.max())),
            "minimum_cell_average": _global_min(self.comm,float(av.min())),
            "mean": mean.tolist(), "covariance": cov.tolist(), "l1": l1, "l2": l2,
            "marginal_skewness":skew,"marginal_excess_kurtosis":kurt,
            "entropy_cell_average":entropy,"effective_support_volume":math.exp(entropy),
            "boundary_cell_mass": boundary_mass,
            "boundary_mass_fraction": boundary_mass/mass,
            "boundary_to_global_max_ratio":boundary_max/max(float(_global_max(self.comm,float(av.max()))),np.finfo(float).tiny),
            "linear_solver": dict(self.last_linear),
            "limiter": asdict(self.last_limiter) if self.last_limiter else None,
        }


@dataclass(frozen=True)
class ObservationModel:
    H: tuple[tuple[float, float, float], ...]
    R: tuple[tuple[float, ...], ...]
    name: str = "linear"

    @classmethod
    def named(cls, name: str, variance: float = 4.0) -> "ObservationModel":
        maps = {
            "x": ((1.,0.,0.),),
            "xz": ((1.,0.,0.),(0.,0.,1.)),
            "full": ((1.,0.,0.),(0.,1.,0.),(0.,0.,1.)),
        }
        H = maps[name]; R = tuple(tuple(variance if i==j else 0. for j in range(len(H))) for i in range(len(H)))
        return cls(H,R,name)

    def observe(self, state: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        H=np.asarray(self.H); R=np.asarray(self.R)
        return H@state + rng.multivariate_normal(np.zeros(H.shape[0]),R)


class BayesianAnalysis:
    def __init__(self, solver: FokkerPlanckSolver, observation_model: ObservationModel,
                 method: str = "projected", quadrature_degree: int = 10):
        if method not in {"nodal", "projected"}:
            raise ValueError("Bayesian analysis method must be 'nodal' or 'projected'")
        self.solver, self.observation_model = solver, observation_model
        self.method, self.quadrature_degree = method, int(quadrature_degree)
        if self.method == "projected":
            # Build the mass matrix and symbolic likelihood once.  Only the
            # forecast coefficients and observation constants change between
            # DA cycles.
            H=np.asarray(self.observation_model.H); R=np.asarray(self.observation_model.R)
            inv=np.linalg.inv(R); norm=(2*np.pi)**(-H.shape[0]/2)/math.sqrt(float(np.linalg.det(R)))
            self._source=fem.Function(solver.V)
            self._observation=[fem.Constant(solver.mesh,PETSc.ScalarType(0.0)) for _ in range(H.shape[0])]
            x=ufl.SpatialCoordinate(solver.mesh)
            residual=ufl.as_vector([
                self._observation[i]-sum(float(H[i,j])*x[j] for j in range(3))
                for i in range(H.shape[0])
            ])
            likelihood=norm*ufl.exp(-.5*ufl.dot(residual,ufl.dot(ufl.as_matrix(inv.tolist()),residual)))
            trial,test=ufl.TrialFunction(solver.V),ufl.TestFunction(solver.V)
            dxq=ufl.Measure("dx",domain=solver.mesh,metadata={"quadrature_degree":self.quadrature_degree})
            self._analysis_a=fem.form(trial*test*dxq)
            self._analysis_L=fem.form(likelihood*self._source*test*dxq)
            self._analysis_A=assemble_matrix(self._analysis_a); self._analysis_A.assemble()
            self._analysis_b=create_vector(solver.V); self._analysis_x=create_vector(solver.V)
            self._analysis_ksp=PETSc.KSP().create(solver.comm)
            self._analysis_ksp.setOperators(self._analysis_A); self._analysis_ksp.setType("cg")
            self._analysis_ksp.setTolerances(rtol=1.e-13,atol=1.e-15,max_it=1000)
            self._analysis_ksp.setErrorIfNotConverged(True)
            self._analysis_ksp.getPC().setType("jacobi"); self._analysis_ksp.setUp()

    def update(self, forecast: DensityState, observation: np.ndarray) -> tuple[DensityState, dict[str,object]]:
        H=np.asarray(self.observation_model.H); R=np.asarray(self.observation_model.R); inv=np.linalg.inv(R)
        norm=(2*np.pi)**(-H.shape[0]/2)/math.sqrt(float(np.linalg.det(R)))
        if self.method == "nodal":
            # This is nodal interpolation of L(x)p_h(x), not an L2 projection.
            out=forecast.copy("posterior_nodal_product")
            coords=self.solver.V.tabulate_dof_coordinates()
            residual=np.asarray(observation)[None,:] - coords@H.T
            likelihood=norm*np.exp(-0.5*np.einsum("ni,ij,nj->n",residual,inv,residual))
            n_owned=self.solver.V.dofmap.index_map.size_local*self.solver.V.dofmap.index_map_bs
            out.function.x.array[:n_owned] *= likelihood[:n_owned]
            out.function.x.scatter_forward()
        else:
            self._source.x.array[:]=forecast.function.x.array; self._source.x.scatter_forward()
            for value,constant in zip(np.asarray(observation,dtype=float),self._observation):
                constant.value=PETSc.ScalarType(value)
            with self._analysis_b.localForm() as local: local.set(0.0)
            assemble_vector(self._analysis_b,self._analysis_L)
            self._analysis_b.ghostUpdate(addv=PETSc.InsertMode.ADD,mode=PETSc.ScatterMode.REVERSE)
            with self._analysis_x.localForm() as local: local.set(0.0)
            self._analysis_ksp.solve(self._analysis_b,self._analysis_x)
            self._analysis_x.ghostUpdate(addv=PETSc.InsertMode.INSERT,mode=PETSc.ScatterMode.FORWARD)
            q=fem.Function(self.solver.V,name="posterior_projected_product")
            assign(self._analysis_x,q); q.x.scatter_forward()
            out=DensityState(q,forecast.time,"posterior_projected_product")
        evidence=self.solver.mass(out)
        if not np.isfinite(evidence) or evidence <= np.finfo(float).tiny:
            raise FloatingPointError(f"Bayesian evidence is invalid: {evidence}")
        out.function.x.array[:] /= evidence; out.function.x.scatter_forward()
        report=self.solver.limiter.apply(out)
        mass=self.solver.mass(out)
        if abs(mass-1)>1e-10 or report.minimum_after < -1e-13:
            raise FloatingPointError("Analysis update violated probability invariants")
        return out, {"method":self.method,"quadrature_degree":self.quadrature_degree,
            "evidence": evidence, "mass": mass, "minimum": report.minimum_after,
            "limiter_relative_l1_correction":report.relative_l1_correction,
            "projection_ksp_iterations":(int(self._analysis_ksp.getIterationNumber())
                if self.method=="projected" else None)}


class TruthSimulator:
    def __init__(self, model: Lorenz63Model, dt: float = 2.5e-4):
        self.model, self.dt = model, float(dt)

    def simulate(self, initial: Iterable[float], times: Iterable[float], seed: int) -> np.ndarray:
        times=np.asarray(tuple(times),dtype=float); rng=np.random.default_rng(seed); B=np.asarray(self.model.B)
        x=np.asarray(tuple(initial),dtype=float); out=np.empty((len(times),3)); t=0.0
        for j,target in enumerate(times):
            while t < target-1e-14:
                h=min(self.dt,target-t)
                x=x+self.model.drift_numpy(x)*h+B@rng.normal(size=3)*math.sqrt(h); t+=h
            out[j]=x
        return out


def solver_metadata(solver: FokkerPlanckSolver) -> dict[str, object]:
    D=solver.model.diffusion
    corners=np.array(np.meshgrid(*[(lo,hi) for lo,hi in solver.domain.bounds],indexing="ij")).reshape(3,-1).T
    max_speed=float(np.linalg.norm(solver.model.drift_numpy(corners),axis=1).max())
    widths=np.array([(hi-lo)/n for (lo,hi),n in zip(solver.domain.bounds,solver.domain.cells)])
    kappa=float(np.linalg.eigvalsh(D).max())
    pe=float(max_speed*widths.max()/(2*kappa)) if kappa>0 else math.inf
    global_dofs=int(solver.comm.allreduce(solver.V.dofmap.index_map.size_local,op=MPI.SUM))
    return {
        "software": {"dolfinx": dolfinx.__version__, "petsc": ".".join(map(str,PETSc.Sys.getVersion()))},
        "sde": "dX=f(X)dt+B dW; f=(sigma(y-x), x(rho-z)-y, xy-beta z)",
        "fpe": "partial_t p + div(f p - D grad p)=0; D=0.5 B B^T",
        "boundary": "total reflecting/no-flux (f p-D grad p).n=0 on finite box",
        "model": asdict(solver.model), "diffusion": D.tolist(), "domain": asdict(solver.domain),
        "dt": solver.dt, "space": f"discontinuous tensor-product degree {solver.degree} (DG/Q{solver.degree})",
        "linear_solver_tolerances": {
            "rtol": solver.ksp_rtol, "atol": solver.ksp_atol,
        },
        "fluxes": "upwind advection; symmetric interior penalty diffusion",
        "time_method": "backward Euler" if solver.theta==1.0 else f"theta method (theta={solver.theta})",
        "positivity": {
            "method": "constrained L2 projection of cell averages, then Bernstein-coefficient scaling",
            "guarantee": f"global mass preserved; all Q{solver.degree} Bernstein coefficients on the limiter control subcells are nonnegative; hence the polynomial is nonnegative throughout each affine axis-aligned hexahedron",
            "control_subdivisions_per_axis":solver.limiter.control_subdivisions,
            "scope": "postprocessed state at every completed timestep; not the unlimited algebraic solution",
            "enabled_during_forecast":solver.apply_positivity,
        },
        "global_cells": int(np.prod(solver.domain.cells)), "global_dofs":global_dofs,
        "severity":{"corner_sample_max_drift_speed":max_speed,"cell_widths":widths.tolist(),"max_cell_Peclet_estimate":pe},
        "resource_estimates":{"minimum_vector_memory_bytes":global_dofs*8*5,
            "single_float32_voxel_tensor_bytes":int(np.prod(solver.domain.cells))*4,
            "note":"Sparse matrix/preconditioner memory is implementation-dependent and additional."},
    }


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2),encoding="utf-8")
