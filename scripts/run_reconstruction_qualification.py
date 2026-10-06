"""Frozen finite-control G02 qualification, with no automatic gate promotion."""
import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from operator_learning.alignment import density_summary, distance  # noqa: E402
from operator_learning.governance import check_repository, validate_predeclaration, validate_provenance  # noqa: E402
from operator_learning.reconstruction import dense_occupation, dependence_diagnostic  # noqa: E402
from operator_learning.reconstruction_controls import empirical_box_density, paired_box_l1_bound, restart_path  # noqa: E402


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], text=True).strip()


def validate(config):
    validate_predeclaration(config)
    if (config['candidate_count'] != 20000 or config['control_count'] != 80000
            or config['thresholds']['tv_max'] != .01
            or config['physical_widths'] != [4, 40/9, 40/9]
            or config['integration_steps'] != [.000125, .00025]
            or config['sampling_counts'] != [5000, 10000, 20000]):
        raise ValueError('Frozen qualification design changed')


def verify_sources(config):
    if git('diff', 'HEAD', '--name-only'):
        raise ValueError('Tracked predeclaration/source edits present')
    untracked = git('ls-files', '--others', '--exclude-standard').splitlines()
    if set(untracked) - set(config['allowed_untracked']):
        raise ValueError('Undeclared untracked work present')
    for name, digest in config['inputs'].items():
        if sha(ROOT/name) != digest:
            raise ValueError(f'Input hash mismatch: {name}')


def prepare(source):
    config = json.loads(source.read_text())
    validate(config)
    if check_repository(ROOT):
        raise ValueError('Governance checks failed')
    relative = str(source.resolve().relative_to(ROOT))
    if subprocess.check_output(['git', '-C', str(ROOT), 'show', f'HEAD:{relative}']) != source.read_bytes():
        raise ValueError('Committed predeclaration required')
    verify_sources(config)
    status = git('status', '--porcelain')
    record = dict(experiment_id=config['id'], gate_id=config['gate_id'], kind=config['kind'],
                  config_sha256=sha(source), git_commit=git('rev-parse', 'HEAD'),
                  git_dirty=bool(status), git_status=status, command=config['command'],
                  runtime_versions=config['runtime_versions'], hardware=config['hardware'],
                  seeds=config['seeds'], input_hashes=config['inputs'], output_hashes={},
                  checkpoint_hashes={}, diagnostics={}, status='PREPARED_NOT_EXECUTED')
    validate_provenance(record)
    run = ROOT/'runs/operator-learning'/config['id']/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run.mkdir(parents=True, exist_ok=False)
    (run/'config.json').write_bytes(source.read_bytes())
    (run/'provenance.json').write_text(json.dumps(record, indent=2)+'\n')
    return run


def bounds(fine, coarse, count, widths):
    stride = len(fine)//count
    sampling = [paired_box_l1_bound(np.repeat(fine[phase::stride], stride, axis=0), fine, widths)/2
                for phase in range(stride)]
    integration = [paired_box_l1_bound(fine[phase::stride], coarse[(phase-1)//2::stride//2], widths)/2
                   for phase in range(1, stride, 2)]
    return dict(count=count, sampling_tv_upper=sampling, aligned_integration_tv_upper=integration,
                total_tv_upper=max(sampling)+max(integration)+1e-10)


def execute(run):
    config = json.loads((run/'config.json').read_text())
    provenance = json.loads((run/'provenance.json').read_text())
    validate(config)
    verify_sources(config)
    versions = dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__)
    if (provenance['status'] != 'PREPARED_NOT_EXECUTED'
            or provenance['config_sha256'] != sha(run/'config.json')
            or provenance['git_commit'] != git('rev-parse', 'HEAD')
            or versions != config['runtime_versions']):
        raise ValueError('Prepared runtime/provenance mismatch')
    if any(os.environ.get(key) != '1' for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS')):
        raise ValueError('One CPU thread required')
    started = time.monotonic()
    provenance.update(status='RUNNING', actual_command=sys.argv,
                      observed_runtime_versions=versions, platform=platform.platform())
    write = lambda name, obj: (run/name).write_text(json.dumps(obj, indent=2, allow_nan=False)+'\n')
    write('provenance.json', provenance)
    records, outputs = [], {}
    for seed in config['seeds']['trajectory']:
        row = dict(seed=seed, status='RUNNING', comparisons=[])
        records.append(row)
        try:
            print(f'seed={seed} paths starting elapsed={time.monotonic()-started:.1f}s', flush=True)
            original, spin = dense_occupation(seed, config['spinup'], .001, .001)
            # First saved state is at20.001; fixed common origin, not reintegrated.
            initial = spin[0].copy()
            fine = restart_path(initial, config['window'], config['integration_steps'][0])
            coarse = restart_path(initial, config['window'], config['integration_steps'][1])
            path = run/f'seed{seed}_paths.npz'
            np.savez_compressed(path, original=original, initial=initial, fine=fine, coarse=coarse)
            outputs[path.name] = sha(path)
            row['initial'] = initial.tolist()
            row['bounds'] = [bounds(fine, coarse, n, config['physical_widths']) for n in config['sampling_counts']]
            candidate = fine[3::4]
            row['dependence'] = [dependence_diagnostic(fine[:, d], 200, .000125) for d in range(3)]
            valid = True
            for shape in config['comparison_shapes']:
                a, ma = empirical_box_density(candidate, config['bounds'], config['physical_widths'], shape)
                b, mb = empirical_box_density(fine, config['bounds'], config['physical_widths'], shape)
                invariants = bool(np.isfinite(a).all() and np.isfinite(b).all()
                                  and min(a.min(), b.min()) >= 0
                                  and max(abs(ma-1), abs(mb-1)) <= config['thresholds']['mass_error_max'])
                valid &= invariants
                comparison = dict(shape=shape, raw_mass_candidate=ma, raw_mass_control=mb,
                                  raw_negative_mass_candidate=float(-a[a<0].sum()*
                                      np.prod(np.diff(config['bounds'], axis=1))/np.prod(shape)),
                                  technical_pass=invariants)
                if invariants:
                    comparison.update(metrics=distance(a, b, config['bounds']),
                                      candidate=density_summary(a, config['bounds'], **config['regions']),
                                      control=density_summary(b, config['bounds'], **config['regions']))
                row['comparisons'].append(comparison)
                path = run/(f'seed{seed}_grid'+'x'.join(map(str, shape))+'.npz')
                np.savez_compressed(path, candidate=a, control=b)
                outputs[path.name] = sha(path)
                del a, b
            candidate_bound = next(x for x in row['bounds'] if x['count'] == config['candidate_count'])
            row.update(status='COMPLETED', candidate_pass=bool(valid and candidate_bound['total_tv_upper'] <= .01))
        except Exception as error:
            row.update(status='FAILED', candidate_pass=False, exception=repr(error))
        write('partial_report.json', dict(records=records, gate_status='OPEN', exclusions=[]))
        print(f'seed={seed} status={row["status"]} candidate_pass={row["candidate_pass"]} elapsed={time.monotonic()-started:.1f}s', flush=True)
    report = dict(records=records, attempted=len(records), exclusions=[],
                  candidate_criteria_passed=all(x['candidate_pass'] for x in records),
                  technical_status='COMPLETED' if all(x['status']=='COMPLETED' for x in records) else 'COMPLETED_WITH_FAILURES',
                  gate_status='OPEN_PENDING_REVIEW', elapsed_seconds=time.monotonic()-started,
                  limitations=config['limitations'])
    write('report.json', report)
    outputs['report.json'] = sha(run/'report.json')
    outputs['partial_report.json'] = sha(run/'partial_report.json')
    provenance.update(status='COMPLETED', output_hashes=outputs,
                      diagnostics=dict(candidate_criteria_passed=report['candidate_criteria_passed'], gate_passed=False))
    validate_provenance(provenance)
    write('provenance.json', provenance)
    write('seal.json', {name: sha(run/name) for name in ['config.json', 'provenance.json', *outputs]})
    print(f'COMPLETE candidate_criteria_passed={report["candidate_criteria_passed"]} G02_PENDING_REVIEW', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', type=Path)
    parser.add_argument('--prepare', action='store_true')
    args = parser.parse_args()
    print(prepare(args.path)) if args.prepare else execute(args.path.resolve())
