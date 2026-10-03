#!/usr/bin/env python3
"""Two aligned expanding boxes, preserving all original interior cells."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
import numpy as np
from memory_backpressure import wait_with_backpressure
import argparse

parser=argparse.ArgumentParser()
parser.add_argument('--completed-first-domain',type=Path)
options=parser.parse_args()

repo = Path(__file__).resolve().parents[1]
root = repo / 'runs/mfem-domain-sensitivity' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
root.mkdir(parents=True, exist_ok=False)
print(root, flush=True)
baseline = repo / 'runs/mfem-broader-support/20261002T080644Z'
first = repo / 'runs/mfem-static-amr-reproduction/20260916T221235Z'
envroot = Path('/home/adam/.local/share/mamba/envs/mfem-lorenz')
environment = dict(os.environ, PATH=str(envroot/'bin')+':'+os.environ['PATH'], OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
shape0 = (180,216,216)
volume = 384000/np.prod(shape0)

def status(value, **extra):
    (root/'status.json').write_text(json.dumps(dict(status=value, **extra), indent=2))

def stats(p, pad):
    centers = [lo-pad*h+(np.arange(n)+.5)*h/4 for lo,h,n in zip((-30,-40,-10),(60/45,80/54,80/54),p.shape)]
    mass = float(p.sum()*volume)
    marginals = [p.sum(axis=tuple(j for j in range(3) if j != i))*volume for i in range(3)]
    means = np.array([np.dot(c,m)/mass for c,m in zip(centers,marginals)])
    cov = np.zeros((3,3))
    for i in range(3):
        cov[i,i] = np.dot((centers[i]-means[i])**2,marginals[i])/mass
        for j in range(i):
            k = 3-i-j
            joint = p.sum(axis=k)*volume
            cov[j,i] = cov[i,j] = float((joint*(centers[j]-means[j])[:,None]*(centers[i]-means[i])[None,:]).sum()/mass)
    interior = tuple(slice(4*pad,-4*pad) for _ in range(3)) if pad else (slice(None),)*3
    boundary_mask = np.ones(p.shape,dtype=bool)
    boundary_mask[4:-4,4:-4,4:-4] = False
    return mass,means,cov,marginals,interior,float(p[boundary_mask].sum()*volume)

try:
    shutil.copyfile(repo/'experiments/mfem-domain-sensitivity.yaml',root/'config.yaml')
    (root/'environment.txt').write_bytes(subprocess.check_output([str(envroot/'bin/mpiexec'),'--version']))
    for args,name in [(['rev-parse','HEAD'],'git_commit.txt'),(['status','--short'],'git_status.txt')]:
        (root/name).write_bytes(subprocess.check_output(['git','-C',str(repo),*args]))
    reports=[]
    previous = baseline
    previous_pad=0
    levels=(1,2)
    if options.completed_first_domain:
        previous=options.completed_first_domain.resolve()
        report=json.loads((previous/'domain_comparison.json').read_text())
        if report['padding'] != 1 or not all(report['gates'].values()):
            raise ValueError('First-domain reference must have passed every gate')
        if not (previous/'mfem/final_q2_subcell_averages.bin').is_file():
            raise ValueError('Missing completed first-domain density')
        reports.append(report)
        previous_pad=1
        levels=(2,)
        (root/'completed_first_domain_reference.json').write_text(json.dumps(dict(path=str(previous),
            sha256=hashlib.sha256((previous/'domain_comparison.json').read_bytes()).hexdigest()),indent=2))
    for pad in levels:
        run=root/f'padding{pad}'
        (run/'design').mkdir(parents=True)
        (run/'mfem').mkdir()
        for name,shape,factor in [('base_cell_marks.bin',(45,54,54),1),('child_cell_marks.bin',(90,108,108),2)]:
            marks=np.fromfile(baseline/'design'/name,dtype=np.uint8).reshape(shape)
            np.pad(marks,pad*factor).tofile(run/'design'/name)
        binary=repo/f'build/mfem-physical-equivalence/mfem_domain_padding{pad}_lowmem'
        command=[str(envroot/'bin/mpiexec'),'-n','8',str(binary),'amr2',str(45+2*pad),str(54+2*pad),str(54+2*pad),str(run/'design/base_cell_marks.bin'),str(run/'design/child_cell_marks.bin'),str(first/'design/mixture_parameters.bin'),str(run/'mfem')]
        inputs=[binary,repo/'mfem/mfem_physical_equivalence.cpp',Path(__file__),first/'design/mixture_parameters.bin',baseline/'design/base_cell_marks.bin',baseline/'design/child_cell_marks.bin',run/'design/base_cell_marks.bin',run/'design/child_cell_marks.bin',previous/'mfem/final_q2_subcell_averages.bin',previous/'mfem/initial_q2_subcell_averages.bin']
        (run/'input_sha256.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},indent=2))
        (run/'command.json').write_text(json.dumps(command,indent=2))
        status('RUNNING_DOMAIN_SENSITIVITY', padding=pad,steps=320)
        process=subprocess.Popen(command,env=environment,start_new_session=True)
        def memory_update(measurement):
            (run/'memory_guard.json').write_text(json.dumps(measurement,indent=2))
            status('PAUSED_LOW_MEMORY' if measurement['paused'] else 'RUNNING_DOMAIN_SENSITIVITY',
                   padding=pad,steps=320,**measurement)
        wait_with_backpressure(process,memory_update)
        if process.returncode:
            raise RuntimeError(f'Solver exit {process.returncode}')
        p=np.fromfile(run/'mfem/final_q2_subcell_averages.bin',dtype=np.float64).reshape(tuple(n+8*pad for n in shape0))
        q=np.fromfile(previous/'mfem/final_q2_subcell_averages.bin',dtype=np.float64).reshape(tuple(n+8*previous_pad for n in shape0))
        mass,mean,cov,marginals,interior,boundary=stats(p,pad)
        oldmass,oldmean,oldcov,oldmarginals,_,_=stats(q,previous_pad)
        cropped=p[4:-4,4:-4,4:-4]
        density=float(volume*np.abs(cropped-q).sum())
        tv=[float(.5*np.abs(a[4:-4]-b).sum()) for a,b in zip(marginals,oldmarginals)]
        covariance=float(np.linalg.norm(cov-oldcov)/np.linalg.norm(oldcov))
        va,ea=np.linalg.eigh(cov); vb,eb=np.linalg.eigh(oldcov)
        angles=np.degrees(np.arccos(np.clip(np.abs(np.sum(ea*eb,axis=0)),0,1)))
        summary=json.loads((run/'mfem/mature_summary.json').read_text())
        initial=np.fromfile(run/'mfem/initial_q2_subcell_averages.bin',dtype=np.float64).reshape(p.shape)
        initialold=np.fromfile(previous/'mfem/initial_q2_subcell_averages.bin',dtype=np.float64).reshape(q.shape)
        initialdiff=float(volume*np.abs(initial[4:-4,4:-4,4:-4]-initialold).sum())
        gates=dict(interior_density=density<=.0025,covariance=covariance<=.005,marginals=max(tv)<=.005,means=float(np.max(np.abs(mean-oldmean)))<=.005,principal_directions=float(max(angles))<=1.,boundary_probability=boundary<=1e-6,initial_match=initialdiff<=1e-6,mass=summary['maximum_absolute_mass_error']<=1e-10,negative_mass=float(-p[p<0].sum()*volume)<=1e-13,positivity=summary['whole_cell_positivity_certified'] and summary['maximum_uncertified_cells']==0,optimizer=summary['optimizer_failures']==0 and summary['fallbacks']==0,correction=summary['mean_relative_l1_correction']<=.0008,export_mass=abs(mass-summary['final_mass'])<=1e-10)
        report=dict(padding=pad,interior_density_l1=density,initial_interior_l1=initialdiff,relative_covariance_change=covariance,marginal_tv_changes=tv,mean_changes=(mean-oldmean).tolist(),principal_direction_angles_degrees=angles.tolist(),outer_boundary_layer_mass=boundary,probability_outside_previous_box=float(mass-cropped.sum()*volume),summary=summary,gates=gates,production_dataset_authorized=False)
        (run/'domain_comparison.json').write_text(json.dumps(report,indent=2))
        reports.append(report)
        if not all(gates.values()):
            status('FAILED_DOMAIN_GATES',padding=pad)
            sys.exit(2)
        previous=run
        previous_pad=pad
    (root/'domain_decision.json').write_text(json.dumps(dict(status='PASSED_TWO_DOMAIN_EXPANSIONS',comparisons=reports,scope='tested mature law and t=0.05 only',production_dataset_authorized=False),indent=2))
    status('PASSED_TWO_DOMAIN_EXPANSIONS')
except BaseException as error:
    if not isinstance(error,SystemExit):
        status('FAILED_DOMAIN_PIPELINE',error=str(error))
    raise
