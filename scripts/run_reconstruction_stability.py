"""Frozen G02 characterization; no FEM, training or automatic gate promotion."""
import argparse
import hashlib
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
from operator_learning.alignment import block_resample, density_summary, distance  # noqa: E402
from operator_learning.governance import validate_predeclaration, validate_provenance  # noqa: E402
from operator_learning.reconstruction import (  # noqa: E402
    dense_occupation, dependence_diagnostic, histogram_physical_widths, physical_bandwidth_density,
)
from operator_learning.representation import reconstruct_vertices, trilinear_voxel_averages  # noqa: E402


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def execute(run):
    config = json.loads((run/'config.json').read_text())
    provenance = json.loads((run/'provenance.json').read_text())
    validate_predeclaration(config)
    if provenance['status'] != 'PREPARED_NOT_EXECUTED':
        raise ValueError('Fresh prepared run required; existing evidence never overwritten')
    if sha(run/'config.json') != provenance['config_sha256']:
        raise ValueError('Frozen config changed')
    commit = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    dirty = subprocess.check_output(['git', '-C', str(ROOT), 'status', '--porcelain'], text=True)
    if commit != provenance['git_commit'] or dirty:
        raise ValueError('Clean committed predeclaration required before scientific execution')
    versions = dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__)
    if versions != config['runtime_versions']:
        raise ValueError(f'Runtime mismatch: {versions}')
    if any(os.environ.get(name) != '1' for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS')):
        raise ValueError('Frozen run requires one BLAS/OpenMP thread')
    if config['scientific_adjudication'] != 'OPEN_PENDING_RECONSTRUCTION_ERROR_BUDGET_AND_REVIEW':
        raise ValueError('This characterization cannot auto-qualify a density estimator')
    for name, digest in config['inputs'].items():
        if sha(ROOT/name) != digest:
            raise ValueError(f'Changed input: {name}')
    started = time.monotonic()
    provenance.update(status='RUNNING', actual_command=sys.argv, observed_runtime_versions=versions,
                      observed_hardware=dict(device='cpu', platform=platform.platform(),
                                             blas_threads=1, openmp_threads=1))
    (run/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    try:
        bounds = config['bounds']
        shape, histogram = config['learning_shape'], config['histogram_shape']
        dv = float(np.prod([hi-lo for lo, hi in bounds])/np.prod(shape))
        records, dependence, pairs = [], [], []
        fixed_widths = histogram_physical_widths(bounds, histogram, config['filter_width'])
        output_hashes = {}

        def reconstruct(cloud, width=None):
            vertices = reconstruct_vertices(cloud, bounds, histogram,
                                           config['filter_width'] if width is None else width)
            return trilinear_voxel_averages(vertices, bounds, shape)

        def store_record(law, name, family, density, reference, metadata):
            mass = float(density.sum()*dv)
            negative = float(np.maximum(-density, 0).sum()*dv)
            if not np.isfinite(density).all() or negative > config['thresholds']['negative_mass_max']:
                raise ValueError(f'Invalid reconstructed density: {name}')
            if abs(mass-1) > config['thresholds']['mass_error_max']:
                raise ValueError(f'Mass check failed: {name}')
            stats = density_summary(density, bounds, **config['regions'])
            refstats = density_summary(reference, bounds, **config['regions'])
            comparison = distance(density, reference, bounds)
            comparison['tv'] = .5*comparison['l1']
            comparison.update(mean_error=float(np.linalg.norm(np.array(stats['mean'])-refstats['mean'])),
                covariance_relative_error=float(np.linalg.norm(np.array(stats['covariance'])-refstats['covariance'])/
                                                np.linalg.norm(refstats['covariance'])),
                positive_x_error=abs(stats['positive_x_probability']-refstats['positive_x_probability']),
                boundary_mass_error=abs(stats['boundary_probability']-refstats['boundary_probability']))
            record = dict(law=law, name=name, family=family, metadata=metadata,
                          raw_mass=mass, raw_negative_mass=negative, statistics=stats,
                          reference_distance=comparison)
            records.append(record)
            return record

        for law in config['laws']:
            print(f'G02 law {law}: replay, fixed-window sampling and reconstruction sensitivity', flush=True)
            source = ROOT/config['source_run']/f'law{law}'
            design = json.loads((source/'prior_design.json').read_text())
            archived = np.load(source/'attractor_samples.npy')
            expected = dict(spinup=config['spinup'], sampling_window=config['window'],
                            rk4_dt=config['dt'], sampling_interval=config['historical_stride']*config['dt'],
                            histogram_shape=histogram, compact_filter_width=config['filter_width'], gaussian_fit=False)
            if any(design.get(key) != value for key, value in expected.items()):
                raise ValueError('Historical generator parameters differ from frozen config')
            initial, dense = dense_occupation(design['seed'], config['spinup'], config['window'], config['dt'])
            if not np.array_equal(initial, np.asarray(design['trajectory_initial'])):
                raise ValueError('Initial-state replay mismatch')
            if not np.array_equal(dense[config['historical_stride']-1::config['historical_stride']], archived):
                raise ValueError('Historical trajectory replay must be bitwise identical')
            cloud_path = run/f'law{law}_dense_samples.npy'
            np.save(cloud_path, dense)
            output_hashes[cloud_path.name] = sha(cloud_path)
            baseline = reconstruct(archived)
            dense_reference = reconstruct(dense)
            density_path = run/f'law{law}_references.npz'
            np.savez_compressed(density_path, historical=baseline, dense=dense_reference)
            output_hashes[density_path.name] = sha(density_path)
            store_record(law, 'historical_to_dense', 'fixed_window_sampling', baseline, dense_reference,
                         dict(count=len(archived), dt=config['dt']*config['historical_stride'],
                              law='Same finite-window trajectory occupation; not stationary-law estimation'))
            for stride in config['sampling_strides']:
                phases = sorted({max(1, int(np.ceil(fraction*stride)))-1 for fraction in config['phase_fractions']})
                for phase in phases:
                    cloud = dense[phase::stride]
                    store_record(law, f'stride{stride}_phase{phase}', 'fixed_window_sampling', reconstruct(cloud), dense_reference,
                        dict(count=len(cloud), stride=stride, phase=phase, integration_dt=config['dt']))
            observables = dict(x=archived[:, 0], y=archived[:, 1], z=archived[:, 2],
                               positive_x=(archived[:, 0] > 0).astype(float),
                               x_squared=archived[:, 0]**2, z_squared=archived[:, 2]**2)
            dependence.append(dict(law=law, diagnostics={name: dependence_diagnostic(
                values, config['acf_max_lag'], config['historical_stride']*config['dt'])
                for name, values in observables.items()}))
            for count in config['independent_reconstruction_counts']:
                densities = []
                for rep in range(config['independent_replicates']):
                    seed = config['seeds']['independent_base']+100000*law+10*count+rep
                    rng = np.random.default_rng(seed)
                    cloud = dense[rng.integers(len(dense), size=count)]
                    density = reconstruct(cloud)
                    densities.append(density)
                    store_record(law, f'iid_count{count}_rep{rep}', 'conditional_on_fixed_trajectory_iid_times',
                        density, dense_reference, dict(count=count, seed=seed,
                        independence='Independent random time indices conditional on this fixed discrete path; not independent trajectories'))
                for a in range(len(densities)):
                    for b in range(a+1, len(densities)):
                        pairs.append(dict(law=law, family='independent_reconstruction', count=count,
                                          replicates=[a, b], **distance(densities[a], densities[b], bounds)))
            for block_length in config['block_lengths']:
                for rep in range(config['block_replicates']):
                    seed = config['seeds']['block_base']+100000*law+100*block_length+rep
                    cloud = block_resample(archived, block_length, np.random.default_rng(seed))
                    store_record(law, f'block{block_length}_rep{rep}', 'circular_block_diagnostic',
                        reconstruct(cloud), baseline, dict(block_length=block_length, seed=seed,
                        interpretation='Block-length sensitivity diagnostic; no bootstrap coverage or confidence interval claim'))
            for h in config['histogram_shapes']:
                density = physical_bandwidth_density(archived, bounds, h, fixed_widths, shape)
                store_record(law, 'histogram_'+'x'.join(map(str, h)), 'fixed_physical_smoothing_histogram',
                    density, baseline, dict(histogram_shape=h, physical_widths=fixed_widths,
                    limitation='Vertex lifting changes with histogram resolution; report joint representation sensitivity'))
            for width in config['filter_widths']:
                store_record(law, f'filter{width}', 'regularization_choice', reconstruct(archived, width), baseline,
                             dict(filter_width=width, physical_widths=histogram_physical_widths(bounds, histogram, width),
                                  interpretation='Different regularized laws; sensitivity, not noise at fixed bandwidth'))
        report = dict(experiment_id=config['id'], gate_id=config['gate_id'], technical_status='COMPLETED',
            gate_status='OPEN', scientific_status=config['scientific_adjudication'], records=records,
            dependence=dependence, independent_pairs=pairs, elapsed_seconds=time.monotonic()-started,
            limitations=config['limitations'], next_action='Review sensitivity; predeclare scientifically justified reconstruction-error budget before qualification')
        (run/'report.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
        output_hashes['report.json'] = sha(run/'report.json')
        provenance.update(status='COMPLETED', output_hashes=output_hashes,
                          diagnostics=dict(technical_checks_passed=True, gate_passed=False))
        validate_provenance(provenance)
        (run/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
        seal = {name: sha(run/name) for name in ['config.json', 'provenance.json', *output_hashes]}
        (run/'seal.json').write_text(json.dumps(seal, indent=2)+'\n')
        print(json.dumps(dict(status='COMPLETED_CHARACTERIZATION_G02_OPEN', elapsed=report['elapsed_seconds'])))
    except Exception as error:
        provenance.update(status='FAILED', diagnostics={'exception': repr(error)})
        (run/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    args = parser.parse_args()
    execute(args.run.resolve())
