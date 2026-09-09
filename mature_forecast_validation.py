#!/usr/bin/env python3
"""Validate forecasts from non-Gaussian post-burn-in DG posterior states."""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
import numpy as np
from lorenz_fpe import Domain,FokkerPlanckSolver,Lorenz63Model
from lorenz_fpe.core import write_json
from lorenz_fpe.validation import covariance_accuracy

def sample_q1(solver,state,n,rng):
    av,vol,_=solver.cell_averages(state); probability=np.maximum(av,0)*vol; probability/=probability.sum()
    cells=rng.choice(len(av),size=n,p=probability); out=np.empty((n,3)); gd=solver.mesh.geometry.dofmaps[0]; geom=solver.mesh.geometry.x
    for cell in np.unique(cells):
        target=np.flatnonzero(cells==cell); coeff=state.function.x.array[solver.V.dofmap.cell_dofs(int(cell))]; vmax=max(float(coeff.max()),np.finfo(float).tiny)
        accepted=[]; needed=len(target)
        while sum(len(x) for x in accepted)<needed:
            points=rng.random((max(32,2*needed),3)); phi=solver.V.element.basix_element.tabulate(0,np.asarray(points,dtype=np.float64))[0,:,:,0]
            values=phi@coeff; keep=points[rng.random(len(points))<np.clip(values/vmax,0,1)]; accepted.append(keep)
        ref=np.concatenate(accepted)[:needed]; xyz=geom[gd[int(cell)]]; lo=xyz.min(0); hi=xyz.max(0); out[target]=lo+ref*(hi-lo)
    return out

def main():
    p=argparse.ArgumentParser(); p.add_argument("--dataset",type=Path,default=Path("sample_dataset")); p.add_argument("--output",type=Path,default=Path("mature_forecast_validation.json"))
    p.add_argument("--particles",type=int,default=50000); p.add_argument("--seed",type=int,default=8841); a=p.parse_args()
    candidates=[]
    for path in a.dataset.glob("trajectories/trajectory_*/cycle_*/diagnostics.json"):
        d=json.loads(path.read_text()); k=d["cycle"]
        if k<3: continue
        q=d["input_posterior"]; cov=np.asarray(q["covariance"])
        candidates.append({"path":path.parent,"trace":float(np.trace(cov)),"skew":max(abs(x) for x in q["marginal_skewness"])})
    choices=[min(candidates,key=lambda x:x["trace"]),max(candidates,key=lambda x:x["trace"]),max(candidates,key=lambda x:x["skew"])]
    unique=[]
    for q in choices:
        if q["path"] not in [x["path"] for x in unique]: unique.append(q)
    solver=FokkerPlanckSolver(Lorenz63Model(),Domain(cells=(12,16,16)),.0025); rng=np.random.default_rng(a.seed); reports=[]
    for index,item in enumerate(unique):
        initial=solver.load_native(item["path"]/"posterior_native.npz"); particles=sample_q1(solver,initial,a.particles,rng)
        forecast=solver.forecast(initial,initial.time,initial.time+.05); fd=solver.diagnostics(forecast)
        h=.00025; B=np.asarray(solver.model.B)
        for _ in range(round(.05/h)): particles += solver.model.drift_numpy(particles)*h+rng.normal(size=particles.shape)@B.T*math.sqrt(h)
        mc_mean=particles.mean(0); mc_cov=np.cov(particles,rowvar=False); tensor=solver.structured_export(forecast,1); vol=solver.domain.volume/tensor.size
        tv=[]
        for axis,((lo,hi),count) in enumerate(zip(solver.domain.bounds,solver.domain.cells)):
            fp=tensor.sum(axis=tuple(i for i in range(3) if i!=axis))*vol; mp=np.histogram(particles[:,axis],bins=count,range=(lo,hi))[0]/a.particles
            tv.append(float(.5*np.abs(fp-mp).sum()))
        reports.append({"selection":("narrow","broad","skewed")[index],"cycle_path":str(item["path"]),
            "input_trace":item["trace"],"input_max_abs_skewness":item["skew"],"particles":a.particles,
            "fpe_mean":fd["mean"],"mc_mean":mc_mean.tolist(),"mean_error":(np.asarray(fd["mean"])-mc_mean).tolist(),
            "covariance_accuracy":covariance_accuracy(np.asarray(fd["covariance"]),particles,a.seed+index,150),
            "marginal_total_variation_distance":tv,"limiter_history":solver.limiter_history_summary(),"fpe_diagnostics":fd})
        print(item["path"],reports[-1]["covariance_accuracy"]["normalized_frobenius_error"],tv,flush=True)
    write_json(a.output,{"classification":"mature DA forecast validation from full native DG posteriors; no Gaussianisation",
        "initial_sampling":"exact rejection sampling from non-negative Q1 polynomial on each selected cell",
        "reports":reports})
if __name__=="__main__": main()
