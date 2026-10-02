#!/usr/bin/env python3
"""Run a frozen-depth broader-support experiment in an immutable directory."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone
import numpy as np
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--half-timestep', action='store_true')
options = parser.parse_args()
temporal = options.half_timestep

repo = Path(__file__).resolve().parents[1]
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
run = repo / ('runs/mfem-mature-half-timestep' if temporal else 'runs/mfem-broader-support') / stamp
run.mkdir(parents=True, exist_ok=False)
(run / 'mfem').mkdir()
print(str(run), flush=True)
pde = '/home/adam/.local/share/mamba/envs/pde/bin/python'
envroot = Path('/home/adam/.local/share/mamba/envs/mfem-lorenz')
baseline = repo / ('runs/mfem-broader-support/20261002T080644Z' if temporal else 'runs/mfem-support-sensitivity/20261001T144235Z')
first = repo / 'runs/mfem-static-amr-reproduction/20260916T221235Z'
binary = repo / ('build/mfem-physical-equivalence/mfem_half_timestep' if temporal else 'build/mfem-physical-equivalence/mfem_physical_equivalence')

def status(value, **extras):
    (run / 'status.json').write_text(json.dumps(dict(status=value, **extras), indent=2))

try:
    status('PREPARING_BROADER_SUPPORT')
    shutil.copyfile(repo / ('experiments/mfem-mature-half-timestep.yaml' if temporal else 'experiments/mfem-broader-support.yaml'), run / 'config.yaml')
    for command, filename in [(['rev-parse', 'HEAD'], 'git_commit.txt'), (['status', '--short'], 'git_status.txt')]:
        (run / filename).write_bytes(subprocess.check_output(['git', '-C', str(repo), *command]))
    if temporal:
        shutil.copytree(baseline / 'design', run / 'design')
    else:
        subprocess.run([pde, '-B', str(repo / 'mfem/prepare_support_test.py'), str(repo), str(run / 'design'), '--coverage', '0.99', '--buffer', '1'], check=True)
    inputs = [binary, repo / 'mfem/prepare_support_test.py', repo / 'mfem/compare_support_test.py', Path(__file__), first / 'design/mixture_parameters.bin', baseline / 'mfem/initial_q2_subcell_averages.bin', baseline / 'mfem/final_q2_subcell_averages.bin', baseline / 'design/child_cell_marks.bin', repo / 'runs/mfem-static-amr-level2/20260922T231219Z/mfem/final_q2_subcell_averages.bin', repo / 'runs/mfem-static-amr-level3/20260923T181337Z/mfem/final_q2_subcell_averages.bin', run / 'design/base_cell_marks.bin', run / 'design/child_cell_marks.bin']
    (run / 'input_sha256.json').write_text(json.dumps({str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}, indent=2))
    environment = dict(os.environ, PATH=str(envroot / 'bin') + ':' + os.environ['PATH'], OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    command = [str(envroot / 'bin/mpiexec'), '-n', '8', str(binary), 'amr2', '45', '54', '54', str(run / 'design/base_cell_marks.bin'), str(run / 'design/child_cell_marks.bin'), str(first / 'design/mixture_parameters.bin'), str(run / 'mfem')]
    if temporal:
        command.append('640')
    (run / 'command.json').write_text(json.dumps(command, indent=2))
    (run / 'environment.txt').write_bytes(subprocess.check_output([str(envroot / 'bin/mpiexec'), '--version']))
    status('RUNNING_HALF_TIMESTEP' if temporal else 'RUNNING_BROADER_SUPPORT', steps=640 if temporal else 320)
    subprocess.run(command, env=environment, check=True)
    audit = subprocess.run([pde, '-B', str(repo / 'mfem/compare_support_test.py'), str(repo), str(run)])
    if audit.returncode not in (0, 2):
        raise RuntimeError('Inherited audit failed')
    report = json.loads((run / 'support_comparison.json').read_text())
    for stage in ('initial', 'final'):
        a = np.fromfile(run / f'mfem/{stage}_q2_subcell_averages.bin', dtype=np.float64)
        b = np.fromfile(baseline / f'mfem/{stage}_q2_subcell_averages.bin', dtype=np.float64)
        if a.shape != b.shape:
            raise ValueError('Export shapes differ')
        report[f'{stage}_density_l1_to_support'] = float(384000 / a.size * np.abs(a-b).sum())
    report['gates'].pop('support_reproduction')
    limit = 0.0025 if temporal else 0.007853258960160175
    report['gates']['temporal_density_sensitivity' if temporal else 'broader_support_sensitivity'] = report['final_density_l1_to_support'] <= limit
    if temporal:
        report['gates']['matched_initial_voxel_density'] = report['initial_density_l1_to_support'] <= 1e-10
        report['gates']['matched_horizon'] = abs(report['amr_summary']['final_time'] - .05) < 1e-12
    report['limits']['maximum_density_l1_to_support'] = limit
    report['scope'] = 'broader spatial support at fixed depth; initialization difference reported separately; no full-density certification'
    report['mature_density_convergence_certified'] = False
    passed = all(report['gates'].values())
    label = 'MATURE_TEMPORAL' if temporal else 'BROADER_SUPPORT'
    report['scope'] = 'matched-mesh half-timestep sensitivity; two levels do not establish temporal order' if temporal else report['scope']
    report['status'] = f'PASSED_{label}_GATES' if passed else f'FAILED_{label}_GATES'
    (run / ('temporal_comparison.json' if temporal else 'broader_support_comparison.json')).write_text(json.dumps(report, indent=2))
    status(report['status'])
except BaseException as error:
    status('FAILED_BROADER_SUPPORT_PIPELINE', error=str(error))
    raise
