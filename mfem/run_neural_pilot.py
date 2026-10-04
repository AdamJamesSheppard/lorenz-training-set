"""Attractor-sampled density -> FPE forecast pilot, with 2 GiB RAM resume."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from datetime import datetime, timezone

import numpy as np
from scipy.ndimage import convolve
from memory_backpressure import wait_with_backpressure


def coarsen(p):
    """Conservative averaging of aligned equal-volume 3x3x3 voxels."""
    return p.reshape(60,3,72,3,72,3).mean(axis=(1,3,5))


def drift(x):
    return np.array([10*(x[1]-x[0]),x[0]*(28-x[2])-x[1],x[0]*x[1]-(8/3)*x[2]])


def rk4(x, dt):
    a=drift(x); b=drift(x+.5*dt*a); c=drift(x+.5*dt*b); d=drift(x+dt*c)
    return x+dt*(a+2*b+2*c+d)/6


def attractor_samples(seed, spinup=20., window=10., dt=.001, stride=10):
    """Deterministic Lorenz-63 trajectory; transient removed, no stationarity proof."""
    rng=np.random.default_rng(seed)
    x=rng.uniform([-10,-10,10],[10,10,30])
    initial=x.copy()
    for _ in range(round(spinup/dt)):
        x=rk4(x,dt)
    cloud=[]
    for i in range(round(window/dt)):
        x=rk4(x,dt)
        if (i+1)%stride==0:
            cloud.append(x.copy())
    return initial,np.array(cloud)


def vertex_density(cloud):
    """Histogram -> compact smoothing -> continuous nonnegative Q1 density."""
    histogram,_=np.histogramdd(cloud,bins=(45,54,54),range=((-30,30),(-40,40),(-10,70)))
    if histogram.sum()!=len(cloud):
        raise ValueError('Attractor samples outside the tested box')
    # Direct nonnegative sums avoid cancellation in the running-sum filter.
    smooth=convolve(histogram,np.ones((3,3,3),dtype=np.float64)/27,mode='constant')
    padded=np.pad(smooth,1,mode='edge')
    vertices=sum(padded[i:i+46,j:j+55,k:k+55] for i in (0,1) for j in (0,1) for k in (0,1))/8
    # Exact integral of piecewise trilinear field, by tensor trapezoidal weights.
    weights=[np.ones(n) for n in vertices.shape]
    for w in weights:
        w[[0,-1]]=.5
    mass=np.einsum('ijk,i,j,k',vertices,*weights)*384000/(45*54*54)
    if mass<=0:
        raise ValueError('Empty empirical prior')
    density=vertices/mass
    if not np.isfinite(density).all() or density.min()<0:
        raise ValueError('Empirical density must be finite and nonnegative before dispatch')
    return density


def main():
    repo=Path(__file__).resolve().parents[1]
    root=repo/'runs/neural-pilot'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    root.mkdir(parents=True)
    print(root,flush=True)
    def status(label,**fields):
        temporary=root/'status.tmp'
        temporary.write_text(json.dumps(dict(status=label,**fields),indent=2))
        temporary.replace(root/'status.json')
    try:
        baseline=repo/'runs/mfem-broader-support/20261002T080644Z/design'
        # Positional placeholder for backward-compatible CLI; ignored when
        # LORENZ_EMPIRICAL_PRIOR selects the non-Gaussian initial coefficient.
        placeholder=repo/'runs/mfem-static-amr-reproduction/20260916T221235Z/design/mixture_parameters.bin'
        binary=repo/'build/mfem-physical-equivalence/mfem_pilot_lowmem'
        envroot=Path('/home/adam/.local/share/mamba/envs/mfem-lorenz')
        inputs=[binary,repo/'scripts/build-pilot-solver',repo/'mfem/mfem_physical_equivalence.cpp',repo/'mfem/empirical_prior.hpp',baseline/'base_cell_marks.bin',baseline/'child_cell_marks.bin',Path(__file__),repo/'scripts/train_neural_pilot.py',repo/'mfem/memory_backpressure.py']
        (root/'input_sha256.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},indent=2))
        for args,name in [(['rev-parse','HEAD'],'git_commit.txt'),(['status','--short'],'git_status.txt')]:
            (root/name).write_bytes(subprocess.check_output(['git','-C',str(repo),*args]))
        shutil.copyfile(repo/'experiments/neural-pilot.json',root/'config.json')
        config=json.loads((root/'config.json').read_text())
        env=dict(os.environ,PATH=str(envroot/'bin')+':'+os.environ['PATH'],OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
        (root/'environment.txt').write_bytes(subprocess.check_output([str(envroot/'bin/mpiexec'),'--version']))
        manifest=[]
        for index in range(6):
            run=root/f'law{index}'
            (run/'mfem').mkdir(parents=True)
            status('SAMPLING_LORENZ_ATTRACTOR',law=index)
            initial,cloud=attractor_samples(config['seed']+index)
            np.save(run/'attractor_samples.npy',cloud)
            vertices=vertex_density(cloud)
            vertices.tofile(run/'empirical_prior.bin')
            (run/'prior_design.json').write_text(json.dumps(dict(seed=config['seed']+index,trajectory_initial=initial.tolist(),spinup=20.,sampling_window=10.,rk4_dt=.001,sampling_interval=.01,count=len(cloud),histogram_shape=[45,54,54],compact_filter_width=3,interpolation='positive trilinear',gaussian_fit=False,stationarity_proved=False,sha256=hashlib.sha256((run/'empirical_prior.bin').read_bytes()).hexdigest()),indent=2))
            command=[str(envroot/'bin/mpiexec'),'-n','8',str(binary),'amr2','45','54','54',str(baseline/'base_cell_marks.bin'),str(baseline/'child_cell_marks.bin'),str(placeholder),str(run/'mfem'),'320']
            (run/'command.json').write_text(json.dumps(command,indent=2))
            prior_env=dict(env,LORENZ_EMPIRICAL_PRIOR=str(run/'empirical_prior.bin'))
            (run/'prior_environment.json').write_text(json.dumps(dict(LORENZ_EMPIRICAL_PRIOR=str(run/'empirical_prior.bin'))))
            with (run/'solver.log').open('w') as log:
                process=subprocess.Popen(command,env=prior_env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                wait_with_backpressure(process,lambda m:status('PAUSED_LOW_MEMORY' if m['paused'] else 'GENERATING_FORECASTS',law=index,total=6,**m),pause_kib=2*1024*1024,resume_kib=2*1024*1024)
            if process.returncode:
                raise RuntimeError(f'Law {index}: solver exit {process.returncode}')
            summary=json.loads((run/'mfem/mature_summary.json').read_text())
            gates=dict(positive=summary['whole_cell_positivity_certified'] and summary['initial_uncertified_cells']==0 and summary['maximum_uncertified_cells']==0,mass=abs(summary['initial_mass']-1)+summary['maximum_absolute_mass_error']<1e-10,optimizer=summary['optimizer_failures']==0 and summary['fallbacks']==0,correction=summary['mean_relative_l1_correction']<8e-4)
            fields=[]; errors=[]
            for name in ('initial','final'):
                p=np.fromfile(run/f'mfem/{name}_q2_subcell_averages.bin',dtype=np.float64).reshape(180,216,216)
                gates[name+'_export']=bool(np.isfinite(p).all() and -p[p<0].sum()*384000/p.size<1e-13 and abs(p.sum()*384000/p.size-1)<1e-10)
                gates[name+'_boundary']=float((p.sum()-p[4:-4,4:-4,4:-4].sum())*384000/p.size)<1e-6
                averaged=coarsen(p); compact=averaged.astype(np.float32)
                errors.append(float(np.abs(averaged-compact).sum()*384000/averaged.size)); fields.append(compact)
            (run/'acceptance.json').write_text(json.dumps(dict(gates=gates,float32_l1_errors=errors),indent=2))
            if not all(gates.values()):
                raise ValueError(f'Law {index}: numerical gates failed; training withheld')
            np.savez(run/'pair.npz',initial=fields[0],final=fields[1])
            manifest.append(dict(law=index,path=f'law{index}/pair.npz',split=config['splits'][index],sha256=hashlib.sha256((run/'pair.npz').read_bytes()).hexdigest()))
            (root/'manifest.json').write_text(json.dumps(manifest,indent=2))
        training_python=repo/'.venv/neural-pilot/bin/python'
        if not training_python.exists():
            raise RuntimeError('Training environment missing')
        with (root/'training.log').open('w') as log:
            with (root/'training_packages.txt').open('w') as packages:
                subprocess.run([str(training_python),'-m','pip','freeze'],stdout=packages,check=True)
            status('TRAINING_DENSITY_FORECAST_OPERATOR')
            process=subprocess.Popen([str(training_python),str(repo/'scripts/train_neural_pilot.py'),str(root)],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            wait_with_backpressure(process,lambda m:status('PAUSED_TRAINING' if m['paused'] else 'TRAINING',**m),pause_kib=2*1024*1024,resume_kib=2*1024*1024)
            if process.returncode:
                raise RuntimeError('Training failed; inspect training.log')
        status('COMPLETED_EXPLORATORY_PILOT',production_authorized=False)
    except BaseException as error:
        status('FAILED',error=str(error))
        raise


if __name__=='__main__':
    main()
