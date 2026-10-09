"""Frozen fresh G03 law-diversity evidence; review never promotes automatically."""
import argparse
from datetime import datetime, timezone
from itertools import combinations
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

import numpy as np
import scipy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from operator_learning.alignment import density_summary, distance
from operator_learning.diversity_qualification import evaluate
from operator_learning.governance import check_repository, validate_predeclaration, validate_provenance
from operator_learning.reconstruction import dense_occupation
from operator_learning.reconstruction_controls import empirical_box_density, restart_path
from scripts.run_reconstruction_qualification import bounds, git, sha, verify_sources


def validate(c):
    validate_predeclaration(c)
    if (c['gate_id'] != 'OL-G03_INPUT_DIVERSITY'
            or c['seeds']['trajectory'] != list(range(83501, 83513))
            or c['windows'] != 2 or c['spinup'] != 20 or c['window'] != 10
            or c['integration_steps'] != [.000125, .00025]
            or c['physical_widths'] != [4, 40/9, 40/9]
            or c['sampling_count'] != 20000 or c['shape'] != [60, 72, 72]
            or c['thresholds'] != dict(reconstruction_tv_max=.01, mass_error_max=1e-10)
            or c['acceptance_rule'] != 'EVERY_LAW_HAS_CROSS_SOURCE_RESOLVED_WITNESS'):
        raise ValueError('Frozen prospective design differs')


def prepare(source):
    c = json.loads(source.read_text())
    validate(c)
    if check_repository(ROOT):
        raise ValueError('Governance checks failed')
    state = json.loads((ROOT/'docs/operator_learning/state.json').read_text())
    if state['gates'][c['gate_id']] != 'OPEN':
        raise ValueError('Current OPEN G03 required')
    relative = str(source.relative_to(ROOT))
    if subprocess.check_output(['git', '-C', str(ROOT), 'show', f'HEAD:{relative}']) != source.read_bytes():
        raise ValueError('Committed predeclaration required')
    verify_sources(c)
    v = dict(experiment_id=c['id'], gate_id=c['gate_id'], kind=c['kind'],
             config_sha256=sha(source), git_commit=git('rev-parse', 'HEAD'),
             git_dirty=bool(git('status', '--porcelain')), git_status=git('status', '--porcelain'),
             command=c['command'], runtime_versions=c['runtime_versions'], hardware=c['hardware'],
             seeds=c['seeds'], input_hashes=c['inputs'], output_hashes={}, checkpoint_hashes={},
             diagnostics={}, status='PREPARED_NOT_EXECUTED')
    validate_provenance(v)
    run = ROOT/'runs/operator-learning'/c['id']/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run.mkdir(parents=True, exist_ok=False)
    (run/'config.json').write_bytes(source.read_bytes())
    (run/'provenance.json').write_text(json.dumps(v, indent=2)+'\n')
    return run


def execute(run):
    c = json.loads((run/'config.json').read_text())
    v = json.loads((run/'provenance.json').read_text())
    validate(c)
    verify_sources(c)
    versions = dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__)
    if (v['status'] != 'PREPARED_NOT_EXECUTED' or versions != c['runtime_versions']
            or sha(run/'config.json') != v['config_sha256'] or git('rev-parse', 'HEAD') != v['git_commit']
            or any(os.environ.get(k) != '1' for k in ['OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS'])):
        raise ValueError('Frozen runtime/provenance mismatch')
    started = time.monotonic()
    rows, pairs, within, outputs = [], [], [], {}
    expected = [f'seed{s}_window{w}' for s in c['seeds']['trajectory'] for w in range(c['windows'])]
    def write(name, obj):
        (run/name).write_text(json.dumps(obj, indent=2, allow_nan=False)+'\n')
    def save(name, **arrays):
        np.savez_compressed(run/name, **arrays)
        outputs[name] = sha(run/name)
    v.update(status='RUNNING', actual_command=sys.argv, observed_runtime_versions=versions,
             observed_hardware=platform.platform())
    write('provenance.json', v)
    try:
        for seed in c['seeds']['trajectory']:
            try:
                _, spin = dense_occupation(seed, c['spinup'], .001, .001)
                initial = spin[0]  # Historical origin at spinup + .001, declared explicitly.
                full = restart_path(initial, c['windows']*c['window'], c['integration_steps'][0])
                save(f'seed{seed}_fine.npz', initial=initial, fine=full)
            except Exception as error:
                for w in range(c['windows']):
                    rows.append(dict(id=f'seed{seed}_window{w}', source=str(seed),
                                     status='FAILED', error=repr(error)))
                continue
            count = int(round(c['window']/c['integration_steps'][0]))
            for w in range(c['windows']):
                ident = f'seed{seed}_window{w}'
                row = dict(id=ident, source=str(seed), window=w, status='RUNNING')
                rows.append(row)
                try:
                    start = initial if w == 0 else full[w*count-1]
                    fine = full[w*count:(w+1)*count]
                    coarse = restart_path(start, c['window'], c['integration_steps'][1])
                    b = bounds(fine, coarse, c['sampling_count'], c['physical_widths'])
                    save(ident+'_control.npz', initial=start, coarse=coarse)
                    arrays, raw = {}, []
                    for phase in range(4):
                        field, mass = empirical_box_density(fine[phase::4], c['bounds'],
                                                            c['physical_widths'], c['shape'])
                        if not np.isfinite(field).all():
                            raise ValueError('Nonfinite raw density')
                        volume = np.prod([(hi-lo)/n for (lo,hi),n in zip(c['bounds'],c['shape'])])
                        neg = float(-np.minimum(field, 0).sum()*volume)
                        raw.append(dict(phase=phase, mass=mass, negative_mass=neg))
                        arrays[f'phase{phase}'] = field
                    save(ident+'_densities.npz', **arrays)
                    for a,bp in combinations(range(4),2):
                        metrics = distance(arrays[f'phase{a}'], arrays[f'phase{bp}'], c['bounds'])
                        within.append(dict(law=ident, phases=[a,bp], tv=metrics['l1']/2))
                    row.update(status='COMPLETED', reconstruction_tv_bound=b['total_tv_upper'],
                               bound=b, raw_mass=raw[3]['mass'], negative_mass=max(x['negative_mass'] for x in raw),
                               raw=raw, path=ident+'_densities.npz',
                               summary=density_summary(arrays['phase3'],c['bounds'],**c['regions']))
                    if any(abs(x['mass']-1)>c['thresholds']['mass_error_max'] for x in raw):
                        row.update(status='FAILED', error='Raw phase mass gate failed; no repair')
                except Exception as error:
                    row.update(status='FAILED', error=repr(error))
                write('partial_report.json',dict(laws=rows,within=within,exclusions=[],elapsed_seconds=time.monotonic()-started))
                print(f'{ident} {row["status"]} elapsed={time.monotonic()-started:.1f}s',flush=True)
        for a,b in combinations(rows,2):
            if a['status'] != 'COMPLETED' or b['status'] != 'COMPLETED':
                continue  # Both attempts remain in report; missing pairs explicitly block eligibility.
            with np.load(run/a['path']) as aa, np.load(run/b['path']) as bb:
                metrics = distance(aa['phase3'],bb['phase3'],c['bounds'])
            pairs.append(dict(a=a['id'], b=b['id'], tv=metrics['l1']/2, metrics=metrics,
                              family='WITHIN_SOURCE' if a['source']==b['source'] else 'CROSS_SOURCE'))
        decision = evaluate(rows,pairs,expected,**c['thresholds'])
        report = dict(laws=rows,pairs=pairs,within=within,exclusions=[],evaluation=decision,
                      gate_status='OPEN',scientific_qualification=False,elapsed_seconds=time.monotonic()-started,
                      limitations=c['limitations'],expected_pairs=276,expected_within=144,
                      technical_status='COMPLETED' if len(rows)==24 and all(r['status']=='COMPLETED' for r in rows) else 'COMPLETED_WITH_FAILURES')
        write('report.json',report)
        for name in ['report.json','partial_report.json']:
            if (run/name).exists():
                outputs[name]=sha(run/name)
        v.update(status='COMPLETED',output_hashes=outputs,diagnostics=dict(review_status=decision['review_status'],gate_passed=False))
        validate_provenance(v)
        write('provenance.json',v)
        write('seal.json',{n:sha(run/n) for n in ['config.json','provenance.json',*outputs]})
    except Exception as error:
        v.update(status='FAILED',diagnostics=dict(error=repr(error)))
        write('provenance.json',v)
        raise


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path',type=Path)
    parser.add_argument('--prepare',action='store_true')
    args=parser.parse_args()
    print(prepare(args.path.resolve())) if args.prepare else execute(args.path.resolve())
