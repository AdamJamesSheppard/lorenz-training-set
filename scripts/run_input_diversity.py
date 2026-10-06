"""Bounded G03 characterization; no automatic scientific qualification."""
import argparse
import json
import os
import platform
import sys
import time
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

import numpy as np
import scipy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from operator_learning.alignment import density_summary, distance  # noqa: E402
from operator_learning.governance import check_repository, validate_predeclaration, validate_provenance  # noqa: E402
from operator_learning.reconstruction_controls import empirical_box_density  # noqa: E402
from scripts.run_reconstruction_qualification import git, sha, verify_sources  # noqa: E402


def resolution_margin(grid_tv, error_a, error_b, mass_a, mass_b):
    values = np.array([grid_tv, error_a, error_b, mass_a, mass_b], dtype=float)
    if not np.isfinite(values).all() or min(grid_tv, error_a, error_b) < 0 or min(mass_a, mass_b) <= 0:
        raise ValueError('Finite valid TV/errors and positive raw masses required')
    signed = float(grid_tv-error_a-error_b-abs(mass_a-1)-abs(mass_b-1)-1e-10)
    return dict(signed_margin=signed, finite_control_tv_lower=max(0., signed),
                resolved=signed > 0)


def validate(config):
    validate_predeclaration(config)
    if (config['gate_id'] != 'OL-G03_INPUT_DIVERSITY'
            or config['scientific_adjudication'] != 'CHARACTERIZATION_ONLY_G03_OPEN'
            or config['phases'] != [0, 1, 2, 3]
            or config['sampling_count'] != 20000):
        raise ValueError('Frozen G03 characterization required')


def prepare(source):
    config = json.loads(source.read_text())
    validate(config)
    if check_repository(ROOT):
        raise ValueError('Governance inconsistency')
    state = json.loads((ROOT/'docs/operator_learning/state.json').read_text())
    if state['gates'][config['gate_id']] != 'OPEN':
        raise ValueError('Only current OPEN gate may be prepared')
    relative = str(source.resolve().relative_to(ROOT))
    # git show must succeed: a working-tree-only draft cannot dispatch.
    import subprocess
    if subprocess.check_output(['git', '-C', str(ROOT), 'show', f'HEAD:{relative}']) != source.read_bytes():
        raise ValueError('Committed config required')
    verify_sources(config)
    status = git('status', '--porcelain')
    provenance = dict(experiment_id=config['id'], gate_id=config['gate_id'], kind=config['kind'],
        config_sha256=sha(source), git_commit=git('rev-parse', 'HEAD'), git_dirty=bool(status),
        git_status=status, command=config['command'], runtime_versions=config['runtime_versions'],
        hardware=config['hardware'], seeds=config['seeds'], input_hashes=config['inputs'],
        output_hashes={}, checkpoint_hashes={}, diagnostics={}, status='PREPARED_NOT_EXECUTED')
    validate_provenance(provenance)
    run = ROOT/'runs/operator-learning'/config['id']/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run.mkdir(parents=True, exist_ok=False)
    (run/'config.json').write_bytes(source.read_bytes())
    (run/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    return run


def execute(run):
    config = json.loads((run/'config.json').read_text())
    provenance = json.loads((run/'provenance.json').read_text())
    validate(config)
    verify_sources(config)
    versions = dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__)
    if (provenance['status'] != 'PREPARED_NOT_EXECUTED'
            or sha(run/'config.json') != provenance['config_sha256']
            or git('rev-parse', 'HEAD') != provenance['git_commit']
            or versions != config['runtime_versions']):
        raise ValueError('Frozen runtime/provenance differs')
    if any(os.environ.get(k) != '1' for k in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS')):
        raise ValueError('One CPU thread required')
    started = time.monotonic()
    write = lambda name, value: (run/name).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    provenance.update(status='RUNNING', actual_command=sys.argv, observed_runtime_versions=versions,
                      observed_hardware=platform.platform())
    write('provenance.json', provenance)
    source = ROOT/config['source_run']
    ledger = json.loads((source/'report.json').read_text())
    seal = json.loads((source/'seal.json').read_text())
    within, between, summaries, errors, outputs = [], [], [], [], {}
    try:
        for name, digest in seal.items():
            if sha(source/name) != digest:
                raise ValueError(f'Source seal mismatch: {name}')
        error_bounds = {row['seed']: next(b['total_tv_upper'] for b in row['bounds']
                         if b['count']==20000) for row in ledger['records']}
        attempts = []
        for shape in config['comparison_shapes']:
            endpoints = {}
            for seed in config['seeds']['trajectory']:
                attempt = dict(seed=seed, shape=shape, status='RUNNING')
                attempts.append(attempt)
                try:
                    with np.load(source/f'seed{seed}_paths.npz', allow_pickle=False) as saved:
                        cloud = saved['fine'].copy()
                    phases, masses = [], []
                    for phase in config['phases']:
                        a, mass = empirical_box_density(cloud[phase::4], config['bounds'], config['physical_widths'], shape)
                        if (not np.isfinite(a).all() or a.min() < 0
                                or abs(mass-1) > config['thresholds']['mass_error_max']):
                            raise ValueError('Raw mass/positivity invariant failed; no repair')
                        phases.append(a)
                        masses.append(mass)
                        summaries.append(dict(seed=seed, phase=phase, shape=shape, raw_mass=mass,
                            negative_mass=0., statistics=density_summary(a, config['bounds'], **config['regions'])))
                    name = f'seed{seed}_grid'+ 'x'.join(map(str, shape)) + '.npz'
                    with np.load(source/name, allow_pickle=False) as original:
                        if not np.array_equal(phases[3], original['candidate']):
                            raise ValueError('Archived endpoint representation differs')
                    for a, b in combinations(range(4), 2):
                        metrics = distance(phases[a], phases[b], config['bounds'])
                        within.append(dict(seed=seed, shape=shape, phases=[a,b],
                                           tv=metrics['l1']/2, metrics=metrics))
                    endpoints[seed] = (phases[3], masses[3])
                    path = run/name
                    np.savez_compressed(path, **{f'phase{i}': a for i,a in enumerate(phases)})
                    outputs[name] = sha(path)
                    attempt['status'] = 'COMPLETED'
                    del phases, cloud
                except Exception as error:
                    attempt.update(status='FAILED', error=repr(error))
                    errors.append(attempt.copy())
                write('partial_report.json', dict(attempts=attempts, within=within, errors=errors, exclusions=[]))
                print(f'G03 seed={seed} grid={shape} {attempt["status"]} elapsed={time.monotonic()-started:.1f}s', flush=True)
            for a,b in combinations(config['seeds']['trajectory'], 2):
                if a not in endpoints or b not in endpoints:
                    between.append(dict(seeds=[a,b], shape=shape, status='MISSING_DUE_TO_RECORDED_FAILURE'))
                    continue
                pa,ma = endpoints[a]
                pb,mb = endpoints[b]
                metrics = distance(pa,pb,config['bounds'])
                tv = metrics['l1']/2
                between.append(dict(seeds=[a,b], shape=shape, status='COMPLETED', tv=tv,
                    metrics=metrics, error_bounds=[error_bounds[a],error_bounds[b]],
                    **resolution_margin(tv,error_bounds[a],error_bounds[b],ma,mb)))
                sa = next(s['statistics'] for s in summaries if s['seed']==a and s['shape']==shape and s['phase']==3)
                sb = next(s['statistics'] for s in summaries if s['seed']==b and s['shape']==shape and s['phase']==3)
                between[-1]['statistics'] = dict(
                    mean_vector_error=float(np.linalg.norm(np.array(sa['mean'])-sb['mean'])),
                    covariance_frobenius_error=float(np.linalg.norm(np.array(sa['covariance'])-sb['covariance'])),
                    lobe_error=abs(sa['positive_x_probability']-sb['positive_x_probability']),
                    tail_error=abs(sa['tail_probability']-sb['tail_probability']),
                    boundary_error=abs(sa['boundary_probability']-sb['boundary_probability']))
            del endpoints
        aggregate, nearest = [], []
        for shape in config['comparison_shapes']:
            for family, rows in [('within',within),('between',between)]:
                values = [r['tv'] for r in rows if r['shape']==shape and 'tv' in r]
                aggregate.append(dict(family=family,shape=shape,count=len(values),
                    median=float(np.median(values)) if values else None,
                    p90=float(np.quantile(values,.9)) if values else None,
                    p95=float(np.quantile(values,.95)) if values else None,
                    worst=float(max(values)) if values else None))
            for seed in config['seeds']['trajectory']:
                rows = [r for r in between if r['shape']==shape and seed in r['seeds'] and 'tv' in r]
                closest = min(rows,key=lambda r:r['tv']) if rows else None
                nearest.append(dict(seed=seed,shape=shape,pair=closest))
        report = dict(attempts=attempts, within=within, between=between, summaries=summaries,
            aggregate=aggregate, nearest_neighbors=nearest,
            prior_count_bounds={row['seed']:row['bounds'] for row in ledger['records']},
            errors=errors, exclusions=[], expected_within=72, expected_between=30,
            technical_status='COMPLETED' if not errors and len(within)==72 and len(between)==30 else 'COMPLETED_WITH_FAILURES',
            gate_status='OPEN', scientific_qualification=False,
            elapsed_seconds=time.monotonic()-started, limitations=config['limitations'])
        write('report.json', report)
        outputs['report.json'] = sha(run/'report.json')
        outputs['partial_report.json'] = sha(run/'partial_report.json')
        provenance.update(status='COMPLETED', output_hashes=outputs,
                          diagnostics=dict(technical_status=report['technical_status'],gate_passed=False))
        validate_provenance(provenance)
        write('provenance.json',provenance)
        write('seal.json',{name:sha(run/name) for name in ['config.json','provenance.json',*outputs]})
        print('G03_CHARACTERIZATION_COMPLETED_GATE_OPEN',flush=True)
    except Exception as error:
        write('partial_report.json',dict(within=within,between=between,errors=errors,exception=repr(error),exclusions=[]))
        provenance.update(status='FAILED',diagnostics=dict(exception=repr(error)))
        write('provenance.json',provenance)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path',type=Path)
    parser.add_argument('--prepare',action='store_true')
    args = parser.parse_args()
    print(prepare(args.path)) if args.prepare else execute(args.path.resolve())
