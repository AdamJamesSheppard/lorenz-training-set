#!/usr/bin/env python3
"""Small strong-scaling benchmark with component timing."""
from __future__ import annotations
import argparse,json,tempfile,time
from pathlib import Path
import numpy as np
from mpi4py import MPI
from lorenz_fpe import Domain,FokkerPlanckSolver,Lorenz63Model

p=argparse.ArgumentParser(); p.add_argument("--cells",nargs=3,type=int,default=(20,24,24)); p.add_argument("--dt",type=float,default=.00125)
p.add_argument("--degree",type=int,choices=(1,2,3),default=1); p.add_argument("--steps",type=int,default=5)
p.add_argument("--export-subcells",type=int,default=None); p.add_argument("--output",type=Path)
a=p.parse_args(); comm=MPI.COMM_WORLD; started=time.perf_counter()
s=FokkerPlanckSolver(Lorenz63Model(),Domain(cells=tuple(a.cells)),a.dt,degree=a.degree); setup=max(comm.allgather(time.perf_counter()-started))
export_subcells=a.export_subcells or a.degree+1
state=s.gaussian((1,1,20),np.diag([4.,4.,9.])); state=s.step(state) # compile/warm up
rows=[]
for _ in range(a.steps): state=s.step(state); rows.append(dict(s.last_timing))
t=time.perf_counter(); d=s.diagnostics(state); diagnostic=max(comm.allgather(time.perf_counter()-t))
t=time.perf_counter(); tensor=s.structured_export(state,export_subcells); export=max(comm.allgather(time.perf_counter()-t))
comm.barrier(); t=time.perf_counter()
if comm.rank==0:
    with tempfile.NamedTemporaryFile(suffix=".npy") as f: np.save(f,tensor); f.flush()
output=max(comm.allgather(time.perf_counter()-t))
result={"mpi_ranks":comm.size,"cells":a.cells,"degree":a.degree,"global_cells":int(np.prod(a.cells)),
 "global_dofs":int(np.prod(a.cells)*(a.degree+1)**3),"steps":a.steps,"dt":a.dt,"export_subcells":export_subcells,
 "setup_seconds":setup,"matrix_assembly_seconds":s.matrix_assembly_seconds,
 "mean_step_seconds":float(np.mean([x["step_seconds"] for x in rows])),
 "mean_rhs_seconds":float(np.mean([x["rhs_seconds"] for x in rows])),
 "mean_solve_seconds":float(np.mean([x["solve_seconds"] for x in rows])),
 "mean_residual_seconds":float(np.mean([x["residual_seconds"] for x in rows])),
 "mean_limiter_seconds":float(np.mean([x["limiter_seconds"] for x in rows])),
 "diagnostics_seconds":diagnostic,"export_seconds":export,"file_output_seconds":output,
 "last_true_relative_residual":d["linear_solver"]["true_relative_residual"],
 "last_mass_error":abs(d["mass"]-1),"last_relative_l1_limiter_correction":d["limiter"]["relative_l1_correction"]}
if comm.rank==0:
    print(json.dumps(result,indent=2),flush=True)
    if a.output: a.output.write_text(json.dumps(result,indent=2))
