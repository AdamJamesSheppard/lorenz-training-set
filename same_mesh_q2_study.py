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
from scipy.ndimage import gaussian_filter

from lorenz_fpe import (
    AFCProjectionFokkerPlanckSolver,
    DensityState,
    Domain,
    FokkerPlanckSolver,
    LocalProjectionFokkerPlanckSolver,
    Lorenz63Model,
)
from lorenz_fpe.core import write_json
from lorenz_fpe.validation import _propagate_particles, covariance_accuracy


def _sha256(path: Path) -> str:
    digest=hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda:source.read(1024*1024),b""):
            digest.update(block)
    return digest.hexdigest()


def _model(noise_matrix: list[float] | tuple[float, ...] | None) -> Lorenz63Model:
    if noise_matrix is None:
        return Lorenz63Model()
    matrix = np.asarray(noise_matrix, dtype=float).reshape(3, 3)
    return Lorenz63Model(B=tuple(tuple(float(value) for value in row) for row in matrix))


def _marginal_tv(cell_averages: np.ndarray, particles: np.ndarray,
                 domain: Domain) -> list[float]:
    grid_shape=cell_averages.shape
    probability=cell_averages*domain.volume/cell_averages.size
    result=[]
    for axis,((lo,hi),count) in enumerate(zip(domain.bounds,grid_shape)):
        other=tuple(i for i in range(3) if i!=axis)
        numerical=probability.sum(axis=other)
        sampled=np.histogram(particles[:,axis],bins=count,range=(lo,hi))[0]/len(particles)
        result.append(float(.5*np.abs(numerical-sampled).sum()))
    return result


def _sample_truncated_gaussian(
    mean: np.ndarray,
    covariance: np.ndarray,
    bounds: tuple[tuple[float, float], ...],
    count: int,
    rng: np.random.Generator,
) -> tuple[np.ndarray, int]:
    """Sample one common continuous Gaussian law conditioned on the box."""
    accepted: list[np.ndarray] = []
    accepted_count = 0
    proposed = 0
    while accepted_count < count:
        batch_size = max(1024, 2 * (count - accepted_count))
        batch = rng.multivariate_normal(mean, covariance, size=batch_size)
        inside = np.ones(batch_size, dtype=bool)
        for axis, (lo, hi) in enumerate(bounds):
            inside &= (batch[:, axis] >= lo) & (batch[:, axis] <= hi)
        kept = batch[inside]
        if kept.size:
            accepted.append(kept)
            accepted_count += len(kept)
        proposed += batch_size
    return np.concatenate(accepted, axis=0)[:count], proposed


def _sample_truncated_mixture(
    mixture: dict[str, object], bounds: tuple[tuple[float, float], ...],
    count: int, rng: np.random.Generator,
) -> tuple[np.ndarray, int]:
    """Draw from a Gaussian mixture conditioned on the computational box."""
    weights=np.asarray(mixture["weights"],dtype=float); weights/=weights.sum()
    means=np.asarray(mixture["means"],dtype=float)
    covariances=np.asarray(mixture["covariances"],dtype=float)
    accepted=[]; have=0; proposed=0
    while have<count:
        batch=max(4096,2*(count-have))
        labels=rng.choice(len(weights),size=batch,p=weights)
        values=np.empty((batch,3),dtype=float)
        for label in np.unique(labels):
            mask=labels==label
            values[mask]=rng.multivariate_normal(
                means[label],covariances[label],size=int(mask.sum())
            )
        inside=np.ones(batch,dtype=bool)
        for axis,(lo,hi) in enumerate(bounds):
            inside&=(values[:,axis]>=lo)&(values[:,axis]<=hi)
        kept=values[inside]
        if len(kept):
            accepted.append(kept); have+=len(kept)
        proposed+=batch
    return np.concatenate(accepted)[:count],proposed


def _symmetric_mature_mixture(
    particles: np.ndarray, components_per_lobe: int,
    rng: np.random.Generator,
) -> dict[str, object]:
    """Fit one lobe by k-means and mirror it under Lorenz symmetry."""
    positive=np.asarray(particles[particles[:,0]>0.0],dtype=float)
    if len(positive)<100*components_per_lobe:
        raise RuntimeError("Spin-up ensemble did not populate the positive Lorenz lobe")
    fit=positive[rng.choice(len(positive),size=min(100000,len(positive)),replace=False)]
    centres=np.empty((components_per_lobe,3),dtype=float)
    centres[0]=fit[rng.integers(len(fit))]
    distance=np.sum((fit-centres[0])**2,axis=1)
    for j in range(1,components_per_lobe):
        probabilities=distance/distance.sum()
        centres[j]=fit[rng.choice(len(fit),p=probabilities)]
        distance=np.minimum(distance,np.sum((fit-centres[j])**2,axis=1))
    for _ in range(40):
        labels=np.argmin(np.sum((fit[:,None,:]-centres[None,:,:])**2,axis=2),axis=1)
        updated=np.stack([
            fit[labels==j].mean(0) if np.any(labels==j) else centres[j]
            for j in range(components_per_lobe)
        ])
        if np.max(np.linalg.norm(updated-centres,axis=1))<1.0e-6:
            centres=updated; break
        centres=updated
    labels=np.argmin(np.sum((positive[:,None,:]-centres[None,:,:])**2,axis=2),axis=1)
    means=[]; covariances=[]; weights=[]
    for j in range(components_per_lobe):
        cluster=positive[labels==j]
        if len(cluster)<10:
            continue
        covariance=np.cov(cluster,rowvar=False)
        eigenvalues,eigenvectors=np.linalg.eigh(covariance)
        covariance=(eigenvectors*np.maximum(eigenvalues,0.25))@eigenvectors.T
        means.append(cluster.mean(0)); covariances.append(covariance)
        weights.append(len(cluster)/(2.0*len(positive)))
    symmetry=np.diag([-1.0,-1.0,1.0])
    mirrored_means=[symmetry@mean for mean in means]
    mirrored_covariances=[symmetry@covariance@symmetry for covariance in covariances]
    return {
        "weights":(weights+weights),
        "means":[value.tolist() for value in means+mirrored_means],
        "covariances":[value.tolist() for value in covariances+mirrored_covariances],
        "construction":"positive-x spin-up clusters mirrored by (x,y,z)->(-x,-y,z)",
    }


def _condition_mixture_on_z(
    mixture: dict[str, object], observation: float, variance: float,
) -> dict[str, object]:
    """Apply a scalar Gaussian z likelihood analytically to every component."""
    weights=np.asarray(mixture["weights"],dtype=float)
    means=np.asarray(mixture["means"],dtype=float)
    covariances=np.asarray(mixture["covariances"],dtype=float)
    updated_means=[]; updated_covariances=[]; updated_weights=[]
    for weight,mean,covariance in zip(weights,means,covariances):
        innovation_variance=float(covariance[2,2]+variance)
        gain=covariance[:,2]/innovation_variance
        updated_means.append(mean+gain*(observation-mean[2]))
        updated_covariances.append(
            covariance-np.outer(covariance[:,2],covariance[2,:])/innovation_variance
        )
        likelihood=np.exp(-0.5*(observation-mean[2])**2/innovation_variance)/math.sqrt(
            2.0*np.pi*innovation_variance
        )
        updated_weights.append(weight*likelihood)
    updated_weights=np.asarray(updated_weights); updated_weights/=updated_weights.sum()
    return {
        "weights":updated_weights.tolist(),
        "means":[value.tolist() for value in updated_means],
        "covariances":[value.tolist() for value in updated_covariances],
        "construction":mixture["construction"],
        "analysis":{"observation_operator":"z","observation":observation,
                    "variance":variance,"method":"analytic Gaussian-mixture conditioning"},
    }


def _lobe_probabilities_grid(cell_averages: np.ndarray, domain: Domain) -> dict[str,float]:
    probability=np.asarray(cell_averages,dtype=float)*domain.volume/cell_averages.size
    x=np.linspace(domain.bounds[0][0],domain.bounds[0][1],cell_averages.shape[0],endpoint=False)
    x+=(domain.bounds[0][1]-domain.bounds[0][0])/(2*cell_averages.shape[0])
    return {"negative_x":float(probability[x<0].sum()),
            "positive_x":float(probability[x>0].sum())}


def _lobe_probabilities_particles(particles: np.ndarray) -> dict[str,float]:
    return {"negative_x":float(np.mean(particles[:,0]<0.0)),
            "positive_x":float(np.mean(particles[:,0]>0.0))}


def _coarsen_averages(values: np.ndarray, shape: tuple[int,int,int]) -> np.ndarray:
    factors=tuple(got//want for got,want in zip(values.shape,shape))
    if any(want*factor!=got for got,want,factor in zip(values.shape,shape,factors)):
        raise ValueError(f"Cannot coarsen {values.shape} exactly to {shape}")
    return values.reshape(
        shape[0],factors[0],shape[1],factors[1],shape[2],factors[2]
    ).mean(axis=(1,3,5))


def _joint_density_comparison(
    values: np.ndarray, particles: np.ndarray, domain: Domain,
    shape: tuple[int,int,int], smoothing_sigma: float,
) -> dict[str,float]:
    numerical=_coarsen_averages(values,shape)
    numerical_probability=numerical*domain.volume/numerical.size
    histogram,_=np.histogramdd(particles,bins=shape,range=domain.bounds)
    sampled_probability=histogram/len(particles)
    numerical_smoothed=gaussian_filter(numerical_probability,smoothing_sigma,mode="constant")
    sampled_smoothed=gaussian_filter(sampled_probability,smoothing_sigma,mode="constant")
    l1=float(np.abs(numerical_smoothed-sampled_smoothed).sum())
    return {"smoothed_probability_l1":l1,"smoothed_total_variation":0.5*l1,
            "mc_probability_inside_domain":float(histogram.sum()/len(particles)),
            "grid":list(shape),"gaussian_smoothing_sigma_in_voxels":smoothing_sigma}


def _write_indicator_snapshot(
    solver: FokkerPlanckSolver, step: int, state: DensityState, output: Path
) -> dict[str,object] | None:
    """Archive one cellwise QP/negativity/jump indicator snapshot."""
    projector=getattr(solver,"local_projector",None)
    if projector is None or projector.last_raw_coefficients is None:
        raise RuntimeError("indicator snapshots require a completed local-QP projection")
    raw=projector.last_raw_coefficients
    final=state.function.x.array
    limiter=solver.limiter
    _,volumes,mids=solver.cell_averages(state)
    correction=np.empty(len(mids)); mass=np.empty(len(mids))
    witnessed=np.empty(len(mids),dtype=np.uint8); high_mode=np.empty(len(mids))
    averages=np.empty(len(mids))
    for cell,dofs in enumerate(limiter.cell_dofs):
        raw_values=raw[dofs]; final_values=final[dofs]
        correction[cell]=volumes[cell]*float(
            limiter._quadrature_weights@np.abs(
                limiter._quadrature_basis@(final_values-raw_values)
            )
        )
        average=limiter.cell_average(final_values); averages[cell]=average
        mass[cell]=volumes[cell]*max(average,0.0)
        witnessed[cell]=int(
            limiter.classify_coefficients(raw_values)["status"]=="WITNESSED_NEGATIVE"
        )
        values=limiter._quadrature_basis@final_values
        high_mode[cell]=volumes[cell]*float(
            limiter._quadrature_weights@np.abs(values-average)
        )
    gathered=solver.comm.gather(
        (mids,volumes,correction,mass,witnessed,high_mode,averages),root=0
    )
    if solver.comm.rank!=0:
        return None
    shape=solver.domain.cells
    arrays={name:np.zeros(shape,dtype=float) for name in (
        "cell_volume","correction_l1","probability_mass","negative_witness_mass",
        "high_mode_l1","cell_average"
    )}
    for gmids,gvol,gcorrection,gmass,gwitnessed,ghigh,gaverage in gathered:
        for row,point in enumerate(gmids):
            index=tuple(min(shape[d]-1,max(0,int(np.searchsorted(
                solver.axis_coordinates[d],point[d],side="right"
            )-1))) for d in range(3))
            arrays["cell_volume"][index]=gvol[row]
            arrays["correction_l1"][index]=gcorrection[row]
            arrays["probability_mass"][index]=gmass[row]
            arrays["negative_witness_mass"][index]=gmass[row]*gwitnessed[row]
            arrays["high_mode_l1"][index]=ghigh[row]
            arrays["cell_average"][index]=gaverage[row]
    jump=np.zeros(shape,dtype=float)
    average=arrays["cell_average"]
    for axis in range(3):
        difference=np.abs(np.diff(average,axis=axis))
        left=[slice(None)]*3; right=[slice(None)]*3
        left[axis]=slice(0,-1); right[axis]=slice(1,None)
        jump[tuple(left)]=np.maximum(jump[tuple(left)],difference)
        jump[tuple(right)]=np.maximum(jump[tuple(right)],difference)
    arrays["jump_indicator"]=jump*arrays["cell_volume"]
    output.mkdir(parents=True,exist_ok=True)
    path=output/f"indicator_step_{step:04d}.npz"
    np.savez_compressed(path,step=step,time=state.time,**arrays)
    return {"step":step,"time":state.time,"path":path.name,
            "sha256":_sha256(path),"bytes":path.stat().st_size,
            "correction_l1_sum":float(arrays["correction_l1"].sum()),
            "negative_witness_probability_mass":float(
                arrays["negative_witness_mass"].sum()
            )}


def prepare_reference(args: argparse.Namespace) -> None:
    if MPI.COMM_WORLD.size!=1:
        raise SystemExit("reference preparation must run on one rank")
    output=args.output.resolve(); output.mkdir(parents=True,exist_ok=False)
    domain=Domain(cells=tuple(args.cells)); model=_model(args.noise_matrix)
    solver=FokkerPlanckSolver(model,domain,args.dt,degree=1)
    rng=np.random.default_rng(args.seed)
    artifacts={}
    if args.mature_mixture:
        equilibrium=math.sqrt(model.beta*(model.rho-1.0))
        half=args.spinup_particles//2
        positive=rng.multivariate_normal(
            [equilibrium,equilibrium,model.rho-1.0],np.diag([4.0,4.0,4.0]),size=half
        )
        negative=positive.copy(); negative[:,:2]*=-1.0
        spinup_initial=np.concatenate([positive,negative],axis=0)
        spinup_started=time.perf_counter()
        spinup=_propagate_particles(
            model,spinup_initial,args.spinup_time,args.spinup_dt,rng
        )
        spinup_seconds=time.perf_counter()-spinup_started
        prior_mixture=_symmetric_mature_mixture(
            spinup,args.components_per_lobe,rng
        )
        mixture=_condition_mixture_on_z(
            prior_mixture,args.observation_z,args.observation_variance
        )
        mixture_path=output/"mature_mixture.json"
        write_json(mixture_path,mixture)
        particles0,proposals=_sample_truncated_mixture(
            mixture,domain.bounds,args.particles,rng
        )
        sampling={"method":"analytic Gaussian mixture conditioned on domain by rejection",
                  "samples":args.particles,"proposals":proposals,
                  "acceptance_rate":args.particles/proposals}
        initialization={
            "method":"independent stochastic spin-up, symmetric Gaussian-mixture fit, z-only analysis",
            "spinup_particles":args.spinup_particles,"spinup_time":args.spinup_time,
            "spinup_dt":args.spinup_dt,"spinup_seconds":spinup_seconds,
            "components_per_lobe":args.components_per_lobe,
            "mixture_components":len(mixture["weights"]),
            "analysis":mixture["analysis"],
            "domain_bounds":[list(item) for item in domain.bounds],
        }
        initial_diagnostics={"sample_mean":particles0.mean(0).tolist(),
            "sample_covariance":np.cov(particles0,rowvar=False).tolist(),
            "lobe_probabilities":_lobe_probabilities_particles(particles0)}
        artifacts[mixture_path.name]={
            "sha256":_sha256(mixture_path),"bytes":mixture_path.stat().st_size
        }
    elif args.continuous_gaussian:
        mean=np.asarray(args.mean,dtype=float)
        covariance=np.diag(np.square(np.asarray(args.std,dtype=float)))
        particles0,proposals=_sample_truncated_gaussian(
            mean,covariance,domain.bounds,args.particles,rng
        )
        sampling={
            "method":"analytic_gaussian_conditioned_on_domain_by_rejection",
            "samples":args.particles,
            "proposals":proposals,
            "acceptance_rate":args.particles/proposals,
        }
        initialization={
            "method":"common_continuous_truncated_gaussian",
            "mean":mean.tolist(),
            "covariance":covariance.tolist(),
            "domain_bounds":[list(item) for item in domain.bounds],
        }
        initial_diagnostics={
            "sample_mean":particles0.mean(0).tolist(),
            "sample_covariance":np.cov(particles0,rowvar=False).tolist(),
        }
    else:
        mean=np.asarray(args.mean,dtype=float)
        covariance=np.diag(np.square(np.asarray(args.std,dtype=float)))
        initial=solver.gaussian_projected(
            mean,covariance,quadrature_degree=14,apply_limiter=True,
        )
        grid=solver.structured_export(initial,3)
        grid_path=output/"initial_q1_subcell_averages.npy"; np.save(grid_path,grid)
        particles0=solver.sample_density(initial,args.particles,rng)
        sampling=dict(solver.last_sampling_report)
        initialization=solver.last_initialization_report
        initial_diagnostics=solver.diagnostics(initial)
        artifacts[grid_path.name]={
            "sha256":_sha256(grid_path),"bytes":grid_path.stat().st_size
        }
    initial_particle_path=output/"mc_initial_particles.npy"
    np.save(initial_particle_path,particles0)
    artifacts[initial_particle_path.name]={
        "sha256":_sha256(initial_particle_path),"bytes":initial_particle_path.stat().st_size
    }
    started=time.perf_counter()
    particles=_propagate_particles(model,particles0,args.t_final,args.mc_dt,rng)
    propagation_seconds=time.perf_counter()-started
    particle_path=output/"mc_final_particles.npy"; np.save(particle_path,particles)
    report={
        "configuration":{"cells":list(args.cells),"dt":args.dt,"t_final":args.t_final,
            "particles":args.particles,"mc_dt":args.mc_dt,"seed":args.seed,
            "mature_mixture":bool(args.mature_mixture),
            "noise_matrix":np.asarray(model.B,dtype=float).tolist(),
            "diffusion_matrix":model.diffusion.tolist()},
        "initialization":initialization,
        "initial_diagnostics":initial_diagnostics,"native_sampling":sampling,
        "mc":{"mean":particles.mean(0).tolist(),"covariance":np.cov(particles,rowvar=False).tolist(),
            "propagation_seconds":propagation_seconds},
        "artifacts":{
            **artifacts,
            particle_path.name:{"sha256":_sha256(particle_path),"bytes":particle_path.stat().st_size},
        },
    }
    write_json(output/"reference.json",report)
    print(output/"reference.json",flush=True)


def run_forecast(args: argparse.Namespace) -> None:
    comm=MPI.COMM_WORLD; rank=comm.rank
    if args.local_projection and args.afc_projection:
        raise ValueError("Choose exactly one local-QP update architecture")
    output=args.output.resolve()
    if rank==0:
        output.mkdir(parents=True,exist_ok=False)
    comm.barrier()
    domain=Domain(cells=tuple(args.cells)); model=_model(args.noise_matrix)
    axis_coordinates=None
    if args.axis_coordinates is not None:
        axis_payload=json.loads(args.axis_coordinates.read_text())
        if all(name in axis_payload for name in ("x","y","z")):
            axis_coordinates=tuple(
                np.asarray(axis_payload[name],dtype=float) for name in ("x","y","z")
            )
        else:
            common_shape=tuple(int(value) for value in axis_payload["common_shape"])
            axis_coordinates=tuple(
                lo+(hi-lo)*np.asarray(axis_payload["edge_indices"][name],dtype=float)/count
                for name,(lo,hi),count in zip(
                    ("x","y","z"),domain.bounds,common_shape
                )
            )
    solver_class = (
        AFCProjectionFokkerPlanckSolver if args.afc_projection else
        LocalProjectionFokkerPlanckSolver if args.local_projection else
        FokkerPlanckSolver
    )
    solver_options = {}
    if args.local_projection or args.afc_projection:
        solver_options = {
            "local_optimizer_backend": args.local_optimizer_backend,
            "local_optimizer_ftol": args.local_optimizer_ftol,
            "local_maximum_iterations": args.local_maximum_iterations,
        }
    solver=solver_class(
        model,domain,args.dt,theta=args.theta,degree=args.degree,
        ksp_rtol=args.ksp_rtol,ksp_atol=args.ksp_atol,
        certificate_mode=args.certificate_mode,
        certificate_max_depth=args.certificate_max_depth,
        certificate_diagnostics=args.degree>=2,
        apply_positivity=not args.disable_positivity,
        axis_coordinates=axis_coordinates,
        **solver_options,
    )
    initial_projection=None
    if args.initialization == "gaussian_projected":
        initial_covariance=np.diag(np.square(np.asarray(args.std,dtype=float)))
        initial=solver.gaussian_projected(
            args.mean,initial_covariance,
            quadrature_degree=args.initial_quadrature_degree,apply_limiter=False,
        )
        if args.local_projection or args.afc_projection:
            initial,initial_projection=solver.local_projector.project_state(
                initial,repair_cell_averages=True,adaptive_skip=True
            )
        elif solver.apply_positivity:
            initial_projection=asdict(solver.limiter.apply(initial))
        embedding=None
    elif args.initialization == "structured":
        if args.initial_grid is None:
            raise ValueError("--initial-grid is required for structured initialization")
        grid=np.load(args.initial_grid)
        initial=solver.from_structured(grid,apply_limiter=False)
        represented=solver.structured_export(initial,3)
        if rank==0:
            embedding={"maximum_subcell_average_error":float(np.max(np.abs(represented-grid))),
                "relative_l2_subcell_average_error":float(
                    np.linalg.norm(represented-grid)/max(np.linalg.norm(grid),np.finfo(float).tiny)
                )}
        else:
            embedding=None
    else:
        if args.mixture is None:
            raise ValueError("--mixture is required for mixture_projected initialization")
        mixture=json.loads(args.mixture.read_text())
        expression=sum(
            float(weight)*solver.gaussian_expression(mean,np.asarray(covariance,dtype=float))
            for weight,mean,covariance in zip(
                mixture["weights"],mixture["means"],mixture["covariances"]
            )
        )
        initial=solver.project_expression(
            expression,"mature_mixture_l2_projected",
            quadrature_degree=args.initial_quadrature_degree,
            normalize=True,apply_limiter=False,
        )
        if args.local_projection or args.afc_projection:
            initial,initial_projection=solver.local_projector.project_state(
                initial,repair_cell_averages=True,adaptive_skip=True
            )
        elif solver.apply_positivity:
            initial_projection=asdict(solver.limiter.apply(initial))
        embedding={"source":"frozen analytic mature Gaussian mixture",
                   "mixture_sha256":_sha256(args.mixture),
                   "local_projection":initial_projection} if rank==0 else None
    initial_diagnostics=solver.diagnostics(initial)
    indicator_steps=set(args.indicator_snapshot_steps or [])
    indicator_records=[]
    if indicator_steps and args.indicator_output is None:
        raise ValueError("--indicator-output is required with indicator snapshot steps")
    if 0 in indicator_steps:
        record=_write_indicator_snapshot(solver,0,initial,args.indicator_output)
        if rank==0: indicator_records.append(record)
    n_owned_initial=solver.V.dofmap.index_map.size_local*solver.V.dofmap.index_map_bs
    initial_state_sha256_by_rank=comm.gather(
        hashlib.sha256(
            np.asarray(initial.function.x.array[:n_owned_initial],dtype=np.float64).tobytes()
        ).hexdigest(),
        root=0,
    )
    if args.initialization == "gaussian_projected" and rank==0:
        represented_covariance=np.asarray(initial_diagnostics["covariance"])
        embedding={
            "source":"common_continuous_truncated_gaussian",
            "mass":initial_diagnostics["mass"],
            "mean_error":(
                np.asarray(initial_diagnostics["mean"])-np.asarray(args.mean)
            ).tolist(),
            "normalized_covariance_error":float(
                np.linalg.norm(represented_covariance-initial_covariance,"fro")
                /np.linalg.norm(initial_covariance,"fro")
            ),
            "local_projection":initial_projection,
        }
    if args.common_export_grid is not None:
        initial_cells=solver.common_grid_export(initial,tuple(args.common_export_grid))
        initial_subcells=initial_cells
    else:
        initial_cells=solver.structured_export(initial,1)
        initial_subcells=solver.structured_export(initial,args.export_subcells)
    initial_particles=(np.load(args.initial_mc_particles)
                       if rank==0 and args.initial_mc_particles is not None else None)
    if rank==0 and initial_particles is not None:
        initial_covariance=covariance_accuracy(
            np.asarray(initial_diagnostics["covariance"]),initial_particles,
            args.bootstrap_seed,args.bootstrap,
        )
        embedding.update({
            "mass":initial_diagnostics["mass"],
            "covariance_accuracy":initial_covariance,
            "marginal_total_variation_distance":_marginal_tv(
                initial_cells,initial_particles,domain
            ),
            "lobe_probabilities":_lobe_probabilities_grid(initial_subcells,domain),
            "mc_lobe_probabilities":_lobe_probabilities_particles(initial_particles),
            "joint_density":_joint_density_comparison(
                initial_subcells,initial_particles,domain,
                tuple(args.density_metric_grid),args.density_smoothing_sigma,
            ),
        })

    steps=round(args.t_final/args.dt)
    if not math.isclose(steps*args.dt,args.t_final,abs_tol=1e-14):
        raise ValueError("t_final must be an integer multiple of dt")
    n_owned=solver.V.dofmap.index_map.size_local*solver.V.dofmap.index_map_bs
    raw_path=None; raw_archive=None
    if args.degree>=2 and not args.no_raw_archive:
        raw_path=output/f"raw_before_correction_rank{rank:04d}.npy"
        raw_archive=np.lib.format.open_memmap(
            raw_path,mode="w+",dtype=np.float64,shape=(steps,n_owned)
        )
    state=initial; started=time.perf_counter(); step_seconds=[]
    for step in range(steps):
        step_started=time.perf_counter(); state=solver.step(state)
        step_seconds.append(time.perf_counter()-step_started)
        if raw_archive is not None:
            source=(solver.limiter.last_raw_coefficients
                    if (solver.apply_positivity or args.local_projection or args.afc_projection)
                    else state.function.x.array)
            raw_archive[step]=source[:n_owned]
            if (step+1)%10==0:
                raw_archive.flush()
        if step+1 in indicator_steps:
            record=_write_indicator_snapshot(
                solver,step+1,state,args.indicator_output
            )
            if rank==0: indicator_records.append(record)
        if rank==0 and ((step+1)%max(1,steps//10)==0 or step+1==steps):
            elapsed=time.perf_counter()-started
            print(f"{args.branch}: step {step+1}/{steps}, elapsed={elapsed:.1f}s",flush=True)
    if raw_archive is not None:
        raw_archive.flush(); del raw_archive
    forecast_seconds=time.perf_counter()-started

    if args.local_projection or args.afc_projection:
        if solver.last_unlimited_state is None:
            raise RuntimeError("Local projection did not retain the unlimited state")
        stages=solver.limiter_stage_states(state.time)
    elif solver.apply_positivity:
        stages=solver.limiter_stage_states(state.time)
    else:
        stages={name:state.copy(name) for name in ("raw","stage1","final")}
    stage_diagnostics={name:solver.diagnostics(stage) for name,stage in stages.items()}
    if args.common_export_grid is not None:
        stage_cells={name:solver.common_grid_export(stage,tuple(args.common_export_grid))
                     for name,stage in stages.items()}
        final_subcells=stage_cells["final"]
    else:
        stage_cells={name:solver.structured_export(stage,1) for name,stage in stages.items()}
        final_subcells=solver.structured_export(stages["final"],args.export_subcells)
    final_subcells_path=output/"final_q2_subcell_averages.npy"
    if rank==0:
        np.save(final_subcells_path,final_subcells)
    particles=np.load(args.mc_particles) if rank==0 else None
    if rank==0:
        bootstrap_seed=args.bootstrap_seed
        comparisons={name:{
            "covariance_accuracy":covariance_accuracy(
                np.asarray(stage_diagnostics[name]["covariance"]),particles,
                bootstrap_seed,args.bootstrap,
            ),
            "marginal_total_variation_distance":_marginal_tv(values,particles,domain),
            "lobe_probabilities":_lobe_probabilities_grid(values,domain),
            "mc_lobe_probabilities":_lobe_probabilities_particles(particles),
        } for name,values in stage_cells.items()}
        comparisons["final"]["joint_density"]=_joint_density_comparison(
            final_subcells,particles,domain,tuple(args.density_metric_grid),
            args.density_smoothing_sigma,
        )
        comparisons["final"]["maximum_lobe_probability_error"]=max(
            abs(comparisons["final"]["lobe_probabilities"][key]
                -comparisons["final"]["mc_lobe_probabilities"][key])
            for key in ("negative_x","positive_x")
        )
    else:
        comparisons=None

    artifacts=[]
    if args.degree>=2:
        classification_source=(solver.limiter.last_raw_coefficients
                               if (solver.apply_positivity or args.local_projection or args.afc_projection)
                               else state.function.x.array)
        records=solver.limiter.classification_records(classification_source)
        records_path=output/f"final_raw_cell_classification_rank{rank:04d}.json"
        records_path.write_text(json.dumps(records,separators=(",",":")),encoding="utf-8")
        artifacts.append(records_path)
        if raw_path is not None:
            artifacts.append(raw_path)
    local_artifacts=[{"path":path.name,"sha256":_sha256(path),"bytes":path.stat().st_size}
                     for path in artifacts]
    gathered_artifacts=comm.gather(local_artifacts,root=0)
    peak_rss_kib=comm.gather(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,root=0)
    maximum_step_seconds=comm.allreduce(max(step_seconds),op=MPI.MAX)
    mean_step_seconds=comm.allreduce(sum(step_seconds)/len(step_seconds),op=MPI.MAX)

    if rank==0:
        gathered_artifacts[0].append({"path":final_subcells_path.name,
            "sha256":_sha256(final_subcells_path),"bytes":final_subcells_path.stat().st_size})
        history=(solver.local_projection_history_summary()
                 if (args.local_projection or args.afc_projection)
                 else solver.limiter_history_summary())
        corrected=comparisons["final"]["covariance_accuracy"]
        positivity_enabled=bool(
            solver.apply_positivity or args.local_projection or args.afc_projection
        )
        mean_l1=(history["relative_l1_correction"]["mean"] if positivity_enabled else 0.0)
        maximum_l1=(history["relative_l1_correction"]["maximum"] if positivity_enabled else 0.0)
        report={
            "branch":args.branch,
            "configuration":{"cells":list(args.cells),"degree":args.degree,"dt":args.dt,
                "theta":args.theta,"t_final":args.t_final,"mpi_ranks":comm.size,
                "ksp_rtol":args.ksp_rtol,"ksp_atol":args.ksp_atol,
                "certificate_mode":args.certificate_mode,
                "certificate_max_depth":args.certificate_max_depth,
                "positivity_applied_each_step":positivity_enabled,
                "positivity_method":(
                    "positive_p0_graph_update_then_limited_antidiffusion_then_local_qp"
                    if args.afc_projection else
                    "global_average_repair_then_local_qp" if args.local_projection else
                    ("global_average_repair_then_scaling" if solver.apply_positivity else "none")),
                "local_optimizer_backend":(args.local_optimizer_backend
                    if (args.local_projection or args.afc_projection) else None),
                "local_optimizer_ftol":(args.local_optimizer_ftol
                    if (args.local_projection or args.afc_projection) else None),
                "local_maximum_iterations":(args.local_maximum_iterations
                    if (args.local_projection or args.afc_projection) else None),
                "initialization":args.initialization,
                "mixture_sha256":(_sha256(args.mixture) if args.mixture else None),
                "initial_mean":list(args.mean),"initial_standard_deviation":list(args.std),
                "initial_quadrature_degree":args.initial_quadrature_degree,
                "export_subcells_per_cell":args.export_subcells,
                "axis_coordinates":(str(args.axis_coordinates.resolve())
                    if args.axis_coordinates else None),
                "axis_coordinates_sha256":(_sha256(args.axis_coordinates)
                    if args.axis_coordinates else None),
                "common_export_grid":(list(args.common_export_grid)
                    if args.common_export_grid else None),
                "cell_count":int(np.prod(args.cells)),
                "dg_dofs":int(np.prod(args.cells)*(args.degree+1)**3),
                "minimum_cell_volume":float(np.min(solver.cell_volumes)),
                "maximum_cell_volume":float(np.max(solver.cell_volumes)),
                "bootstrap_replicates":args.bootstrap,
                "bootstrap_seed":bootstrap_seed,"seed":args.seed,
                "density_metric_grid":list(args.density_metric_grid),
                "density_smoothing_sigma":args.density_smoothing_sigma,
                "noise_matrix":np.asarray(model.B,dtype=float).tolist(),
                "diffusion_matrix":model.diffusion.tolist()},
            "initial_embedding":embedding,"initial_diagnostics":initial_diagnostics,
            "initial_state_sha256_by_rank":initial_state_sha256_by_rank,
            "final_stage_diagnostics":stage_diagnostics,"comparisons_to_common_mc":comparisons,
            "limiter_history":history,
            "limiter_steps":(solver.local_projection_history
                if (args.local_projection or args.afc_projection) else
                [asdict(item) for item in solver.limiter_history]),
            "indicator_snapshots":indicator_records,
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


def recover_final(args: argparse.Namespace) -> None:
    """Reconstruct a corrected final state from a prior raw MPI archive."""
    comm=MPI.COMM_WORLD; rank=comm.rank
    output=args.output.resolve()
    if rank==0:
        output.mkdir(parents=True,exist_ok=False)
    comm.barrier()
    solver=FokkerPlanckSolver(
        Lorenz63Model(),Domain(cells=tuple(args.cells)),args.dt,degree=args.degree,
        certificate_mode=args.certificate_mode,
        certificate_max_depth=args.certificate_max_depth,
        certificate_diagnostics=args.degree>=2,
    )
    archive_path=args.raw_dir/f"raw_before_correction_rank{rank:04d}.npy"
    raw=np.load(archive_path,mmap_mode="r")
    n_owned=solver.V.dofmap.index_map.size_local*solver.V.dofmap.index_map_bs
    if raw.shape[1]!=n_owned:
        raise ValueError(f"raw archive has {raw.shape[1]} owned dofs, expected {n_owned}")
    solver.p_new.x.array[:n_owned]=raw[-1]
    solver.p_new.x.scatter_forward()
    state=DensityState(solver.p_new,args.t_final,"recovered_final_raw")
    limiter=solver.limiter.apply(state)
    diagnostics=solver.diagnostics(state)
    subcells=solver.structured_export(state,3)
    source_hashes=comm.gather({"rank":rank,"sha256":_sha256(archive_path)},root=0)
    if rank==0:
        state_path=output/"final_q2_subcell_averages.npy"; np.save(state_path,subcells)
        report={"source_raw_directory":str(args.raw_dir.resolve()),
            "configuration":{"cells":list(args.cells),"degree":args.degree,"dt":args.dt,
                "t_final":args.t_final,"mpi_ranks":comm.size,
                "certificate_mode":args.certificate_mode,
                "certificate_max_depth":args.certificate_max_depth},
            "source_archive_hashes":source_hashes,"limiter":asdict(limiter),
            "diagnostics":diagnostics,"artifact":{"path":state_path.name,
                "sha256":_sha256(state_path),"bytes":state_path.stat().st_size}}
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
    common.add_argument("--noise-matrix",type=float,nargs=9)
    common.add_argument("--output",type=Path,required=True)
    prep=sub.add_parser("prepare",parents=[common])
    prep.add_argument("--particles",type=int,default=200000)
    prep.add_argument("--mc-dt",type=float,default=.000125)
    prep.add_argument("--mean",type=float,nargs=3,default=(1.0,1.0,20.0))
    prep.add_argument("--std",type=float,nargs=3,default=(2.0,2.0,3.0))
    prep.add_argument("--continuous-gaussian",action="store_true")
    prep.add_argument("--mature-mixture",action="store_true")
    prep.add_argument("--spinup-particles",type=int,default=200000)
    prep.add_argument("--spinup-time",type=float,default=2.0)
    prep.add_argument("--spinup-dt",type=float,default=0.001)
    prep.add_argument("--components-per-lobe",type=int,default=8)
    prep.add_argument("--observation-z",type=float,default=25.0)
    prep.add_argument("--observation-variance",type=float,default=16.0)
    run=sub.add_parser("forecast",parents=[common])
    run.add_argument("--branch",required=True)
    run.add_argument("--degree",type=int,choices=(1,2),required=True)
    run.add_argument("--theta",type=float,choices=(0.5,1.0),default=1.0)
    run.add_argument("--ksp-rtol",type=float,default=1.0e-10)
    run.add_argument("--ksp-atol",type=float,default=1.0e-13)
    run.add_argument("--certificate-mode",choices=("fixed","adaptive"),default="fixed")
    run.add_argument("--certificate-max-depth",type=int,default=4)
    run.add_argument("--initialization",choices=("structured","gaussian_projected",
                                                  "mixture_projected"),
                     default="structured")
    run.add_argument("--initial-grid",type=Path)
    run.add_argument("--mixture",type=Path)
    run.add_argument("--initial-mc-particles",type=Path)
    run.add_argument("--mean",type=float,nargs=3,default=(1.0,1.0,20.0))
    run.add_argument("--std",type=float,nargs=3,default=(2.0,2.0,3.0))
    run.add_argument("--initial-quadrature-degree",type=int,default=14)
    run.add_argument("--export-subcells",type=int,default=3)
    run.add_argument("--axis-coordinates",type=Path)
    run.add_argument("--common-export-grid",type=int,nargs=3)
    run.add_argument("--mc-particles",type=Path,required=True)
    run.add_argument("--bootstrap",type=int,default=200)
    run.add_argument("--bootstrap-seed",type=int,default=20261910)
    run.add_argument("--density-metric-grid",type=int,nargs=3,default=(20,24,24))
    run.add_argument("--density-smoothing-sigma",type=float,default=0.75)
    run.add_argument("--disable-positivity",action="store_true")
    run.add_argument("--local-projection",action="store_true")
    run.add_argument("--afc-projection",action="store_true")
    run.add_argument("--local-optimizer-backend",choices=("osqp","slsqp"),default="osqp")
    run.add_argument("--local-optimizer-ftol",type=float,default=1.0e-10)
    run.add_argument("--local-maximum-iterations",type=int,default=10_000)
    run.add_argument("--no-raw-archive",action="store_true")
    run.add_argument("--indicator-snapshot-steps",type=int,nargs="*")
    run.add_argument("--indicator-output",type=Path)
    recover=sub.add_parser("recover",parents=[common])
    recover.add_argument("--degree",type=int,choices=(1,2),default=2)
    recover.add_argument("--certificate-mode",choices=("fixed","adaptive"),default="adaptive")
    recover.add_argument("--certificate-max-depth",type=int,default=4)
    recover.add_argument("--raw-dir",type=Path,required=True)
    return p


if __name__=="__main__":
    arguments=parser().parse_args()
    if arguments.command=="prepare":
        prepare_reference(arguments)
    elif arguments.command=="forecast":
        run_forecast(arguments)
    else:
        recover_final(arguments)
