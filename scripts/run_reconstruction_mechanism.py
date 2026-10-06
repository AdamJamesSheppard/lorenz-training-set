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
from operator_learning.reconstruction import physical_bandwidth_density  # noqa: E402
from operator_learning.reconstruction_controls import restart_path, exact_box_histogram_density  # noqa: E402


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_design(config):
    validate_predeclaration(config)
    if config['scientific_adjudication'] != 'CHARACTERIZATION_ONLY_G02_OPEN':
        raise ValueError('Characterization cannot qualify G02')
    if config['integration_steps'] != [.001, .0005] or config['window'] != 10:
        raise ValueError('Frozen common-start design changed')
    if config['hardware']['gpu'] or config['hardware']['mpi']:
        raise ValueError('CPU-only design required')



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
    records, outputs, attempted = [], {}, []
    bounds = config['bounds']
    widths = config['physical_widths']
    histograms = config['histogram_shapes']
    try:
        for seed in config['seeds']['trajectory']:
            attempted.append(seed)
            print(f'G02 refinement seed {seed}: two RK4 paths and conservative reconstruction', flush=True)
            saved = np.load(ROOT/config['source_run']/f'seed{seed}_paths.npz')
            # Exact stored first post-burn-in fine-path state, no reintegrated burn-in.
            initial = saved['dt0005'][0].copy()
            fine = restart_path(initial, config['window'], .0005)
            coarse = restart_path(initial, config['window'], .001)
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

                def exact(cloud, histogram):
                    density, raw_mass = exact_box_histogram_density(cloud, bounds, histogram, widths, shape)
                    if abs(raw_mass-1) > config['thresholds']['mass_error_max']:
                        raise ValueError(f'Exact-box raw mass defect {raw_mass}; no renormalization')
                    return density

                record('common_start_integration', reconstruct(coarse[1::2], histograms[0]),
                       reconstruct(fine[3::4], histograms[0]),
                       dict(count=5000, steps=[.001, .0005], common_state=initial.tolist(),
                            path_max_difference=float(np.linalg.norm(coarse-fine[1::2], axis=1).max())))
                previous_legacy = previous_exact = None
                references = {}
                for i, histogram in enumerate(histograms):
                    legacy = reconstruct(fine, histogram)
                    control = exact(fine, histogram)
                    record('architecture', legacy, control, dict(histogram=histogram,
                        alternative='Exact continuous histogram convolution without vertex lifting; diagnostic only'))
                    if i:
                        metadata = dict(histograms=[histograms[i-1], histogram], physical_widths=widths)
                        record('legacy_histogram', previous_legacy, legacy, metadata)
                        record('exact_box_histogram', previous_exact, control, metadata)
                    previous_legacy, previous_exact = legacy, control
                    references[f'legacy_h{i}'] = legacy
                    references[f'exact_h{i}'] = control
                path = run / (f'seed{seed}_grid'+ 'x'.join(map(str, shape)) + '.npz')
                np.savez_compressed(path, **references)
                outputs[path.name] = sha(path)
                del references, previous_legacy, previous_exact, legacy, control
            print(f'G02 seed {seed} completed; elapsed {time.monotonic()-started:.1f}s', flush=True)
        report = dict(experiment_id=config['id'], gate_status='OPEN', technical_status='COMPLETED',
                      records=records, elapsed_seconds=time.monotonic()-started,
                      limitations=config['limitations'], scientific_qualification=False,
                      attempted_seeds=attempted, exclusions=[], expected_comparisons=132)
        if len(records) != 132:
            raise ValueError('Incomplete comparison ledger')
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
        (run / 'partial_report.json').write_text(json.dumps(dict(records=records,
            attempted_seeds=attempted, expected_comparisons=132, completed_comparisons=len(records),
            exclusions=[], gate_status='OPEN', exception=repr(error)), indent=2)+'\n')
        provenance.update(status='FAILED', diagnostics=dict(exception=repr(error)))
        (run / 'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    execute(parser.parse_args().run.resolve())
