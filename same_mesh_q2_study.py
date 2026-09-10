#!/usr/bin/env python3
"""Run the predeclared same-mesh Q1/Q2 positivity falsification study."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import resource
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np
from mpi4py import MPI

from lorenz_fpe import Domain, FokkerPlanckSolver, Lorenz63Model
from lorenz_fpe.core import write_json
from lorenz_fpe.validation import _propagate_particles, covariance_accuracy


def _sha256(path: Path) -> str:
    digest=hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda:source.read(1024*1024),b""):
            digest.update(block)
    return digest.hexdigest()


def _marginal_tv(cell_averages: np.ndarray, particles: np.ndarray,
                 domain: Domain) -> list[float]:
    probability=cell_averages*domain.volume/np.prod(domain.cells)
    result=[]
    for axis,((lo,hi),count) in enumerate(zip(domain.bounds,domain.cells)):
        other=tuple(i for i in range(3) if i!=axis)
        numerical=probability.sum(axis=other)
        sampled=np.histogram(particles[:,axis],bins=count,range=(lo,hi))[0]/len(particles)
        result.append(float(.5*np.abs(numerical-sampled).sum()))
    return result


def prepare_reference(args: argparse.Namespace) -> None:
    if MPI.COMM_WORLD.size!=1:
        raise SystemExit("reference preparation must run on one rank")
    output=args.output.resolve(); output.mkdir(parents=True,exist_ok=False)
    domain=Domain(cells=tuple(args.cells)); model=Lorenz63Model()
    solver=FokkerPlanckSolver(model,domain,args.dt,degree=1)
    initial=solver.gaussian_projected(
        (1.0,1.0,20.0),np.diag([4.0,4.0,9.0]),quadrature_degree=14,
        apply_limiter=True,
    )
    grid=solver.structured_export(initial,3)
    grid_path=output/"initial_q1_subcell_averages.npy"; np.save(grid_path,grid)
    rng=np.random.default_rng(args.seed)
    particles0=solver.sample_density(initial,args.particles,rng)
    sampling=dict(solver.last_sampling_report)
    started=time.perf_counter()
    particles=_propagate_particles(model,particles0,args.t_final,args.mc_dt,rng)
    propagation_seconds=time.perf_counter()-started
    particle_path=output/"mc_final_particles.npy"; np.save(particle_path,particles)
    report={
        "configuration":{"cells":list(args.cells),"dt":args.dt,"t_final":args.t_final,
            "particles":args.particles,"mc_dt":args.mc_dt,"seed":args.seed},
        "initialization":solver.last_initialization_report,
        "initial_diagnostics":solver.diagnostics(initial),"native_sampling":sampling,
        "mc":{"mean":particles.mean(0).tolist(),"covariance":np.cov(particles,rowvar=False).tolist(),
            "propagation_seconds":propagation_seconds},
        "artifacts":{
            grid_path.name:{"sha256":_sha256(grid_path),"bytes":grid_path.stat().st_size},
            particle_path.name:{"sha256":_sha256(particle_path),"bytes":particle_path.stat().st_size},
        },
    }
    write_json(output/"reference.json",report)
    print(output/"reference.json",flush=True)


def run_forecast(args: argparse.Namespace) -> None:
    comm=MPI.COMM_WORLD; rank=comm.rank
    output=args.output.resolve()
    if rank==0:
        output.mkdir(parents=True,exist_ok=False)
    comm.barrier()
    domain=Domain(cells=tuple(args.cells)); model=Lorenz63Model()
    solver=FokkerPlanckSolver(
        model,domain,args.dt,degree=args.degree,certificate_mode=args.certificate_mode,
        certificate_max_depth=args.certificate_max_depth,
        certificate_diagnostics=args.degree>=2,
    )
    grid=np.load(args.initial_grid)
    initial=solver.from_structured(grid,apply_limiter=False)
    initial_diagnostics=solver.diagnostics(initial)
    represented=solver.structured_export(initial,3)
    if rank==0:
        embedding={"maximum_subcell_average_error":float(np.max(np.abs(represented-grid))),
            "relative_l2_subcell_average_error":float(
                np.linalg.norm(represented-grid)/max(np.linalg.norm(grid),np.finfo(float).tiny)
            )}
    else:
        embedding=None

    steps=round(args.t_final/args.dt)
    if not math.isclose(steps*args.dt,args.t_final,abs_tol=1e-14):
        raise ValueError("t_final must be an integer multiple of dt")
    n_owned=solver.V.dofmap.index_map.size_local*solver.V.dofmap.index_map_bs
    raw_path=None; raw_archive=None
    if args.degree>=2:
        raw_path=output/f"raw_before_correction_rank{rank:04d}.npy"
        raw_archive=np.lib.format.open_memmap(
            raw_path,mode="w+",dtype=np.float64,shape=(steps,n_owned)
        )
    state=initial; started=time.perf_counter(); step_seconds=[]
    for step in range(steps):
        step_started=time.perf_counter(); state=solver.step(state)
        step_seconds.append(time.perf_counter()-step_started)
        if raw_archive is not None:
            raw_archive[step]=solver.limiter.last_raw_coefficients[:n_owned]
            if (step+1)%10==0:
                raw_archive.flush()
        if rank==0 and ((step+1)%max(1,steps//10)==0 or step+1==steps):
            elapsed=time.perf_counter()-started
            print(f"{args.branch}: step {step+1}/{steps}, elapsed={elapsed:.1f}s",flush=True)
    if raw_archive is not None:
        raw_archive.flush(); del raw_archive
    forecast_seconds=time.perf_counter()-started

    stages=solver.limiter_stage_states(state.time)
    stage_diagnostics={name:solver.diagnostics(stage) for name,stage in stages.items()}
    stage_cells={name:solver.structured_export(stage,1) for name,stage in stages.items()}
    particles=np.load(args.mc_particles) if rank==0 else None
    if rank==0:
        comparisons={name:{
            "covariance_accuracy":covariance_accuracy(
                np.asarray(stage_diagnostics[name]["covariance"]),particles,
                args.seed+1000+index,args.bootstrap,
            ),
            "marginal_total_variation_distance":_marginal_tv(values,particles,domain),
        } for index,(name,values) in enumerate(stage_cells.items())}
    else:
        comparisons=None

    artifacts=[]
    if raw_path is not None:
        records=solver.limiter.classification_records(solver.limiter.last_raw_coefficients)
        records_path=output/f"final_raw_cell_classification_rank{rank:04d}.json"
        records_path.write_text(json.dumps(records,separators=(",",":")),encoding="utf-8")
        artifacts.extend([raw_path,records_path])
    local_artifacts=[{"path":path.name,"sha256":_sha256(path),"bytes":path.stat().st_size}
                     for path in artifacts]
    gathered_artifacts=comm.gather(local_artifacts,root=0)
    peak_rss_kib=comm.gather(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,root=0)
    maximum_step_seconds=comm.allreduce(max(step_seconds),op=MPI.MAX)
    mean_step_seconds=comm.allreduce(sum(step_seconds)/len(step_seconds),op=MPI.MAX)

    if rank==0:
        history=solver.limiter_history_summary()
        corrected=comparisons["final"]["covariance_accuracy"]
        mean_l1=history["relative_l1_correction"]["mean"]
        maximum_l1=history["relative_l1_correction"]["maximum"]
        report={
            "branch":args.branch,
            "configuration":{"cells":list(args.cells),"degree":args.degree,"dt":args.dt,
                "t_final":args.t_final,"mpi_ranks":comm.size,
                "certificate_mode":args.certificate_mode,
                "certificate_max_depth":args.certificate_max_depth,
                "bootstrap_replicates":args.bootstrap,"seed":args.seed},
            "initial_embedding":embedding,"initial_diagnostics":initial_diagnostics,
            "final_stage_diagnostics":stage_diagnostics,"comparisons_to_common_mc":comparisons,
            "limiter_history":history,
            "limiter_steps":[asdict(item) for item in solver.limiter_history],
            "timing":{"forecast_seconds":forecast_seconds,
                "maximum_step_seconds":maximum_step_seconds,"mean_step_seconds":mean_step_seconds,
                "matrix_assembly_seconds":solver.matrix_assembly_seconds},
            "resources":{"maximum_rank_peak_rss_kib":int(max(peak_rss_kib)),
                "raw_archive_total_bytes":int(sum(
                    item["bytes"] for group in gathered_artifacts for item in group
                    if item["path"].startswith("raw_before")
                ))},
            "branch_gates":{"corrected_covariance_at_most_0_03":
                corrected["normalized_frobenius_error"]<=.03,
                "corrected_covariance_at_most_five_mc_p95":
                corrected["pde_error_to_mc_noise_p95_ratio"]<=5.0,
                "limiter_mean_relative_l1_at_most_0_001":mean_l1<=.001,
                "limiter_max_relative_l1_at_most_0_005":maximum_l1<=.005,
                "mass_error_at_most_1e_10":abs(stage_diagnostics["final"]["mass"]-1.0)<=1e-10,
                "negative_mass_at_most_1e_13":stage_diagnostics["final"]["negative_mass"]<=1e-13},
            "artifacts":[item for group in gathered_artifacts for item in group],
            "interpretation":"Branch-local gates only; degree and timestep decisions require the aggregate comparison.",
        }
        write_json(output/"report.json",report)
        print(output/"report.json",flush=True)


def parser() -> argparse.ArgumentParser:
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="command",required=True)
    common=argparse.ArgumentParser(add_help=False)
    common.add_argument("--cells",type=int,nargs=3,default=(30,36,36))
    common.add_argument("--dt",type=float,default=.000625)
    common.add_argument("--t-final",type=float,default=.05)
    common.add_argument("--seed",type=int,default=20260910)
    common.add_argument("--output",type=Path,required=True)
    prep=sub.add_parser("prepare",parents=[common])
    prep.add_argument("--particles",type=int,default=200000)
    prep.add_argument("--mc-dt",type=float,default=.000125)
    run=sub.add_parser("forecast",parents=[common])
    run.add_argument("--branch",required=True)
    run.add_argument("--degree",type=int,choices=(1,2),required=True)
    run.add_argument("--certificate-mode",choices=("fixed","adaptive"),default="fixed")
    run.add_argument("--certificate-max-depth",type=int,default=4)
    run.add_argument("--initial-grid",type=Path,required=True)
    run.add_argument("--mc-particles",type=Path,required=True)
    run.add_argument("--bootstrap",type=int,default=200)
    return p


if __name__=="__main__":
    arguments=parser().parse_args()
    if arguments.command=="prepare":
        prepare_reference(arguments)
    else:
        run_forecast(arguments)
