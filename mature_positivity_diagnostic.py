#!/usr/bin/env python3
"""Compare mature-state positivity treatments on identical raw Q2 polynomials."""
from __future__ import annotations

import argparse
import json
import math
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np
from mpi4py import MPI

from lorenz_fpe import DensityState, Domain, LocalProjectionFokkerPlanckSolver
from lorenz_fpe.core import write_json
from lorenz_fpe.local_projection import LocalPolynomialProjector
from same_mesh_q2_study import _model, _sha256


def _mixture_state(solver, path: Path, quadrature_degree: int) -> DensityState:
    mixture=json.loads(path.read_text())
    expression=sum(
        float(weight)*solver.gaussian_expression(mean,np.asarray(covariance,dtype=float))
        for weight,mean,covariance in zip(
            mixture["weights"],mixture["means"],mixture["covariances"]
        )
    )
    return solver.project_expression(
        expression,"raw_mature_mixture",quadrature_degree,True,False
    )


def _classification(solver, state: DensityState, depth: int) -> tuple[dict[str,int],list[str]]:
    statuses=[]
    for dofs in solver.limiter.cell_dofs:
        statuses.append(str(solver.limiter.classify_coefficients(
            state.function.x.array[dofs],max_depth=depth
        )["status"]))
    names=("CERTIFIED_NONNEGATIVE","WITNESSED_NEGATIVE","UNRESOLVED")
    counts={name:int(solver.comm.allreduce(statuses.count(name),op=MPI.SUM)) for name in names}
    return counts,statuses


def _distribution_change(solver, raw: DensityState, corrected: DensityState) -> dict[str,object]:
    l1,l2=solver.limiter._difference_norms(
        raw.function.x.array,corrected.function.x.array
    )
    raw_diag=solver.diagnostics(raw); corrected_diag=solver.diagnostics(corrected)
    raw_grid=solver.structured_export(raw,1)
    corrected_grid=solver.structured_export(corrected,1)
    if solver.comm.rank:
        return {}
    volume=solver.domain.volume/raw_grid.size
    marginal_tvs=[]
    for axis in range(3):
        other=tuple(i for i in range(3) if i!=axis)
        marginal_tvs.append(float(
            0.5*np.abs((raw_grid-corrected_grid).sum(axis=other)*volume).sum()
        ))
    nx=raw_grid.shape[0]
    x=np.linspace(solver.domain.bounds[0][0],solver.domain.bounds[0][1],nx,endpoint=False)
    x+=(solver.domain.bounds[0][1]-solver.domain.bounds[0][0])/(2*nx)
    lobe_change=max(
        abs(float((raw_grid[x>0]-corrected_grid[x>0]).sum()*volume)),
        abs(float((raw_grid[x<0]-corrected_grid[x<0]).sum()*volume)),
    )
    return {
        "l1_correction":l1,"l2_correction":l2,
        "mass_change":float(corrected_diag["mass"]-raw_diag["mass"]),
        "covariance_frobenius_change":float(np.linalg.norm(
            np.asarray(corrected_diag["covariance"])-np.asarray(raw_diag["covariance"]),"fro"
        )),
        "marginal_total_variation_changes":marginal_tvs,
        "maximum_lobe_probability_change":lobe_change,
    }


def _evaluate_snapshot(solver, raw: DensityState, label: str,
                       current_depth: int, deep_depth: int) -> dict[str,object] | None:
    current_counts,current_status=_classification(solver,raw,current_depth)
    deep_counts,deep_status=_classification(solver,raw,deep_depth)
    rescued_local=sum(
        a!="CERTIFIED_NONNEGATIVE" and b=="CERTIFIED_NONNEGATIVE"
        for a,b in zip(current_status,deep_status)
    )
    rescued=int(solver.comm.allreduce(rescued_local,op=MPI.SUM))

    solver.limiter.certificate_max_depth=current_depth
    current_projector=LocalPolynomialProjector(
        solver.limiter,optimizer_backend="osqp",optimizer_ftol=1.0e-10,
        maximum_iterations=10000,
    )
    current,current_report=current_projector.project_state(
        raw,repair_cell_averages=True,adaptive_skip=True
    )
    current_change=_distribution_change(solver,raw,current)

    solver.limiter.certificate_max_depth=deep_depth
    deep_projector=LocalPolynomialProjector(
        solver.limiter,optimizer_backend="osqp",optimizer_ftol=1.0e-10,
        maximum_iterations=10000,
    )
    deep,deep_report=deep_projector.project_state(
        raw,repair_cell_averages=True,adaptive_skip=True
    )
    deep_change=_distribution_change(solver,raw,deep)

    scalar=raw.copy("scalar_limited")
    scalar_report=asdict(solver.limiter.apply(scalar))
    scalar_change=_distribution_change(solver,raw,scalar)
    solver.limiter.certificate_max_depth=current_depth
    if solver.comm.rank:
        return None
    return {
        "label":label,"time":raw.time,
        "classification":{"depth_current":current_depth,"current":current_counts,
                          "depth_deep":deep_depth,"deep":deep_counts,
                          "cells_rescued_by_deeper_certification":rescued},
        "current_local_qp":{"report":current_report,"change":current_change},
        "deep_certificate_local_qp":{"report":deep_report,"change":deep_change},
        "scalar_limiter":{"report":scalar_report,"change":scalar_change},
    }


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--mixture",type=Path,required=True)
    parser.add_argument("--expected-mixture-sha256",required=True)
    parser.add_argument("--cells",type=int,nargs=3,required=True)
    parser.add_argument("--dt",type=float,required=True)
    parser.add_argument("--times",type=float,nargs="+",required=True)
    parser.add_argument("--noise-matrix",type=float,nargs=9,required=True)
    parser.add_argument("--quadrature-degree",type=int,default=14)
    parser.add_argument("--current-depth",type=int,default=4)
    parser.add_argument("--deep-depth",type=int,default=8)
    args=parser.parse_args()
    mixture_sha256=_sha256(args.mixture)
    if mixture_sha256!=args.expected_mixture_sha256:
        raise ValueError("Mature mixture hash does not match the predeclared artifact")
    comm=MPI.COMM_WORLD
    if comm.rank==0:
        args.output.mkdir(parents=True,exist_ok=False)
    comm.barrier()
    solver=LocalProjectionFokkerPlanckSolver(
        _model(args.noise_matrix),Domain(cells=tuple(args.cells)),args.dt,
        theta=0.5,degree=2,ksp_rtol=1.0e-12,ksp_atol=1.0e-15,
        certificate_mode="fixed",certificate_max_depth=args.current_depth,
        certificate_diagnostics=True,local_optimizer_backend="osqp",
        local_optimizer_ftol=1.0e-10,local_maximum_iterations=10000,
    )
    raw_initial=_mixture_state(solver,args.mixture,args.quadrature_degree)
    snapshots=[]; started=time.perf_counter()
    item=_evaluate_snapshot(
        solver,raw_initial,"initialization",args.current_depth,args.deep_depth
    )
    if item is not None: snapshots.append(item)
    solver.limiter.certificate_max_depth=args.current_depth
    state,initial_report=solver.local_projector.project_state(
        raw_initial,repair_cell_averages=True,adaptive_skip=True
    )
    targets=sorted(set(float(value) for value in args.times)); target_steps={
        round(value/args.dt):value for value in targets
    }
    if any(step<1 or not math.isclose(step*args.dt,value,abs_tol=1.0e-13)
           for step,value in target_steps.items()):
        raise ValueError("Every diagnostic time must be a positive integer multiple of dt")
    for step in range(1,max(target_steps)+1):
        state=solver.step(state)
        if step in target_steps:
            raw=solver.last_unlimited_state
            if raw is None: raise RuntimeError("Missing unlimited snapshot")
            item=_evaluate_snapshot(
                solver,raw,f"forecast_step_{step}",args.current_depth,args.deep_depth
            )
            if item is not None: snapshots.append(item)
        if comm.rank==0 and (step%max(1,max(target_steps)//10)==0 or step==max(target_steps)):
            print(f"step {step}/{max(target_steps)} elapsed={time.perf_counter()-started:.1f}s",flush=True)
    if comm.rank==0:
        report={
            "configuration":{"cells":list(args.cells),"dt":args.dt,"times":targets,
                "mpi_ranks":comm.size,"current_depth":args.current_depth,
                "deep_depth":args.deep_depth,"mixture_sha256":mixture_sha256,
                "noise_matrix":np.asarray(args.noise_matrix).reshape(3,3).tolist()},
            "initial_baseline_projection":initial_report,"snapshots":snapshots,
            "wall_seconds":time.perf_counter()-started,
            "interpretation":"Offline same-raw-polynomial diagnostic; no method certification decision.",
        }
        write_json(args.output/"report.json",report)
        print(args.output/"report.json",flush=True)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
