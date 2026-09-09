#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
import numpy as np
from lorenz_fpe import Domain, FokkerPlanckSolver, Lorenz63Model
from lorenz_fpe.core import solver_metadata

p=argparse.ArgumentParser(description="Positivity-limited DG(Qk) Lorenz-63 Fokker--Planck forecast")
p.add_argument("--cells",nargs=3,type=int,default=(12,16,16),metavar=("NX","NY","NZ")); p.add_argument("--dt",type=float,default=.0025)
p.add_argument("--theta",type=float,choices=(0.5,1.0),default=1.0,help="1=backward Euler; 0.5=experimental Crank-Nicolson plus positivity postprocessing")
p.add_argument("--degree",type=int,choices=(1,2,3),default=1)
p.add_argument("--initialization",choices=("projected","nodal"),default="projected")
p.add_argument("--quadrature-degree",type=int,default=14)
p.add_argument("--t-final",type=float,default=.25); p.add_argument("--mean",nargs=3,type=float,default=(1,1,20)); p.add_argument("--std",nargs=3,type=float,default=(3,3,5))
p.add_argument("--noise-matrix",nargs=9,type=float,default=None,metavar=("B11","B12","B13","B21","B22","B23","B31","B32","B33"))
a=p.parse_args(); B=np.eye(3) if a.noise_matrix is None else np.asarray(a.noise_matrix).reshape(3,3)
model=Lorenz63Model(B=tuple(tuple(float(x) for x in row) for row in B))
solver=FokkerPlanckSolver(model,Domain(cells=tuple(a.cells)),a.dt,a.theta,a.degree)
metadata=solver_metadata(solver)
if solver.comm.rank==0: print(json.dumps(metadata,indent=2),flush=True)
q=(solver.gaussian_projected(a.mean,np.diag(np.asarray(a.std)**2),quadrature_degree=a.quadrature_degree)
   if a.initialization=="projected" else solver.gaussian_interpolated(a.mean,np.diag(np.asarray(a.std)**2)))
out=solver.forecast(q,0,a.t_final,progress=True)
diagnostics=solver.diagnostics(out)
if solver.comm.rank==0: print(json.dumps(diagnostics,indent=2),flush=True)
