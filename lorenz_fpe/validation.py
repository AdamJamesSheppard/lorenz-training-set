"""Independent analytic and Monte-Carlo validation utilities."""

from __future__ import annotations

import math
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import ufl
from dolfinx import fem

from .core import (BayesianAnalysis, Domain, FokkerPlanckSolver, Lorenz63Model,
                   ObservationModel, TruthSimulator, write_json)
from .finite_volume import ConservativeFiniteVolume


def _correlation(cov: np.ndarray) -> np.ndarray:
    scale=np.sqrt(np.maximum(np.diag(cov),np.finfo(float).tiny))
    return cov/np.outer(scale,scale)


def covariance_accuracy(pde_covariance: np.ndarray, samples: np.ndarray, seed: int,
                        bootstrap_replicates: int = 200) -> dict[str,object]:
    """Scale-aware covariance comparison with nonparametric MC uncertainty."""
    pde=np.asarray(pde_covariance,float); samples=np.asarray(samples,float)
    mc=np.cov(samples,rowvar=False); denom=float(np.linalg.norm(mc)); error=pde-mc
    ep=float(np.linalg.norm(error)/denom)
    pde_e,pde_v=np.linalg.eigh(pde); mc_e,mc_v=np.linalg.eigh(mc)
    order=np.argsort(mc_e)[::-1]; mc_e=mc_e[order]; mc_v=mc_v[:,order]
    order=np.argsort(pde_e)[::-1]; pde_e=pde_e[order]; pde_v=pde_v[:,order]
    angles=np.degrees(np.arccos(np.clip(np.abs(np.sum(pde_v*mc_v,axis=0)),0,1)))
    rng=np.random.default_rng(seed); n=len(samples); boot_cov=[]; boot_noise=[]; boot_eigs=[]
    for _ in range(bootstrap_replicates):
        c=np.cov(samples[rng.integers(0,n,n)],rowvar=False)
        boot_cov.append(c); boot_noise.append(np.linalg.norm(c-mc)/denom)
        boot_eigs.append(np.linalg.eigvalsh(c)[::-1])
    bc=np.asarray(boot_cov); bn=np.asarray(boot_noise); be=np.asarray(boot_eigs)
    lo,hi=np.quantile(bc,[.025,.975],axis=0); elo,ehi=np.quantile(be,[.025,.975],axis=0)
    return {
        "pde_covariance":pde.tolist(),"mc_covariance":mc.tolist(),"entrywise_error":error.tolist(),
        "variance_error":np.diag(error).tolist(),"pde_correlation":_correlation(pde).tolist(),
        "mc_correlation":_correlation(mc).tolist(),"correlation_error":(_correlation(pde)-_correlation(mc)).tolist(),
        "pde_eigenvalues":pde_e.tolist(),"mc_eigenvalues":mc_e.tolist(),"eigenvalue_error":(pde_e-mc_e).tolist(),
        "principal_axis_orientation_error_degrees":angles.tolist(),
        "frobenius_error":float(np.linalg.norm(error)),"normalized_frobenius_error":ep,
        "mc_covariance_bootstrap_95_percent_ci":{"lower":lo.tolist(),"upper":hi.tolist()},
        "mc_eigenvalue_bootstrap_95_percent_ci":{"lower":elo.tolist(),"upper":ehi.tolist()},
        "mc_normalized_covariance_noise_floor":{"median":float(np.median(bn)),"p95":float(np.quantile(bn,.95)),
            "p99":float(np.quantile(bn,.99))},
        "pde_error_to_mc_noise_p95_ratio":ep/max(float(np.quantile(bn,.95)),np.finfo(float).tiny),
        "bootstrap_replicates":bootstrap_replicates,
    }


@dataclass(frozen=True)
class ConstantModel:
    velocity: tuple[float,float,float] = (0.,0.,0.)
    B: tuple[tuple[float,float,float],...] = ((1.,0.,0.),(0.,1.,0.),(0.,0.,1.))
    sigma: float = 0.; rho: float = 0.; beta: float = 0.
    @property
    def diffusion(self):
        B=np.asarray(self.B); return .5*B@B.T
    def drift_numpy(self,x):
        return np.broadcast_to(np.asarray(self.velocity),np.shape(x)).copy()
    def drift_ufl(self,x):
        # Tiny symbolic term attaches this otherwise constant expression to
        # the mesh domain; its physical effect is far below IEEE roundoff.
        return ufl.as_vector([v + 1.0e-300*x[0] for v in self.velocity])


def gaussian_errors(solver:FokkerPlanckSolver,state,mean,covariance)->dict[str,float]:
    x=ufl.SpatialCoordinate(solver.mesh); mean=np.asarray(mean); cov=np.asarray(covariance); inv=np.linalg.inv(cov)
    d=ufl.as_vector([x[i]-mean[i] for i in range(3)])
    exact=(2*np.pi)**-1.5/math.sqrt(float(np.linalg.det(cov)))*ufl.exp(-.5*ufl.dot(d,ufl.dot(ufl.as_matrix(inv.tolist()),d)))
    e=state.function-exact
    return {"l1_error":solver._integral(abs(e)),"l2_error":math.sqrt(max(0.,solver._integral(e*e)))}


def gaussian_representation_metrics(solver:FokkerPlanckSolver,state,mean,covariance,
                                    quadrature_degree:int=16)->dict[str,object]:
    """Compare a discrete density with the finite-box normalized Gaussian."""
    exact_raw=solver.gaussian_expression(mean,covariance)
    normalizer=solver._integral(exact_raw,quadrature_degree)
    exact=exact_raw/normalizer; x=ufl.SpatialCoordinate(solver.mesh)
    exact_mean=np.array([solver._integral(x[i]*exact,quadrature_degree) for i in range(3)])
    exact_cov=np.empty((3,3))
    for i in range(3):
        for j in range(3):
            exact_cov[i,j]=solver._integral((x[i]-exact_mean[i])*(x[j]-exact_mean[j])*exact,quadrature_degree)
    d=solver.diagnostics(state); numerical_cov=np.asarray(d["covariance"]); error=state.function-exact
    return {"analytic_finite_box_mass_before_normalization":normalizer,
        "mass":d["mass"],"minimum":d["minimum"],"negative_mass":d["negative_mass"],
        "mean":d["mean"],"analytic_mean":exact_mean.tolist(),
        "mean_error":(np.asarray(d["mean"])-exact_mean).tolist(),
        "covariance":d["covariance"],"analytic_covariance":exact_cov.tolist(),
        "covariance_error":(numerical_cov-exact_cov).tolist(),
        "normalized_covariance_error":float(np.linalg.norm(numerical_cov-exact_cov)/np.linalg.norm(exact_cov)),
        "l1_error":solver._integral(abs(error),quadrature_degree),
        "l2_error":math.sqrt(max(0.,solver._integral(error*error,quadrature_degree))),
        "entropy_cell_average":d["entropy_cell_average"]}


def initialization_representation_study(
    resolutions=((8,10,10),(12,16,16),(20,24,24),(30,36,36)),
    mean=(1.,1.,20.), covariance=np.diag([4.,4.,9.]), quadrature_degree=14,
)->dict[str,object]:
    """Interpolation/projection errors and projection quadrature convergence."""
    rows=[]
    for cells in resolutions:
        solver=FokkerPlanckSolver(Lorenz63Model(),Domain(cells=tuple(cells)),.00125)
        for method,limited in (("nodal_interpolation",True),("l2_projection_unlimited",False),
                               ("l2_projection_limited",True)):
            if method=="nodal_interpolation":
                state=solver.gaussian_interpolated(mean,covariance); initialization=dict(solver.last_initialization_report)
            else:
                state=solver.gaussian_projected(mean,covariance,quadrature_degree=quadrature_degree,
                                                apply_limiter=limited)
                initialization=dict(solver.last_initialization_report)
            rows.append({"cells":list(cells),"method":method,
                "representation":gaussian_representation_metrics(solver,state,mean,covariance,quadrature_degree+2),
                "initialization":initialization})

    # This sequence isolates integration accuracy from mesh/positivity effects.
    cells=tuple(resolutions[1]); solver=FokkerPlanckSolver(Lorenz63Model(),Domain(cells=cells),.00125)
    projected=[]
    for degree in (4,6,8,10,12,14,16):
        state=solver.gaussian_projected(mean,covariance,quadrature_degree=degree,apply_limiter=False)
        projected.append((degree,state.function.x.array.copy(),solver.mass(state)))
    reference=projected[-1][1]
    quadrature=[{"quadrature_degree":degree,"mass":mass,
        "relative_coefficient_difference_to_degree_16":float(np.linalg.norm(coeff-reference)/max(np.linalg.norm(reference),np.finfo(float).tiny))}
        for degree,coeff,mass in projected]
    return {"analytic_reference":"Gaussian normalized on the finite computational box",
        "resolutions":[list(x) for x in resolutions],"rows":rows,
        "projection_quadrature_convergence":{"cells":list(cells),"records":quadrature}}


def _propagate_particles(model,particles,t_final,dt,rng):
    particles=np.asarray(particles,float).copy(); B=np.asarray(model.B); steps=round(t_final/dt)
    for _ in range(steps):
        particles += model.drift_numpy(particles)*dt+rng.normal(size=particles.shape)@B.T*math.sqrt(dt)
    return particles


def same_initial_law_monte_carlo(cells=(20,24,24),dt=.000625,t_final=.05,
                                 n_particles=100000,seed=20260908,
                                 initialization="l2_projection",bootstrap_replicates=200,
                                 degree=1)->dict[str,object]:
    """FEM and SDE branches start from the identical limited native Q1 law."""
    model=Lorenz63Model(); solver=FokkerPlanckSolver(model,Domain(cells=tuple(cells)),dt,degree=degree)
    mean=np.array([1.,1.,20.]); cov=np.diag([4.,4.,9.])
    if initialization=="l2_projection":
        initial=solver.gaussian_projected(mean,cov,quadrature_degree=14,apply_limiter=True)
    elif initialization=="nodal_interpolation":
        initial=solver.gaussian_interpolated(mean,cov)
    else:
        raise ValueError("initialization must be l2_projection or nodal_interpolation")
    initial_metrics=gaussian_representation_metrics(solver,initial,mean,cov,16)
    rng=np.random.default_rng(seed)
    particles0=solver.sample_density(initial,n_particles,rng); sampling=dict(solver.last_sampling_report)
    initial_covariance=covariance_accuracy(np.asarray(solver.diagnostics(initial)["covariance"]),particles0,seed+17,bootstrap_replicates)
    out=solver.forecast(initial,0,t_final); fd=solver.diagnostics(out)
    particles=_propagate_particles(model,particles0,t_final,1.25e-4,rng)
    mc_mean=particles.mean(0); mc_cov=np.cov(particles,rowvar=False)
    covariance_report=covariance_accuracy(np.asarray(fd["covariance"]),particles,seed+991,bootstrap_replicates)
    tensor=solver.structured_export(out,1); voxel_probability=tensor*solver.domain.volume/tensor.size
    marginal_tv=[]
    for axis,((lo,hi),count) in enumerate(zip(solver.domain.bounds,solver.domain.cells)):
        fpe=voxel_probability.sum(axis=tuple(i for i in range(3) if i!=axis))
        mc=np.histogram(particles[:,axis],bins=count,range=(lo,hi))[0]/n_particles
        marginal_tv.append(float(.5*np.abs(fpe-mc).sum()))
    return {"comparison_label":"propagation disagreement from identical numerical initial law",
        "cells":list(cells),"degree":degree,"global_dofs":int(np.prod(cells)*(degree+1)**3),
        "dt":dt,"t_final":t_final,"initialization":initialization,
        "particles":n_particles,"mc_dt":1.25e-4,"seed":seed,
        "initial_representation_vs_analytic":initial_metrics,"native_sampling":sampling,
        "initial_sample_mean":particles0.mean(0).tolist(),"initial_sample_covariance":np.cov(particles0,rowvar=False).tolist(),
        "initial_sampling_covariance_accuracy":initial_covariance,
        "fpe_mean":fd["mean"],"mc_mean":mc_mean.tolist(),"mean_difference":(np.asarray(fd["mean"])-mc_mean).tolist(),
        "covariance_accuracy":covariance_report,"marginal_total_variation_distance":marginal_tv,
        "limiter_history":solver.limiter_history_summary(),"fpe_diagnostics":fd}


def analytic_bayesian_update_study(
    resolutions=((8,10,10),(12,16,16),(20,24,24)),quadrature_degree=14,degree=1,
)->dict[str,object]:
    """Nodal and projected likelihood products against conjugate Gaussian Bayes."""
    mean=np.array([1.,1.,20.]); covariance=np.array([[4.,.8,.3],[.8,5.,-.4],[.3,-.4,9.]])
    observation_model=ObservationModel.named("xz",4.0); H=np.asarray(observation_model.H); R=np.asarray(observation_model.R)
    observation=np.array([2.5,18.0]); innovation=observation-H@mean
    S=H@covariance@H.T+R; K=covariance@H.T@np.linalg.inv(S)
    exact_mean=mean+K@innovation
    I=np.eye(3); exact_cov=(I-K@H)@covariance@(I-K@H).T+K@R@K.T
    rows=[]
    for cells in resolutions:
        solver=FokkerPlanckSolver(Lorenz63Model(),Domain(cells=tuple(cells)),.00125,degree=degree)
        prior=solver.gaussian_projected(mean,covariance,quadrature_degree=quadrature_degree,apply_limiter=True)
        prior_metrics=gaussian_representation_metrics(solver,prior,mean,covariance,quadrature_degree+2)
        for method in ("nodal","projected"):
            posterior,analysis=BayesianAnalysis(solver,observation_model,method,quadrature_degree).update(prior,observation)
            metrics=gaussian_representation_metrics(solver,posterior,exact_mean,exact_cov,quadrature_degree+2)
            rows.append({"cells":list(cells),"method":method,"analysis":analysis,
                "prior_representation":prior_metrics,"posterior":metrics})
    return {"degree":degree,"prior_mean":mean.tolist(),"prior_covariance":covariance.tolist(),
        "observation_model":asdict(observation_model),"observation":observation.tolist(),
        "exact_posterior_mean":exact_mean.tolist(),"exact_posterior_covariance":exact_cov.tolist(),"rows":rows}


def manufactured_total_flux_boundary(
    resolutions=(4,6,8,12),dt=.00025,t_final=.01,quadrature_degree=12,
)->dict[str,object]:
    """Stationary exponential with nonzero advective and diffusive face fluxes.

    With p=C exp(a.x), D=I/2 and f=D a, both component fluxes are
    nonzero on appropriate exterior faces but their total J=f p-D grad p
    vanishes pointwise.  It therefore tests the combined no-flux treatment.
    """
    exponent=np.array([.4,-.3,.2]); velocity=.5*exponent
    domain_bounds=((-1.,1.),(-1.,1.),(-1.,1.)); rows=[]
    for n_cells in resolutions:
        model=ConstantModel(tuple(velocity)); solver=FokkerPlanckSolver(
            model,Domain(domain_bounds,(n_cells,)*3),dt)
        x=ufl.SpatialCoordinate(solver.mesh)
        raw=ufl.exp(sum(float(exponent[i])*x[i] for i in range(3)))
        normalizer=solver._integral(raw,quadrature_degree); exact=raw/normalizer
        initial=solver.project_expression(exact,"manufactured_total_flux",quadrature_degree,True,True)
        initial_limiter=dict(solver.last_projection_report)
        out=solver.forecast(initial,0,t_final)
        error=out.function-exact; evolution=out.function-initial.function
        normal=ufl.FacetNormal(solver.mesh); D=ufl.as_matrix(model.diffusion.tolist())
        f=model.drift_ufl(x); physical_trace=ufl.dot(f*out.function-ufl.dot(D,ufl.grad(out.function)),normal)
        boundary_local=fem.assemble_scalar(fem.form(physical_trace*physical_trace*ufl.ds))
        boundary_l2=math.sqrt(max(0.,float(solver.comm.allreduce(boundary_local))))
        rows.append({"cells_per_axis":n_cells,
            "advective_normal_speeds":{"x_minus":-velocity[0],"x_plus":velocity[0],
                "y_minus":-velocity[1],"y_plus":velocity[1],"z_minus":-velocity[2],"z_plus":velocity[2]},
            "analytic_total_flux":"identically zero",
            "l1_error":solver._integral(abs(error),quadrature_degree),
            "l2_error":math.sqrt(max(0.,solver._integral(error*error,quadrature_degree))),
            "l1_change_from_projected_initial":solver._integral(abs(evolution),quadrature_degree),
            "boundary_physical_flux_trace_l2":boundary_l2,
            "mass_error":abs(solver.mass(out)-1.),"minimum":solver.diagnostics(out)["minimum"],
            "initialization":initial_limiter,"limiter_history":solver.limiter_history_summary()})
    for i in range(1,len(rows)):
        ratio=resolutions[i]/resolutions[i-1]
        rows[i]["observed_l1_order"]=float(math.log(rows[i-1]["l1_error"]/rows[i]["l1_error"])/math.log(ratio))
        rows[i]["observed_l2_order"]=float(math.log(rows[i-1]["l2_error"]/rows[i]["l2_error"])/math.log(ratio))
    return {"manufactured_density":"C exp(0.4 x - 0.3 y + 0.2 z)",
        "diffusion":model.diffusion.tolist(),"velocity":velocity.tolist(),"dt":dt,"t_final":t_final,"rows":rows}


def higher_order_convergence_study(dt=.000625,t_final=.01,quadrature_degree=14)->dict[str,object]:
    """Q1/Q2 analytic accuracy, limiter impact, and cost on controlled grids."""
    domain=Domain(((-6.,6.),(-6.,6.),(-6.,6.)),(8,8,8))
    mean=np.array([-.4,.2,.1]); covariance=np.diag([.49,.64,.36]); velocity=np.array([.7,-.3,.2])
    exact_final_mean=mean+velocity*t_final; exact_final_cov=covariance+np.eye(3)*t_final
    groups={}
    for degree,resolutions in ((1,(8,12,16)),(2,(4,6,8))):
        rows=[]
        for n in resolutions:
            solver=FokkerPlanckSolver(ConstantModel(tuple(velocity)),
                Domain(domain.bounds,(n,n,n)),dt,degree=degree)
            initial=solver.gaussian_projected(mean,covariance,quadrature_degree=quadrature_degree,apply_limiter=True)
            initial_report=dict(solver.last_initialization_report); initial_error=gaussian_representation_metrics(
                solver,initial,mean,covariance,quadrature_degree+2)
            started=time.perf_counter(); out=solver.forecast(initial,0,t_final)
            wall=time.perf_counter()-started
            final_error=gaussian_representation_metrics(solver,out,exact_final_mean,exact_final_cov,quadrature_degree+2)
            rows.append({"degree":degree,"cells_per_axis":n,"global_dofs":n**3*(degree+1)**3,
                "initial_error":initial_error,"initialization":initial_report,"final_error":final_error,
                "forecast_wall_seconds":wall,"matrix_assembly_seconds":solver.matrix_assembly_seconds,
                "limiter_history":solver.limiter_history_summary()})
        for i in range(1,len(rows)):
            ratio=resolutions[i]/resolutions[i-1]
            for key in ("l1_error","l2_error"):
                rows[i][f"observed_{key.split('_')[0]}_order"]=float(math.log(
                    rows[i-1]["final_error"][key]/rows[i]["final_error"][key])/math.log(ratio))
        groups[f"Q{degree}"]=rows

    # Verify the exact moment-orthogonality statement before positivity.
    moment_checks=[]
    for degree in (1,2):
        solver=FokkerPlanckSolver(Lorenz63Model(),Domain(cells=(12,16,16)),.00125,degree=degree)
        state=solver.gaussian_projected((1.,1.,20.),np.diag([4.,4.,9.]),
                                        quadrature_degree=quadrature_degree,apply_limiter=False)
        moment_checks.append({"degree":degree,"unlimited_projection":gaussian_representation_metrics(
            solver,state,(1.,1.,20.),np.diag([4.,4.,9.]),quadrature_degree+2)})
    return {"dt":dt,"t_final":t_final,"groups":groups,
        "moment_preservation_check":moment_checks,
        "positivity":"Q1 uses whole-cell Bernstein/vertex positivity; Q2 uses Bernstein coefficients on 2x2x2 subcells"}


def independent_reference_and_mc_density_study(
    base_cells=(30,36,36), factors=(1,2), dt=.000625, t_final=.05,
    n_particles=200000, seed=20260909, bootstrap_replicates=200,
)->dict[str,object]:
    """Triangulate Q1 DG, an independent FV solver, and MC full densities.

    Every branch starts from the same Bernstein-positive native Q1 density.
    The finite-volume hierarchy receives its exact subcell averages, while MC
    uses exact rejection sampling from that polynomial.
    """
    from scipy.ndimage import gaussian_filter

    model=Lorenz63Model(); base_domain=Domain(cells=tuple(base_cells))
    solver=FokkerPlanckSolver(model,base_domain,dt,degree=1)
    initial=solver.gaussian_projected((1.,1.,20.),np.diag([4.,4.,9.]),
                                      quadrature_degree=14,apply_limiter=True)
    initial_report=dict(solver.last_initialization_report)
    fem_started=time.perf_counter(); fem=solver.forecast(initial,0,t_final)
    fem_seconds=time.perf_counter()-fem_started; fem_diag=solver.diagnostics(fem)

    fv_rows=[]; fv_results={}
    for factor in factors:
        cells=tuple(int(n*factor) for n in base_cells)
        fv=ConservativeFiniteVolume(model,Domain(base_domain.bounds,cells))
        initial_averages=solver.structured_export(initial,int(factor))
        result=fv.propagate(initial_averages,0,t_final)
        diagnostics=fv.diagnostics(result.density)
        fem_on_grid=solver.structured_export(fem,int(factor))
        voxel_volume=Domain(base_domain.bounds,cells).volume/np.prod(cells)
        pair_l1=float(np.abs(result.density-fem_on_grid).sum()*voxel_volume)
        fv_rows.append({"factor":int(factor),"cells":list(cells),
            "global_cells":int(np.prod(cells)),"maximum_stable_dt":fv.maximum_stable_step,
            "actual_steps":result.steps,"wall_seconds":result.wall_seconds,
            "working_density_bytes":int(result.density.nbytes),"diagnostics":diagnostics,
            "l1_difference_from_q1_dg":pair_l1,"tv_difference_from_q1_dg":.5*pair_l1})
        fv_results[int(factor)]=(fv,result)

    rng=np.random.default_rng(seed); sample_started=time.perf_counter()
    particles0=solver.sample_density(initial,n_particles,rng)
    sample_seconds=time.perf_counter()-sample_started
    propagation_started=time.perf_counter()
    particles=_propagate_particles(model,particles0,t_final,1.25e-4,rng)
    propagation_seconds=time.perf_counter()-propagation_started
    finest_factor=int(max(factors)); finest_fv,finest_result=fv_results[finest_factor]
    finest_cells=tuple(int(n*finest_factor) for n in base_cells)
    ranges=list(base_domain.bounds); histogram_started=time.perf_counter()
    counts,_=np.histogramdd(particles,bins=finest_cells,range=ranges)
    voxel_volume=base_domain.volume/np.prod(finest_cells)
    histogram_density=counts/(n_particles*voxel_volume)
    histogram_seconds=time.perf_counter()-histogram_started
    fem_finest=solver.structured_export(fem,finest_factor)

    def density_comparison(a,b):
        l1=float(np.abs(a-b).sum()*voxel_volume)
        l2=float(np.sqrt(((a-b)**2).sum()*voxel_volume))
        return {"l1":l1,"l2":l2,"total_variation":.5*l1}

    kde=[]
    for bandwidth in (.75,1.0,1.5,2.0):
        smoothed=gaussian_filter(counts,sigma=bandwidth,mode="constant")
        smoothed/=smoothed.sum()*voxel_volume
        kde.append({"bandwidth_in_voxels":bandwidth,
            "vs_finite_volume":density_comparison(smoothed,finest_result.density),
            "vs_q1_dg":density_comparison(smoothed,fem_finest),
            "minimum":float(smoothed.min())})

    batches=[]
    for i,batch in enumerate(np.array_split(particles,5)):
        bc,_=np.histogramdd(batch,bins=finest_cells,range=ranges)
        bd=bc/(len(batch)*voxel_volume)
        batches.append({"batch":i,"particles":len(batch),
            "vs_full_histogram":density_comparison(bd,histogram_density),
            "zero_voxel_fraction":float(np.mean(bc==0))})

    mc_cov=np.cov(particles,rowvar=False)
    fem_covariance=covariance_accuracy(np.asarray(fem_diag["covariance"]),particles,
                                        seed+41,bootstrap_replicates)
    fv_covariance=covariance_accuracy(np.asarray(finest_fv.diagnostics(finest_result.density)["covariance"]),
                                      particles,seed+42,bootstrap_replicates)
    finite_volume_prob=finest_result.density*voxel_volume
    low_expected=finite_volume_prob < 1.0/n_particles
    mc_prob=histogram_density*voxel_volume
    tail={"definition":"finest-FV voxels with expected count below one at the MC path count",
        "voxel_fraction":float(low_expected.mean()),
        "finite_volume_probability":float(finite_volume_prob[low_expected].sum()),
        "mc_histogram_probability":float(mc_prob[low_expected].sum()),
        "zero_histogram_voxel_fraction":float(np.mean(counts==0))}
    return {"comparison_label":"identical native Q1 initial law for all three branches",
        "base_cells":list(base_cells),"fem_degree":1,"fem_dt":dt,"t_final":t_final,
        "initialization":initial_report,"native_sampling":dict(solver.last_sampling_report),
        "q1_dg":{"wall_seconds":fem_seconds,"diagnostics":fem_diag,
            "limiter_history":solver.limiter_history_summary()},
        "finite_volume":{"method":"independent first-order upwind FV, centred diagonal diffusion, SSPRK(3,3), zero total boundary flux",
            "scope":"validator only; diagonal D; not a high-order production candidate","levels":fv_rows},
        "monte_carlo":{"particles":n_particles,"sde_dt":1.25e-4,"seed":seed,
            "sampling_seconds":sample_seconds,"propagation_seconds":propagation_seconds,
            "histogram_seconds":histogram_seconds,"sample_array_bytes":int(particles.nbytes),
            "mean":particles.mean(0).tolist(),"covariance":mc_cov.tolist(),
            "histogram_shape":list(finest_cells),"histogram_density_bytes":int(histogram_density.nbytes),
            "histogram_repeatability":batches,"kde_sensitivity":kde,"tail_resolution":tail},
        "finest_grid_full_density_comparisons":{
            "q1_dg_vs_finite_volume":density_comparison(fem_finest,finest_result.density),
            "mc_histogram_vs_finite_volume":density_comparison(histogram_density,finest_result.density),
            "mc_histogram_vs_q1_dg":density_comparison(histogram_density,fem_finest)},
        "covariance_vs_mc":{"q1_dg":fem_covariance,"finite_volume":fv_covariance}}


def common_initial_law_mc_timestep_sensitivity(
    cells=(30,36,36),n_particles=50000,t_final=.05,
    coarse_dt=1.25e-4,seed=20260910,
)->dict[str,object]:
    """Common-Brownian MC timestep check from the limited native Q1 law."""
    model=Lorenz63Model(); solver=FokkerPlanckSolver(model,Domain(cells=tuple(cells)),.000625)
    initial=solver.gaussian_projected((1.,1.,20.),np.diag([4.,4.,9.]),
                                      quadrature_degree=14,apply_limiter=True)
    rng=np.random.default_rng(seed); sampled=solver.sample_density(initial,n_particles,rng)
    coarse=sampled.copy(); fine=sampled.copy(); fine_dt=coarse_dt/2; B=np.asarray(model.B)
    started=time.perf_counter()
    for _ in range(round(t_final/coarse_dt)):
        z1=rng.normal(size=coarse.shape); z2=rng.normal(size=coarse.shape)
        coarse += model.drift_numpy(coarse)*coarse_dt + (z1+z2)@B.T*math.sqrt(fine_dt)
        fine += model.drift_numpy(fine)*fine_dt + z1@B.T*math.sqrt(fine_dt)
        fine += model.drift_numpy(fine)*fine_dt + z2@B.T*math.sqrt(fine_dt)
    cc,fc=np.cov(coarse,rowvar=False),np.cov(fine,rowvar=False)
    return {"comparison_label":"common initial samples and common Brownian increments",
        "cells":list(cells),"particles":n_particles,"seed":seed,"t_final":t_final,
        "coarse_dt":coarse_dt,"fine_dt":fine_dt,"wall_seconds":time.perf_counter()-started,
        "native_sampling":dict(solver.last_sampling_report),
        "coarse_mean":coarse.mean(0).tolist(),"fine_mean":fine.mean(0).tolist(),
        "mean_difference_coarse_minus_fine":(coarse.mean(0)-fine.mean(0)).tolist(),
        "coarse_covariance":cc.tolist(),"fine_covariance":fc.tolist(),
        "covariance_difference_coarse_minus_fine":(cc-fc).tolist(),
        "normalized_covariance_difference":float(np.linalg.norm(cc-fc)/np.linalg.norm(fc))}


def analytic_benchmarks(cells=(8,8,8),dt=.005,t_final=.02)->dict[str,object]:
    domain=Domain(((-6.,6.),(-6.,6.),(-6.,6.)),tuple(cells)); m0=np.array([-.4,.2,.1]); C0=np.diag([.49,.64,.36])
    results={}
    for name,velocity in (("pure_diffusion",(0.,0.,0.)),("constant_advection_diffusion",(.7,-.3,.2))):
        model=ConstantModel(velocity)
        solver=FokkerPlanckSolver(model,domain,dt)
        state=solver.gaussian(m0,C0)
        out=solver.forecast(state,0,t_final)
        exact_mean=m0+np.asarray(velocity)*t_final; exact_cov=C0+2*model.diffusion*t_final
        err=gaussian_errors(solver,out,exact_mean,exact_cov); diag=solver.diagnostics(out)
        results[name]={**err,"mass_error":abs(diag["mass"]-1),"minimum":diag["minimum"],
                       "mean_error":float(np.linalg.norm(np.asarray(diag["mean"])-exact_mean)),
                       "covariance_error":float(np.linalg.norm(np.asarray(diag["covariance"])-exact_cov)),
                       "diagnostics":diag}
    # A non-Gaussian propagation test: preservation of invariants is the target.
    solver=FokkerPlanckSolver(ConstantModel((.4,.1,-.2)),domain,dt)
    mix=solver.mixture([(-1.,0.,0.),(1.,.5,-.3)],[.3*np.eye(3),.45*np.eye(3)],[.4,.6])
    out=solver.forecast(mix,0,t_final); d=solver.diagnostics(out)
    results["non_gaussian"]={"mass_error":abs(d["mass"]-1),"minimum":d["minimum"],"diagnostics":d}
    return results


def monte_carlo_lorenz(cells=(20,24,24),dt=.00125,t_final=.05,n_particles=100000,seed=2026,
                       bootstrap_replicates=200,theta=1.0)->dict[str,object]:
    model=Lorenz63Model(); solver=FokkerPlanckSolver(model,Domain(cells=tuple(cells)),dt,theta)
    mean=np.array([1.,1.,20.]); cov=np.diag([2.,2.,3.])**2
    initial=solver.gaussian(mean,cov); out=solver.forecast(initial,0,t_final); fd=solver.diagnostics(out)
    rng=np.random.default_rng(seed); particles=rng.multivariate_normal(mean,cov,n_particles); h=2.5e-4; steps=round(t_final/h); B=np.asarray(model.B)
    for _ in range(steps): particles += model.drift_numpy(particles)*h + rng.normal(size=particles.shape)@B.T*math.sqrt(h)
    mc_mean=particles.mean(axis=0); mc_cov=np.cov(particles,rowvar=False); mean_se=np.sqrt(np.diag(mc_cov)/n_particles)
    covariance=covariance_accuracy(np.asarray(fd["covariance"]),particles,seed+991,bootstrap_replicates)
    path_counts=[n for n in (30000,60000,100000) if n<=n_particles]
    if n_particles not in path_counts: path_counts.append(n_particles)
    path_convergence=[]
    for count in path_counts:
        part=particles[:count]; c=np.cov(part,rowvar=False); m=part.mean(axis=0)
        path_convergence.append({"paths":count,"mean":m.tolist(),"mean_standard_error":np.sqrt(np.diag(c)/count).tolist(),
            "covariance":c.tolist(),"pde_mean_error":(np.asarray(fd["mean"])-m).tolist(),
            "pde_normalized_covariance_error":float(np.linalg.norm(np.asarray(fd["covariance"])-c)/np.linalg.norm(c))})
    batches=[]
    for i,part in enumerate(np.array_split(particles,5)):
        c=np.cov(part,rowvar=False); batches.append({"batch":i,"paths":len(part),"mean":part.mean(axis=0).tolist(),
            "covariance":c.tolist(),"normalized_covariance_deviation_from_full":float(np.linalg.norm(c-mc_cov)/np.linalg.norm(mc_cov))})
    vox=solver.structured_export(out); voxel_volume=solver.domain.volume/np.prod(solver.domain.cells); voxel_probability=vox*voxel_volume
    marginal_tv=[]
    for axis,((lo,hi),count) in enumerate(zip(solver.domain.bounds,solver.domain.cells)):
        fpe_prob=voxel_probability.sum(axis=tuple(i for i in range(3) if i!=axis))
        mc_prob=np.histogram(particles[:,axis],bins=count,range=(lo,hi))[0]/n_particles
        marginal_tv.append(float(.5*np.abs(fpe_prob-mc_prob).sum()))
    centers=[np.linspace(lo+(hi-lo)/(2*n),hi-(hi-lo)/(2*n),n) for (lo,hi),n in zip(solver.domain.bounds,solver.domain.cells)]
    X,_,Z=np.meshgrid(*centers,indexing="ij")
    mask=(X>0)&(Z>20); region_fpe=float(voxel_probability[mask].sum())
    # A cell-average tensor can represent only unions of whole voxels.  Use
    # the lower face of the first selected voxel as the identical MC cutoff.
    hz=(solver.domain.bounds[2][1]-solver.domain.bounds[2][0])/solver.domain.cells[2]
    selected_z=Z[mask]; effective_z_cut=float(selected_z.min()-hz/2)
    indicator=(particles[:,0]>0)&(particles[:,2]>effective_z_cut); region_mc=float(indicator.mean()); region_se=math.sqrt(region_mc*(1-region_mc)/n_particles)
    return {"particles":n_particles,"theta":theta,"fpe_mean":fd["mean"],"mc_mean":mc_mean.tolist(),"mc_mean_standard_error":mean_se.tolist(),
            "mean_difference":(np.asarray(fd["mean"])-mc_mean).tolist(),"covariance_accuracy":covariance,
            "path_count_convergence":path_convergence,"independent_batch_diagnostics":batches,
            "marginal_total_variation_distance":marginal_tv,
            "region_x_positive_z_high":{"nominal_z_cut":20.0,"effective_voxel_boundary_z_cut":effective_z_cut,
                "fpe_probability":region_fpe,"mc_probability":region_mc,"mc_standard_error":region_se},
            "limiter_history":solver.limiter_history_summary(),"fpe_diagnostics":fd}


def monte_carlo_time_step_check(n_particles=30000,t_final=.05,coarse_dt=.00025,seed=6611)->dict[str,object]:
    """Common-random-number Euler--Maruyama time-step sensitivity."""
    model=Lorenz63Model(); rng=np.random.default_rng(seed); mean=np.array([1.,1.,20.]); cov=np.diag([2.,2.,3.])**2
    coarse=rng.multivariate_normal(mean,cov,n_particles); fine=coarse.copy(); hf=coarse_dt/2; B=np.asarray(model.B)
    for _ in range(round(t_final/coarse_dt)):
        z1=rng.normal(size=coarse.shape); z2=rng.normal(size=coarse.shape)
        coarse += model.drift_numpy(coarse)*coarse_dt + (z1+z2)@B.T*math.sqrt(hf)
        fine += model.drift_numpy(fine)*hf + z1@B.T*math.sqrt(hf)
        fine += model.drift_numpy(fine)*hf + z2@B.T*math.sqrt(hf)
    cm, fm=coarse.mean(0),fine.mean(0); cc,fc=np.cov(coarse,rowvar=False),np.cov(fine,rowvar=False)
    return {"paths":n_particles,"coarse_dt":coarse_dt,"fine_dt":hf,"mean_difference_coarse_minus_fine":(cm-fm).tolist(),
        "covariance_difference_coarse_minus_fine":(cc-fc).tolist(),"covariance_frobenius_difference":float(np.linalg.norm(cc-fc)),
        "normalized_covariance_difference":float(np.linalg.norm(cc-fc)/np.linalg.norm(fc))}


def convergence_study()->dict[str,object]:
    records=[]
    for n,dt in ((6,.01),(8,.005),(10,.0025)):
        r=analytic_benchmarks((n,n,n),dt,.02)["constant_advection_diffusion"]
        records.append({"cells_per_axis":n,"dt":dt,"l1_error":r["l1_error"],"l2_error":r["l2_error"],
                        "mean_error":r["mean_error"],"covariance_error":r["covariance_error"]})
    for i in range(1,len(records)):
        ratio=np.log(records[i-1]["l1_error"]/records[i]["l1_error"])/np.log(records[i]["cells_per_axis"]/records[i-1]["cells_per_axis"])
        records[i]["observed_l1_rate_coupled_refinement"]=float(ratio)
    spatial=[]
    for n in (6,8,10):
        r=analytic_benchmarks((n,n,n),.00125,.02)["constant_advection_diffusion"]
        spatial.append({"cells_per_axis":n,"dt":.00125,"l1_error":r["l1_error"],"l2_error":r["l2_error"]})
    for i in range(1,len(spatial)):
        spatial[i]["observed_l1_order"]=float(np.log(spatial[i-1]["l1_error"]/spatial[i]["l1_error"])/
            np.log(spatial[i]["cells_per_axis"]/spatial[i-1]["cells_per_axis"]))
        spatial[i]["observed_l2_order"]=float(np.log(spatial[i-1]["l2_error"]/spatial[i]["l2_error"])/
            np.log(spatial[i]["cells_per_axis"]/spatial[i-1]["cells_per_axis"]))
    temporal=[]
    for step in (.01,.005,.0025,.00125):
        r=analytic_benchmarks((10,10,10),step,.02)["constant_advection_diffusion"]
        temporal.append({"cells_per_axis":10,"dt":step,"l1_error":r["l1_error"],"l2_error":r["l2_error"]})
    # Same-mesh Lorenz temporal self-convergence cancels the dominant spatial
    # error and exposes backward-Euler/limiter time error directly.
    levels=(.005,.0025,.00125,.000625,.0003125); temporal_states=[]
    temporal_cells=(12,16,16)
    for step in levels:
        s=FokkerPlanckSolver(Lorenz63Model(),Domain(cells=temporal_cells),step)
        out=s.forecast(s.gaussian((1.,1.,20.),np.diag([4.,4.,9.])),0,.02)
        temporal_states.append((step,s.structured_export(out,2),s.diagnostics(out)))
    ref=temporal_states[-1]; voxel_volume=Domain(cells=temporal_cells).volume/ref[1].size; temporal_self=[]
    for step,tensor,diag in temporal_states:
        delta=tensor-ref[1]
        temporal_self.append({"dt":step,"l1_difference_to_dt_ref":float(np.abs(delta).sum()*voxel_volume),
            "l2_difference_to_dt_ref":float(np.sqrt((delta*delta).sum()*voxel_volume)),
            "mean_difference_to_dt_ref":float(np.linalg.norm(np.asarray(diag["mean"])-np.asarray(ref[2]["mean"]))),
            "covariance_difference_to_dt_ref":float(np.linalg.norm(np.asarray(diag["covariance"])-np.asarray(ref[2]["covariance"])))})
    for i in range(1,len(temporal_self)-1):
        e0=temporal_self[i-1]["l1_difference_to_dt_ref"]; e1=temporal_self[i]["l1_difference_to_dt_ref"]
        temporal_self[i]["observed_l1_order"]=float(np.log(e0/e1)/np.log(2))
    return {"reference":"analytic translated/spread Gaussian","coupled_refinement":records,
            "spatial_refinement_fixed_dt":spatial,"temporal_refinement_fixed_mesh":temporal,
            "lorenz_temporal_self_convergence":{"cells":temporal_cells,"reference_dt":levels[-1],"records":temporal_self},
            "polynomial_degree":"This legacy convergence sequence is Q1 only; current Q2/Q3 use Bernstein control subcells",
            "note":"Preliminary engineering study. Spatial error dominates the fixed-mesh temporal sequence; finer meshes are required for an asymptotic publication study."}


def limiter_impact(cells=(12,16,16),dt=.0025,t_final=.05)->dict[str,object]:
    """Measure every limiter stage at every step of a Lorenz forecast."""
    solver=FokkerPlanckSolver(Lorenz63Model(),Domain(cells=tuple(cells)),dt)
    state=solver.gaussian((1.,1.,20.),np.diag([4.,4.,9.])); steps=round(t_final/dt); rows=[]; stage_observables=[]
    selected={0,steps//2,steps-1}
    for k in range(steps):
        state=solver.step(state); report=asdict(solver.last_limiter); report["step"]=k+1; report["time"]=state.time
        rows.append(report)
        if k in selected:
            stages=solver.limiter_stage_states(state.time); diag={name:solver.diagnostics(q) for name,q in stages.items()}
            raw,stage1,final=(diag[x] for x in ("raw","stage1","final"))
            stage_observables.append({"step":k+1,"time":state.time,
                "raw_to_stage1_mean_change":(np.asarray(stage1["mean"])-np.asarray(raw["mean"])).tolist(),
                "stage1_to_final_mean_change":(np.asarray(final["mean"])-np.asarray(stage1["mean"])).tolist(),
                "raw_to_final_covariance_frobenius_change":float(np.linalg.norm(np.asarray(final["covariance"])-np.asarray(raw["covariance"]))),
                "raw_to_final_entropy_change":float(final["entropy_cell_average"]-raw["entropy_cell_average"]),
                "raw":{x:raw[x] for x in ("mass","minimum","minimum_cell_average","mean","covariance","entropy_cell_average")},
                "stage1":{x:stage1[x] for x in ("mass","minimum","minimum_cell_average","mean","covariance","entropy_cell_average")},
                "final":{x:final[x] for x in ("mass","minimum","minimum_cell_average","mean","covariance","entropy_cell_average")}})
    keys=("raw_negative_cell_average_fraction","relative_l1_correction","raw_to_final_l2_correction",
          "corrected_fraction","minimum_scaling_factor","projection_seconds","scaling_seconds")
    summary={k:{"mean":float(np.mean([r[k] for r in rows])),"maximum":float(np.max([r[k] for r in rows]))} for k in keys}
    summary["steps_with_any_negative_raw_average"]=int(sum(r["raw_negative_cell_averages"]>0 for r in rows))
    summary["steps_with_scaling"]=int(sum(r["scaled_cells"]>0 for r in rows))
    severity=max(r["relative_l1_correction"] for r in rows)
    summary["classification"]="weak" if severity<1e-3 else ("material" if severity<1e-2 else "severe")
    return {"configuration":{"cells":cells,"dt":dt,"t_final":t_final},"per_step":rows,
            "selected_stage_observables":stage_observables,"aggregate":summary}


def voxel_projection_validation(cells=(12,16,16),dt=.0025,t_final=.05)->dict[str,object]:
    solver=FokkerPlanckSolver(Lorenz63Model(),Domain(cells=tuple(cells)),dt)
    state=solver.forecast(solver.gaussian((1.,1.,20.),np.diag([4.,4.,9.])),0,t_final)
    native=solver.diagnostics(state); rows=[]
    # 3-point quadrature within every subvoxel estimates piecewise-constant
    # reconstruction error against the native Q1 polynomial.
    gp,gw=np.polynomial.legendre.leggauss(3); gp=.5*(gp+1); gw=.5*gw
    for s in (1,2,4):
        tensor=solver.structured_export(state,s); shape=np.asarray(tensor.shape); widths=np.array([hi-lo for lo,hi in solver.domain.bounds])/shape
        reconstructed=solver.from_structured(tensor,state.time)
        volume=float(np.prod(widths)); probability=tensor*volume; mass=float(probability.sum())
        axes=[np.linspace(lo+h/2,hi-h/2,n) for (lo,hi),h,n in zip(solver.domain.bounds,widths,shape)]
        X=np.meshgrid(*axes,indexing="ij"); mean=np.array([float((probability*X[i]).sum()/mass) for i in range(3)])
        cov=np.empty((3,3))
        for i in range(3):
            for j in range(3):
                cov[i,j]=float((probability*(X[i]-mean[i])*(X[j]-mean[j])).sum()/mass)
                if i==j: cov[i,j]+=widths[i]**2/12
        ref_points=[]; ref_weights=[]; voxel_ids=[]
        for i in range(s):
            for j in range(s):
                for k in range(s):
                    for qi in range(3):
                        for qj in range(3):
                            for qk in range(3):
                                ref_points.append(((i+gp[qi])/s,(j+gp[qj])/s,(k+gp[qk])/s))
                                ref_weights.append(gw[qi]*gw[qj]*gw[qk]/s**3); voxel_ids.append((i,j,k))
        phi=np.asarray(solver.V.element.basix_element.tabulate(0,np.asarray(ref_points,dtype=np.float64))[0,:,:,0])
        l1=l2sq=roundtrip_l1=roundtrip_l2sq=0.0
        for c,dofs in enumerate(solver.limiter.cell_dofs):
            values=phi@state.function.x.array[dofs]
            reconstructed_values=phi@reconstructed.function.x.array[dofs]
            cell_mid=solver.mesh.geometry.x[solver.mesh.geometry.dofmaps[0][c]].mean(axis=0); base=[]
            for d,((lo,hi),n) in enumerate(zip(solver.domain.bounds,solver.domain.cells)):
                base.append(min(n-1,max(0,int(math.floor((cell_mid[d]-lo)/(hi-lo)*n)))))
            constants=np.array([tensor[base[0]*s+i,base[1]*s+j,base[2]*s+k] for i,j,k in voxel_ids])
            diff=values-constants; w=np.asarray(ref_weights)*solver.cell_volumes[c]
            l1+=float(w@np.abs(diff)); l2sq+=float(w@(diff*diff))
            roundtrip_diff=values-reconstructed_values
            roundtrip_l1+=float(w@np.abs(roundtrip_diff)); roundtrip_l2sq+=float(w@(roundtrip_diff*roundtrip_diff))
        rows.append({"subcells_per_dg_cell":s,"tensor_shape":tensor.shape,"mass_error":abs(mass-native["mass"]),
            "l1_shape_error":l1,"l2_shape_error":math.sqrt(l2sq),"mean_error":(mean-np.asarray(native["mean"])).tolist(),
            "covariance_frobenius_error":float(np.linalg.norm(cov-np.asarray(native["covariance"]))),
            "q1_roundtrip_l1_error":roundtrip_l1,"q1_roundtrip_l2_error":math.sqrt(roundtrip_l2sq),
            "q1_roundtrip_mass_error":abs(solver.mass(reconstructed)-native["mass"]),
            "minimum_voxel_density":float(tensor.min()),"storage_float64_bytes":int(tensor.size*8)})
    return {"cells":cells,"native":native,"refinements":rows}


def weighted_particle_da(cells=(20,24,24),dt=.00125,t_final=.05,n_particles=50000,seed=4401)->dict[str,object]:
    """One forecast-analysis cycle against an independent importance sample."""
    model=Lorenz63Model(); domain=Domain(cells=tuple(cells)); solver=FokkerPlanckSolver(model,domain,dt)
    obs_model=ObservationModel.named("xz",9.0); analysis=BayesianAnalysis(solver,obs_model)
    mean=np.array([1.,1.,20.]); cov=np.diag([2.,2.,3.])**2
    prior=solver.gaussian(mean,cov); forecast=solver.forecast(prior,0,t_final)
    truth=TruthSimulator(model).simulate((2.,-1.,22.),[t_final],seed)[0]
    obs_rng=np.random.default_rng(seed+1); observation=obs_model.observe(truth,obs_rng)
    posterior,ad=analysis.update(forecast,observation); pd=solver.diagnostics(posterior)

    rng=np.random.default_rng(seed+2); particles=rng.multivariate_normal(mean,cov,n_particles)
    h=2.5e-4; B=np.asarray(model.B)
    for _ in range(round(t_final/h)):
        particles += model.drift_numpy(particles)*h + rng.normal(size=particles.shape)@B.T*math.sqrt(h)
    H=np.asarray(obs_model.H); R=np.asarray(obs_model.R); inv=np.linalg.inv(R)
    residual=observation[None,:]-particles@H.T
    logw=-.5*np.einsum("ni,ij,nj->n",residual,inv,residual); logw-=logw.max()
    weights=np.exp(logw); weights/=weights.sum(); ess=1/float(weights@weights)
    wm=weights@particles; centered=particles-wm; wcov=(centered*weights[:,None]).T@centered
    posterior_sample=particles[rng.choice(n_particles,size=max(1000,int(ess)),replace=True,p=weights)]
    covariance=covariance_accuracy(np.asarray(pd["covariance"]),posterior_sample,seed+818,150)

    vox=solver.structured_export(posterior); voxel_prob=vox*domain.volume/np.prod(domain.cells); marginal_tv=[]
    for axis,((lo,hi),count) in enumerate(zip(domain.bounds,domain.cells)):
        fpe_prob=voxel_prob.sum(axis=tuple(i for i in range(3) if i!=axis))
        hist=np.histogram(particles[:,axis],bins=count,range=(lo,hi),weights=weights)[0]
        marginal_tv.append(float(.5*np.abs(fpe_prob-hist).sum()))
    return {"particles":n_particles,"effective_sample_size":ess,"truth":truth.tolist(),"observation":observation.tolist(),
            "fpe_posterior_mean":pd["mean"],"particle_posterior_mean":wm.tolist(),
            "mean_difference":(np.asarray(pd["mean"])-wm).tolist(),
            "fpe_posterior_covariance":pd["covariance"],"particle_posterior_covariance":wcov.tolist(),
            "covariance_frobenius_difference":float(np.linalg.norm(np.asarray(pd["covariance"])-wcov)),
            "normalized_covariance_frobenius_difference":float(np.linalg.norm(np.asarray(pd["covariance"])-wcov)/np.linalg.norm(wcov)),
            "posterior_resampling_covariance_uncertainty":covariance,
            "marginal_total_variation_distance":marginal_tv,"analysis_evidence":ad["evidence"],
            "fpe_diagnostics":pd,
            "caveat":"Self-normalised importance sampling is not exact; ESS reports weight degeneracy and Euler-Maruyama adds time-discretisation error."}


def domain_sensitivity()->dict[str,object]:
    # Expanded grid has exactly the same widths and aligned interior cells:
    # h=(6,20/3,20/3), with two extra cells on each side of every axis.
    configs=[("baseline",Domain(cells=(10,12,12))),
             ("expanded",Domain(((-42.,42.),(-160./3,160./3),(-70./3,250./3)),(14,16,16)))]
    rows=[]
    for name,domain in configs:
        s=FokkerPlanckSolver(Lorenz63Model(),domain,.0025)
        q=s.gaussian((1,1,20),np.diag([4.,4.,9.])); out=s.forecast(q,0,.05); d=s.diagnostics(out)
        rows.append({"name":name,"domain":domain.bounds,"cells":domain.cells,"mean":d["mean"],"covariance":d["covariance"],
                     "boundary_mass_fraction":d["boundary_mass_fraction"],"boundary_to_global_max_ratio":d["boundary_to_global_max_ratio"]})
    return {"runs":rows,"mean_difference_norm":float(np.linalg.norm(np.asarray(rows[0]["mean"])-np.asarray(rows[1]["mean"]))),
            "covariance_difference_frobenius":float(np.linalg.norm(np.asarray(rows[0]["covariance"])-np.asarray(rows[1]["covariance"]))) }


def run_validation(output:Path)->dict[str,object]:
    report={"analytic_benchmarks":analytic_benchmarks(),"monte_carlo":monte_carlo_lorenz(),
            "monte_carlo_time_step":monte_carlo_time_step_check(),
            "weighted_particle_da":weighted_particle_da(),"convergence":convergence_study(),
            "limiter_impact":limiter_impact(),"voxel_projection":voxel_projection_validation(),
            "domain_sensitivity":domain_sensitivity()}
    write_json(output,report); return report
