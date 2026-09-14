#!/usr/bin/env python3
"""Single-step Bernstein-DOF convex-limiting diagnostic for mature Q2 states."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
from mpi4py import MPI

from lorenz_fpe import DensityState, Domain, FokkerPlanckSolver, LocalProjectionFokkerPlanckSolver
from lorenz_fpe.core import write_json
from lorenz_fpe.local_projection import LocalPolynomialProjector
from mature_positivity_diagnostic import _distribution_change, _mixture_state
from same_mesh_q2_study import _model, _sha256


def _simplex_projection(values: np.ndarray, target: float, lower: float) -> np.ndarray:
    """Euclidean projection onto {x >= lower, sum(x) = target}."""
    values=np.asarray(values,dtype=float)
    available=float(target-lower*len(values))
    if available < -1.0e-13*max(1.0,abs(target)):
        raise ValueError("Infeasible Bernstein-DOF lower bound")
    shifted=values-lower
    if available <= 0.0:
        return np.full_like(values,target/len(values))
    ordered=np.sort(shifted)[::-1]
    cumulative=np.cumsum(ordered)-available
    indices=np.arange(1,len(values)+1)
    active=np.nonzero(ordered-cumulative/indices>0.0)[0]
    rho=int(active[-1]) if len(active) else 0
    threshold=float(cumulative[rho]/(rho+1))
    projected=np.maximum(shifted-threshold,0.0)+lower
    projected[int(np.argmax(projected))] += target-float(projected.sum())
    return projected


def _repair_cell_averages(solver, raw: DensityState) -> tuple[DensityState,np.ndarray]:
    output=raw.copy("common_positive_cell_averages")
    local=np.asarray([
        solver.limiter.cell_average(output.function.x.array[dofs])
        for dofs in solver.limiter.cell_dofs
    ])
    gathered=solver.comm.gather(local,root=0)
    volumes=solver.comm.gather(solver.limiter.cell_volumes,root=0)
    if solver.comm.rank==0:
        repaired=solver.limiter.project_cell_averages(
            np.concatenate(gathered),np.concatenate(volumes)
        )
        chunks=[]; offset=0
        for values in gathered:
            chunks.append(repaired[offset:offset+len(values)])
            offset+=len(values)
    else:
        chunks=None
    target=np.asarray(solver.comm.scatter(chunks,root=0),dtype=float)
    for cell,dofs in enumerate(solver.limiter.cell_dofs):
        values=output.function.x.array[dofs].copy()
        values += target[cell]-solver.limiter.cell_average(values)
        output.function.x.array[dofs]=values
    output.function.x.scatter_forward()
    return output,target


def _dof_convex_limit(solver, raw: DensityState) -> tuple[DensityState,dict[str,object]]:
    """Limit whole-cell Bernstein DOFs by conservative simplex projection."""
    started=time.perf_counter()
    output,target=_repair_cell_averages(solver,raw)
    transform=np.asarray(solver.limiter.to_whole_bernstein,dtype=float)
    inverse=np.linalg.inv(transform)
    bernstein_average=np.full(transform.shape[0],1.0/transform.shape[0])
    represented_average=solver.limiter.average_weights@inverse
    if not np.allclose(represented_average,bernstein_average,rtol=0.0,atol=2.0e-13):
        raise RuntimeError("Whole-cell Bernstein coefficients do not have uniform integral weights")
    changed=0; probability=0.0; minimum=np.inf
    for cell,dofs in enumerate(solver.limiter.cell_dofs):
        coefficients=output.function.x.array[dofs].copy()
        control=transform@coefficients
        average=float(target[cell])
        scale=max(float(np.max(np.abs(control))),abs(average),np.finfo(float).tiny)
        margin=256.0*np.finfo(float).eps*scale
        if float(control.min()) < margin:
            projected=_simplex_projection(control,27.0*average,margin)
            coefficients=inverse@projected
            coefficients += average-solver.limiter.cell_average(coefficients)
            output.function.x.array[dofs]=coefficients
            changed+=1
            probability+=solver.limiter.cell_volumes[cell]*average
        minimum=min(minimum,float((transform@output.function.x.array[dofs]).min()))
    output.function.x.scatter_forward()
    classification=solver.limiter._classification_summary(output.function.x.array)
    total_cells=int(solver.comm.allreduce(solver.limiter.n_local_cells,op=MPI.SUM))
    report={
        "method":"whole-cell Bernstein-DOF conservative simplex convex limiter",
        "architecture":"positive cell-average baseline plus coefficient-local antidiffusive recovery",
        "constraint_scope":"Q2 whole-cell Bernstein DOFs; sufficient whole-cell positivity",
        "changed_cells":int(solver.comm.allreduce(changed,op=MPI.SUM)),
        "total_cells":total_cells,
        "projected_probability_mass":float(solver.comm.allreduce(probability,op=MPI.SUM)),
        "minimum_whole_cell_bernstein_coefficient":float(
            solver.comm.allreduce(minimum,op=MPI.MIN)
        ),
        "whole_cell_positivity_certified":classification["counts"]["CERTIFIED_NONNEGATIVE"]==total_cells,
        "final_certificate_counts":classification["counts"],
        "final_quadrature_negative_mass":classification["quadrature_negative_mass"],
        "wall_seconds":float(solver.comm.allreduce(time.perf_counter()-started,op=MPI.MAX)),
    }
    return output,report


def _evaluate(solver,raw: DensityState,label: str) -> dict[str,object] | None:
    projector=LocalPolynomialProjector(
        solver.limiter,optimizer_backend="osqp",optimizer_ftol=1.0e-10,
        maximum_iterations=10000,
    )
    qp,qp_report=projector.project_state(raw,repair_cell_averages=True,adaptive_skip=True)
    qp_change=_distribution_change(solver,raw,qp)
    dof,dof_report=_dof_convex_limit(solver,raw)
    dof_change=_distribution_change(solver,raw,dof)
    if solver.comm.rank:
        return None
    qp_l1=float(qp_change["l1_correction"])
    dof_l1=float(dof_change["l1_correction"])
    return {
        "label":label,"time":raw.time,
        "current_local_qp":{"report":qp_report,"change":qp_change},
        "dof_convex":{"report":dof_report,"change":dof_change},
        "dof_to_qp_l1_ratio":dof_l1/qp_l1 if qp_l1>0.0 else None,
        "continuation_gate_below_half_qp":dof_l1<0.5*qp_l1,
        "mass_gate":abs(float(dof_change["mass_change"]))<=1.0e-12,
        "statistics_gates":{
            "covariance_no_worse_than_qp":float(dof_change["covariance_frobenius_change"])
                <=float(qp_change["covariance_frobenius_change"])+1.0e-12,
            "lobe_no_worse_than_qp":float(dof_change["maximum_lobe_probability_change"])
                <=float(qp_change["maximum_lobe_probability_change"])+1.0e-12,
            "marginals_no_worse_than_qp":max(dof_change["marginal_total_variation_changes"])
                <=max(qp_change["marginal_total_variation_changes"])+1.0e-12,
        },
    }


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--mixture",type=Path,required=True)
    parser.add_argument("--expected-mixture-sha256",required=True)
    parser.add_argument("--cells",type=int,nargs=3,required=True)
    parser.add_argument("--dt",type=float,required=True)
    parser.add_argument("--noise-matrix",type=float,nargs=9,required=True)
    parser.add_argument("--quadrature-degree",type=int,default=14)
    args=parser.parse_args()
    mixture_hash=_sha256(args.mixture)
    if mixture_hash!=args.expected_mixture_sha256:
        raise ValueError("Mature mixture hash does not match the predeclared artifact")
    comm=MPI.COMM_WORLD
    if comm.rank==0:
        args.output.mkdir(parents=True,exist_ok=False)
    comm.barrier()
    solver=LocalProjectionFokkerPlanckSolver(
        _model(args.noise_matrix),Domain(cells=tuple(args.cells)),args.dt,
        theta=0.5,degree=2,ksp_rtol=1.0e-12,ksp_atol=1.0e-15,
        certificate_mode="fixed",certificate_max_depth=4,
        certificate_diagnostics=True,local_optimizer_backend="osqp",
        local_optimizer_ftol=1.0e-10,local_maximum_iterations=10000,
    )
    started=time.perf_counter()
    raw_initial=_mixture_state(solver,args.mixture,args.quadrature_degree)
    initial=_evaluate(solver,raw_initial,"mature_initial_projection")
    positive_initial,initial_report=solver.local_projector.project_state(
        raw_initial,repair_cell_averages=True,adaptive_skip=True
    )
    raw_step=FokkerPlanckSolver.step(solver,positive_initial)
    dynamic=_evaluate(solver,raw_step,"one_q2_cn_step_from_common_positive_p0")
    if comm.rank==0:
        snapshots=[initial,dynamic]
        all_gates=all(
            item["continuation_gate_below_half_qp"] and item["mass_gate"]
            and all(item["statistics_gates"].values())
            and item["dof_convex"]["report"]["whole_cell_positivity_certified"]
            and item["dof_convex"]["report"]["final_quadrature_negative_mass"]==0.0
            for item in snapshots
        )
        report={
            "classification":("PURSUE_DOF_CONVEX_UPDATE" if all_gates
                              else "DO_NOT_PURSUE_THIS_DOF_CONVEX_PROTOTYPE"),
            "all_predeclared_gates_passed":all_gates,
            "configuration":{"cells":list(args.cells),"dt":args.dt,"mpi_ranks":comm.size,
                "mixture_sha256":mixture_hash,"noise_matrix":np.asarray(
                    args.noise_matrix).reshape(3,3).tolist()},
            "common_positive_initial_projection":initial_report,
            "snapshots":snapshots,
            "thresholds":{"maximum_dof_to_qp_l1_ratio":0.5,"maximum_mass_change":1.0e-12,
                "statistics_change_must_not_exceed_current_qp":True,
                "whole_cell_positivity_and_zero_negative_mass_required":True},
            "scope":"Offline initial/one-step diagnostic only; no certification or dataset authorization.",
            "wall_seconds":time.perf_counter()-started,
        }
        write_json(args.output/"report.json",report)
        print(args.output/"report.json",flush=True)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
