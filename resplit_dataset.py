#!/usr/bin/env python3
"""Recompute trajectory-level train/validation/test split for a dataset."""
import argparse,json
from pathlib import Path
from lorenz_fpe.core import write_json
from lorenz_fpe.dataset import DatasetSplitter
p=argparse.ArgumentParser(); p.add_argument("dataset",type=Path); p.add_argument("--seed",type=int,default=1729); a=p.parse_args()
path=a.dataset/"dataset_manifest.json"; manifest=json.loads(path.read_text())
ids=sorted({r["trajectory_id"] for r in manifest["all_cycle_records"]})
manifest.update(DatasetSplitter.split(ids,a.seed)); write_json(path,manifest)
print(json.dumps({k:manifest[k] for k in ("train_trajectory_ids","validation_trajectory_ids","test_trajectory_ids")},indent=2))
