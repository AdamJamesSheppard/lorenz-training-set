#!/usr/bin/env python3
from pathlib import Path
import argparse,json
from lorenz_fpe.validation import run_validation
p=argparse.ArgumentParser(); p.add_argument("--output",type=Path,default=Path("validation_report.json")); a=p.parse_args()
r=run_validation(a.output); print(json.dumps(r,indent=2))
