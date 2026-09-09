#!/usr/bin/env python3
"""Exploratory multi-trajectory stationarity and coverage study."""
from __future__ import annotations
import argparse,json,math,time
from pathlib import Path
import numpy as np
from lorenz_fpe import BayesianAnalysis,Domain,FokkerPlanckSolver,Lorenz63Model,ObservationModel,TruthSimulator
from lorenz_fpe.core import solver_metadata,write_json
from lorenz_fpe.dataset import DatasetGenerator,DatasetSplitter

def tensor_stats(a,domain):
    a=np.asarray(a,float); shape=np.asarray(a.shape); widths=np.array([hi-lo for lo,hi in domain.bounds])/shape
    vol=float(np.prod(widths)); prob=a*vol; mass=float(prob.sum()); prob/=mass
    axes=[np.linspace(lo+h/2,hi-h/2,n) for (lo,hi),h,n in zip(domain.bounds,widths,shape)]
    xyz=np.meshgrid(*axes,indexing="ij"); mean=np.array([(prob*xyz[i]).sum() for i in range(3)])
    cov=np.empty((3,3)); skew=[]; kurt=[]
    for i in range(3):
        for j in range(3): cov[i,j]=(prob*(xyz[i]-mean[i])*(xyz[j]-mean[j])).sum()+(widths[i]**2/12 if i==j else 0)
        var=max(cov[i,i],np.finfo(float).tiny)
        skew.append(float((prob*(xyz[i]-mean[i])**3).sum()/var**1.5))
        kurt.append(float((prob*(xyz[i]-mean[i])**4).sum()/var**2-3))
    entropy=-float(np.sum(np.where(prob>0,prob*np.log(np.maximum(a,np.finfo(float).tiny)),0)))
    return {"mass":mass,"mean":mean.tolist(),"covariance_eigenvalues":np.linalg.eigvalsh(cov).tolist(),
        "covariance_trace":float(np.trace(cov)),"covariance_log_determinant":float(np.linalg.slogdet(cov)[1]),
        "entropy":entropy,"effective_support":math.exp(entropy),"skewness":skew,"excess_kurtosis":kurt,
        "mode_count":DatasetGenerator._mode_count(a),"boundary_mass":float((prob[0].sum()+prob[-1].sum()+prob[:,0].sum()+prob[:,-1].sum()+prob[:,:,0].sum()+prob[:,:,-1].sum()))}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--output",type=Path,default=Path("mature_da_report.json")); p.add_argument("--trajectories",type=int,default=20)
    p.add_argument("--cycles",type=int,default=20); p.add_argument("--observation",choices=("x","xz","full"),default="xz")
    p.add_argument("--cells",nargs=3,type=int,default=(8,10,10)); p.add_argument("--dt",type=float,default=.005); p.add_argument("--obs-interval",type=float,default=.05)
    p.add_argument("--degree",type=int,choices=(1,2,3),default=1)
    p.add_argument("--analysis",choices=("nodal","projected"),default="projected")
    p.add_argument("--quadrature-degree",type=int,default=14)
    p.add_argument("--obs-variance",type=float,default=9.); p.add_argument("--seed",type=int,default=71023); a=p.parse_args()
    domain=Domain(cells=tuple(a.cells)); solver=FokkerPlanckSolver(Lorenz63Model(),domain,a.dt,degree=a.degree); obs_model=ObservationModel.named(a.observation,a.obs_variance)
    rows=[]; started=time.perf_counter()
    for j in range(a.trajectories):
        rng=np.random.default_rng(a.seed+10007*j); analysis=BayesianAnalysis(
            solver,obs_model,a.analysis,a.quadrature_degree)
        mean=np.array([1.,1.,20.])+rng.normal(0,[3,3,5]); std=rng.uniform([2,2,3],[5,5,8])
        posterior=solver.gaussian_projected(mean,np.diag(std**2),
            quadrature_degree=a.quadrature_degree,apply_limiter=True)
        times=np.arange(1,a.cycles+1)*a.obs_interval; truth0=np.array([1.,1.,20.])+rng.normal(0,[4,4,6])
        truth=TruthSimulator(solver.model).simulate(truth0,times,a.seed+10007*j+1); observations=np.stack([obs_model.observe(q,rng) for q in truth])
        previous=None
        for k,(target,y) in enumerate(zip(times,observations)):
            forecast=solver.forecast(posterior,posterior.time,float(target)); limiter=solver.limiter_history_summary()
            posterior,analysis_report=analysis.update(forecast,y); tensor=solver.structured_export(posterior,a.degree+1); stats=tensor_stats(tensor,domain)
            stats.update({"trajectory_id":f"trajectory_{j:06d}","cycle":k,"successive_tv":None if previous is None else float(.5*np.abs(tensor-previous).sum()*domain.volume/tensor.size),
                "limiter_mean_relative_l1":limiter["relative_l1_correction"]["mean"],"limiter_max_relative_l1":limiter["relative_l1_correction"]["maximum"],
                "analysis_limiter_relative_l1":analysis_report["limiter_relative_l1_correction"]})
            rows.append(stats); previous=tensor
        print(f"trajectory {j+1}/{a.trajectories} elapsed={time.perf_counter()-started:.1f}s",flush=True)

    feature_names=["entropy","covariance_trace","covariance_log_determinant","effective_support","limiter_mean_relative_l1","successive_tv"]
    cycle_summary=[]
    for k in range(a.cycles):
        rr=[r for r in rows if r["cycle"]==k]; summary={"cycle":k,"n":len(rr)}
        for name in feature_names:
            values=np.array([r[name] for r in rr if r[name] is not None],float)
            summary[name]={"mean":float(values.mean()) if len(values) else None,"std":float(values.std(ddof=1)) if len(values)>1 else None}
        summary["mean_covariance_eigenvalues"]=np.mean([r["covariance_eigenvalues"] for r in rr],axis=0).tolist()
        summary["mean_absolute_skewness"]=np.mean(np.abs([r["skewness"] for r in rr]),axis=0).tolist()
        summary["mean_excess_kurtosis"]=np.mean([r["excess_kurtosis"] for r in rr],axis=0).tolist()
        summary["mean_mode_count"]=float(np.mean([r["mode_count"] for r in rr])); cycle_summary.append(summary)

    # Reference operational window is the final five cycles.  A candidate
    # burn-in is accepted only when every subsequent cycle mean stays within
    # half a final-window between-trajectory standard deviation for core scale statistics.
    stationarity_features=["entropy","covariance_trace","covariance_log_determinant","effective_support"]
    window=min(5,a.cycles); ref_rows=[r for r in rows if r["cycle"]>=a.cycles-window]
    ref_mean={f:float(np.mean([r[f] for r in ref_rows])) for f in stationarity_features}
    ref_std={f:float(np.std([r[f] for r in ref_rows],ddof=1)) for f in stationarity_features}
    z_by_cycle=[]
    for summary in cycle_summary:
        z=max(abs(summary[f]["mean"]-ref_mean[f])/max(ref_std[f],np.finfo(float).tiny) for f in stationarity_features)
        z_by_cycle.append(float(z))
    burn_in=None
    for k in range(max(0,a.cycles-window)):
        if max(z_by_cycle[k:])<=.5: burn_in=k; break

    proposed=burn_in if burn_in is not None else max(0,a.cycles-window); mature=[r for r in rows if r["cycle"]>=proposed]
    ids=sorted({r["trajectory_id"] for r in rows}); split=DatasetSplitter.split(ids,a.seed)
    vector_names=["entropy","covariance_trace","covariance_log_determinant","effective_support"]
    X=np.array([[r[n] for n in vector_names] for r in mature]); labels=[r["trajectory_id"] for r in mature]
    train_mask=np.array([x in split["train_trajectory_ids"] for x in labels]); mu=X[train_mask].mean(0); sd=X[train_mask].std(0); Z=(X-mu)/np.maximum(sd,1e-14)
    _,singular,Vt=np.linalg.svd(Z[train_mask],full_matrices=False); scores=Z@Vt[:2].T
    train_min=X[train_mask].min(0); train_max=X[train_mask].max(0)
    coverage={}
    for split_name,key in (("validation","validation_trajectory_ids"),("test","test_trajectory_ids")):
        mask=np.array([x in split[key] for x in labels]); inside=((X[mask]>=train_min)&(X[mask]<=train_max)).all(1)
        dist=np.sqrt(((scores[mask,None,:]-scores[train_mask][None,:,:])**2).sum(2)).min(1) if mask.any() else np.array([])
        coverage[split_name]={"states":int(mask.sum()),"fraction_inside_training_feature_box":float(inside.mean()) if len(inside) else None,
            "mean_nearest_train_distance_pca2":float(dist.mean()) if len(dist) else None,"max_nearest_train_distance_pca2":float(dist.max()) if len(dist) else None}
    configuration={k:(str(v) if isinstance(v,Path) else v) for k,v in vars(a).items()}
    report={"classification":"regenerated_with_projected_analysis; exploratory_coarse_distribution_study_not_ground_truth","configuration":configuration,"solver":solver_metadata(solver),
        "cycle_summary":cycle_summary,"stationarity":{"reference_window":[a.cycles-window,a.cycles-1],"features":stationarity_features,
            "max_standardized_difference_by_cycle":z_by_cycle,"criterion":"all subsequent cycle means within 0.5 final-window SD",
            "evidence_based_burn_in":burn_in,"recommended_provisional_burn_in":proposed,
            "conclusion":"criterion_met" if burn_in is not None else "no stable burn-in established in available horizon"},
        "coverage":{"features":vector_names,"pca_singular_values":singular.tolist(),"trajectory_split":split,**coverage},
        "rows":rows,"wall_seconds":time.perf_counter()-started}
    write_json(a.output,report); print(json.dumps({"stationarity":report["stationarity"],"coverage":coverage,"wall_seconds":report["wall_seconds"]},indent=2))
if __name__=="__main__": main()
