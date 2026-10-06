"""Fresh-seed reconstruction characterization; never qualifies G02 automatically."""
import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import scipy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from operator_learning.alignment import density_summary, distance  # noqa: E402
from operator_learning.governance import validate_predeclaration, validate_provenance  # noqa: E402
from operator_learning.reconstruction import dense_occupation, physical_bandwidth_density  # noqa: E402


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_design(config):
    validate_predeclaration(config)
    assert config['scientific_adjudication'] == 'CHARACTERIZATION_ONLY_G02_OPEN'
    assert config['hardware']['gpu'] is False and config['hardware']['mpi'] is False
    assert config['integration_steps'] == [.001, .0005]
    assert config['sampling_counts'] == [5000, 10000, 20000]
    assert config['window'] == 10 and config['spinup'] == 20
    assert config['seeds']['trajectory'] == list(range(71029, 71035))
    assert config['comparison_shapes'] == [[60, 72, 72], [120, 144, 144]]
    assert config['histogram_shapes'] == [[45, 54, 54], [60, 72, 72], [90, 108, 108]]


def execute(run):
    config = json.loads((run / 'config.json').read_text())
    provenance = json.loads((run / 'provenance.json').read_text())
    validate_design(config)
    if provenance['status'] != 'PREPARED_NOT_EXECUTED':
        raise ValueError('New prepared run required')
    if sha(run / 'config.json') != provenance['config_sha256']:
        raise ValueError('Frozen config changed')
    commit = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    dirty = subprocess.check_output(['git', '-C', str(ROOT), 'status', '--porcelain'], text=True)
    if dirty or commit != provenance['git_commit']:
        raise ValueError('Clean committed predeclaration required')
    versions = dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__)
    if versions != config['runtime_versions']:
        raise ValueError('Runtime differs from predeclaration')
    if any(os.environ.get(key) != '1' for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS')):
        raise ValueError('One BLAS/OpenMP thread required')
    for name, digest in config['inputs'].items():
        if sha(ROOT / name) != digest:
            raise ValueError(f'Input changed: {name}')
    started = time.monotonic()
    provenance.update(status='RUNNING', actual_command=sys.argv, observed_runtime_versions=versions,
                      observed_hardware=dict(device='cpu', platform=platform.platform()))
    (run / 'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    records, outputs = [], {}
    bounds = config['bounds']
    widths = config['physical_widths']
    histograms = config['histogram_shapes']
    try:
        for seed in config['seeds']['trajectory']:
            print(f'G02 refinement seed {seed}: two RK4 paths and conservative reconstruction', flush=True)
            initial, fine = dense_occupation(seed, config['spinup'], config['window'], .0005)
            other_initial, coarse = dense_occupation(seed, config['spinup'], config['window'], .001)
            if not np.array_equal(initial, other_initial):
                raise ValueError('Initial states differ')
            path = run / f'seed{seed}_paths.npz'
            np.savez_compressed(path, initial=initial, dt0005=fine, dt001=coarse)
            outputs[path.name] = sha(path)
            for shape in config['comparison_shapes']:
                dv = float(np.prod([hi-lo for lo, hi in bounds])/np.prod(shape))

                def reconstruct(cloud, histogram):
                    density = physical_bandwidth_density(cloud, bounds, histogram, widths, shape)
                    if not np.isfinite(density).all() or density.min() < 0:
                        raise ValueError('Invalid probability density')
                    if abs(density.sum()*dv-1) > config['thresholds']['mass_error_max']:
                        raise ValueError('Mass invariant failed')
                    return density

                def record(family, a, b, metadata):
                    sa = density_summary(a, bounds, **config['regions'])
                    sb = density_summary(b, bounds, **config['regions'])
                    metrics = distance(a, b, bounds)
                    metrics.update(tv=metrics['l1']/2,
                        mean_error=float(np.linalg.norm(np.array(sa['mean'])-sb['mean'])),
                        covariance_relative_error=float(np.linalg.norm(np.array(sa['covariance'])-sb['covariance'])/
                                                        np.linalg.norm(sb['covariance'])),
                        positive_x_error=abs(sa['positive_x_probability']-sb['positive_x_probability']),
                        boundary_mass_error=abs(sa['boundary_probability']-sb['boundary_probability']))
                    records.append(dict(seed=seed, comparison_shape=shape, family=family,
                        metadata=metadata, metrics=metrics, raw_mass_a=float(a.sum()*dv),
                        raw_mass_b=float(b.sum()*dv), raw_negative_mass=0))

                reference = reconstruct(fine, histograms[0])
                for count in config['sampling_counts'][:-1]:
                    stride = len(fine)//count
                    for phase in sorted({stride//2-1, stride-1}):
                        density = reconstruct(fine[phase::stride], histograms[0])
                        record('sampling', density, reference, dict(count=count, phase=phase, stride=stride,
                            reference_count=20000, integration_dt=.0005))
                # Matching times, same initial state, including independently integrated burn-in.
                a = reconstruct(coarse[1::2], histograms[0])
                b = reconstruct(fine[3::4], histograms[0])
                record('integration', a, b, dict(count=5000, steps=[.001, .0005],
                    interpretation='Full burn-in plus window path sensitivity; chaotic amplification included'))
                densities = [reference] + [reconstruct(fine, h) for h in histograms[1:]]
                for i, j in ((0, 1), (1, 2), (0, 2)):
                    record('histogram', densities[i], densities[j], dict(histograms=[histograms[i], histograms[j]],
                        count=20000, physical_widths=widths, lifting_coupled=True))
                # Store all histogram reference fields, not fabricated archived solutions.
                path = run / (f'seed{seed}_grid'+ 'x'.join(map(str, shape)) + '.npz')
                np.savez_compressed(path, **{f'h{i}': p for i, p in enumerate(densities)})
                outputs[path.name] = sha(path)
                del densities, reference, a, b
            print(f'G02 seed {seed} completed; elapsed {time.monotonic()-started:.1f}s', flush=True)
        report = dict(experiment_id=config['id'], gate_status='OPEN', technical_status='COMPLETED',
                      records=records, elapsed_seconds=time.monotonic()-started,
                      limitations=config['limitations'], scientific_qualification=False)
        path = run / 'report.json'
        path.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
        outputs[path.name] = sha(path)
        provenance.update(status='COMPLETED', output_hashes=outputs,
                          diagnostics=dict(technical_checks_passed=True, gate_passed=False))
        validate_provenance(provenance)
        (run / 'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
        seal = {name: sha(run / name) for name in ['config.json', 'provenance.json', *outputs]}
        (run / 'seal.json').write_text(json.dumps(seal, indent=2)+'\n')
        print(f'COMPLETED_CHARACTERIZATION_G02_OPEN elapsed={report["elapsed_seconds"]:.1f}s', flush=True)
    except Exception as error:
        provenance.update(status='FAILED', diagnostics=dict(exception=repr(error)))
        (run / 'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    execute(parser.parse_args().run.resolve())
