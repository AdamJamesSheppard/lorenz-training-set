"""New window-local numerical controls; archived G03 laws are never changed."""
import argparse
import json
import os
import platform
import sys
import time
from pathlib import Path

import numpy as np
import scipy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.run_input_coverage import prepare, validate
from scripts.run_reconstruction_qualification import bounds, git, sha, verify_sources
from operator_learning.reconstruction_controls import restart_path


def window_start(initial, fine, window, count):
    if window < 0 or count <= 0 or (window+1)*count > len(fine):
        raise ValueError('Window outside saved path')
    return np.asarray(initial if window==0 else fine[window*count-1]).copy()


def execute(run):
    c=json.loads((run/'config.json').read_text())
    v=json.loads((run/'provenance.json').read_text())
    validate(c)
    verify_sources(c)
    versions=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__)
    if (v['status']!='PREPARED_NOT_EXECUTED' or versions!=c['runtime_versions']
            or sha(run/'config.json')!=v['config_sha256'] or git('rev-parse','HEAD')!=v['git_commit']):
        raise ValueError('Frozen provenance/runtime mismatch')
    if any(os.environ.get(k)!='1' for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS']):
        raise ValueError('One CPU thread required')
    source=ROOT/c['source_run']
    seal=json.loads((source/'seal.json').read_text())
    for name,digest in seal.items():
        if sha(source/name)!=digest:
            raise ValueError('Archived source seal mismatch: '+name)
    old=json.loads((source/'report.json').read_text())
    if len(old['laws'])!=36 or old['errors']:
        raise ValueError('Complete36-law source required; preserve source failures')
    rows,outputs=[],{}
    started=time.monotonic()
    write=lambda n,x:(run/n).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
    v.update(status='RUNNING',actual_command=sys.argv,observed_runtime_versions=versions,
             observed_hardware=platform.platform())
    write('provenance.json',v)
    try:
        for seed in c['seeds']['trajectory']:
            with np.load(source/f'seed{seed}_paths.npz') as a:
                fine=a['fine'].copy()
                initial=a['initial'].copy()
            for w in range(c['windows']):
                ident=f'seed{seed}_window{w}'
                row=dict(id=ident,seed=seed,window=w,status='RUNNING')
                rows.append(row)
                print(ident+' local control starting',flush=True)
                try:
                    start=window_start(initial,fine,w,c['control_count'])
                    saved=fine[w*c['control_count']:(w+1)*c['control_count']]
                    replay=restart_path(start,c['window'],c['integration_steps'][0])
                    if not np.array_equal(replay,saved):
                        raise ValueError('Fine replay differs; archived law cannot be replaced')
                    coarse=restart_path(start,c['window'],c['integration_steps'][1])
                    name=ident+'_local_control.npz'
                    np.savez_compressed(run/name,initial=start,coarse=coarse)
                    outputs[name]=sha(run/name)
                    b=bounds(saved,coarse,c['sampling_count'],c['physical_widths'])
                    prior=next(x for x in old['laws'] if x['id']==ident)
                    row.update(status='COMPLETED',fine_replay_bitwise=True,initial=start.tolist(),
                        previous_accumulated_bound=prior['bound'],local_bound=b,
                        previous_sufficient_certification=prior['reconstruction_resolved'],
                        local_sufficient_certification=b['total_tv_upper']<=c['thresholds']['reconstruction_tv_max'])
                except Exception as error:
                    row.update(status='FAILED',error=repr(error))
                write('partial_report.json',dict(rows=rows,exclusions=[],elapsed_seconds=time.monotonic()-started))
        report=dict(rows=rows,exclusions=[],expected_attempts=36,
            technical_status='COMPLETED' if len(rows)==36 and all(x['status']=='COMPLETED' for x in rows) else 'COMPLETED_WITH_FAILURES',
            gate_status='OPEN',scientific_qualification=False,elapsed_seconds=time.monotonic()-started,
            source_run=c['source_run'],limitations=c['limitations'])
        write('report.json',report)
        for n in ['report.json','partial_report.json']:
            outputs[n]=sha(run/n)
        v.update(status='COMPLETED',output_hashes=outputs,diagnostics=dict(technical_status=report['technical_status'],gate_passed=False))
        write('provenance.json',v)
        write('seal.json',{n:sha(run/n) for n in ['config.json','provenance.json',*outputs]})
    except Exception as error:
        v.update(status='FAILED',diagnostics=dict(error=repr(error)))
        write('provenance.json',v)
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('path',type=Path)
    p.add_argument('--prepare',action='store_true')
    a=p.parse_args()
    print(prepare(a.path.resolve())) if a.prepare else execute(a.path.resolve())
