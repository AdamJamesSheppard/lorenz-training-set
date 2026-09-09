import json
import numpy as np
from lorenz_fpe import Domain,FokkerPlanckSolver,Lorenz63Model
s=FokkerPlanckSolver(Lorenz63Model(),Domain(cells=(4,6,6)),.01)
q=s.gaussian((1,1,20),np.diag([4.,4.,9.])); q=s.forecast(q,0,.02); d=s.diagnostics(q)
if s.comm.rank==0:
    print("MPI_PROBE="+json.dumps({"mass":d["mass"],"l2":d["l2"],"mean":d["mean"],
        "relative_l1_correction":d["limiter"]["relative_l1_correction"],"minimum":d["minimum"]}),flush=True)
