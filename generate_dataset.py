#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
from lorenz_fpe import Domain,FokkerPlanckSolver,Lorenz63Model
from lorenz_fpe.dataset import DatasetConfig,DatasetGenerator

p=argparse.ArgumentParser(description="Generate post-burn-in Lorenz-63 DA operator pairs")
p.add_argument("--output",type=Path,default=Path("sample_dataset")); p.add_argument("--trajectories",type=int,default=5)
p.add_argument("--cycles",type=int,default=10); p.add_argument("--burn-in",type=int,default=4); p.add_argument("--obs-interval",type=float,default=.05)
p.add_argument("--observation",choices=("x","xz","full"),default="xz"); p.add_argument("--obs-variance",type=float,default=4.)
p.add_argument("--cells",nargs=3,type=int,default=(12,16,16)); p.add_argument("--dt",type=float,default=.0025); p.add_argument("--seed",type=int,default=1729)
p.add_argument("--theta",type=float,choices=(0.5,1.0),default=1.0)
p.add_argument("--degree",type=int,choices=(1,2,3),default=1)
p.add_argument("--export-subcells",type=int,default=None,help="Subvoxels per DG cell axis; default degree+1 permits polynomial round-trip")
p.add_argument("--max-limiter-relative-l1",type=float,default=.005,help="Reject cycles whose maximum raw-to-limited relative L1 correction exceeds this")
p.add_argument("--quadrature-degree",type=int,default=14)
p.add_argument("--analysis",choices=("nodal","projected"),default="projected")
p.add_argument("--noise-matrix",nargs=9,type=float,default=None)
a=p.parse_args(); B=np.eye(3) if a.noise_matrix is None else np.asarray(a.noise_matrix).reshape(3,3)
model=Lorenz63Model(B=tuple(tuple(float(x) for x in row) for row in B))
solver=FokkerPlanckSolver(model,Domain(cells=tuple(a.cells)),a.dt,a.theta,a.degree)
export_subcells=a.export_subcells or a.degree+1
config=DatasetConfig(a.trajectories,a.cycles,a.burn_in,a.obs_interval,a.observation,a.obs_variance,
    a.seed,export_subcells,a.max_limiter_relative_l1,a.quadrature_degree,a.analysis)
DatasetGenerator(solver,config).generate(a.output)
