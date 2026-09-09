#!/usr/bin/env python3
"""Run the initialization and Bayesian-analysis validation repair phases."""
from __future__ import annotations
import argparse
from pathlib import Path
from lorenz_fpe.core import write_json
from lorenz_fpe.validation import (analytic_bayesian_update_study,
    initialization_representation_study,same_initial_law_monte_carlo)

p=argparse.ArgumentParser()
p.add_argument("--output",type=Path,default=Path("validation_repair_report.json"))
p.add_argument("--particles",type=int,default=100000)
p.add_argument("--bootstrap",type=int,default=200)
a=p.parse_args()

report={
    "initial_representation":initialization_representation_study(),
    "analytic_bayesian_update":analytic_bayesian_update_study(),
    "same_initial_law_monte_carlo":[
        same_initial_law_monte_carlo(cells,(.000625 if cells==(30,36,36) else .00125),
            n_particles=a.particles,seed=20260908+i,initialization=method,
            bootstrap_replicates=a.bootstrap)
        for i,(cells,method) in enumerate((((20,24,24),"nodal_interpolation"),
                                            ((20,24,24),"l2_projection"),
                                            ((30,36,36),"l2_projection")))
    ],
}
write_json(a.output,report)
