"""Execute one frozen small OL-G00 comparison; never generate FEM targets/train."""
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
from operator_learning.alignment import (  # noqa: E402
    block_resample, condition_density, density_summary, distance,
    draw_density, evolve_sde, reconstruct,
)
from operator_learning.governance import validate_predeclaration, validate_provenance  # noqa: E402


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def execute(run):
    config = json.loads((run/'config.json').read_text())
    provenance = json.loads((run/'provenance.json').read_text())
    validate_predeclaration(config)
    if provenance['status'] != 'PREPARED_NOT_EXECUTED':
        raise ValueError('Fresh prepared run required; completed/failed runs never overwritten')
    if sha(run/'config.json') != provenance['config_sha256']:
        raise ValueError('Frozen config changed')
    commit = subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip()
    dirty = subprocess.check_output(['git','status','--short'], text=True)
    if commit != provenance['git_commit'] or dirty:
        raise ValueError('Run must use clean predeclaration commit')
    versions = dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__)
    if versions != config['runtime_versions']:
        raise ValueError(f'Runtime mismatch: {versions}')
    for path, digest in config['inputs'].items():
        if sha(ROOT/path) != digest:
            raise ValueError(f'Changed input: {path}')
    started = time.monotonic()
    provenance.update(status='RUNNING', actual_command=sys.argv,
                      observed_runtime_versions=versions,
                      observed_hardware=dict(platform=platform.platform(), device='cpu',
                                             cpu_count=os.cpu_count(), threads=1))
    (run/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    records, comparisons, observation_records = [], [], []
    bounds, shape = config['bounds'], config['learning_shape']
    source = ROOT/config['source_run']
    (run/'densities').mkdir()

    def store(name, family, law, replicate, density, metadata):
        path = run/'densities'/f'{name}.npz'
        np.savez_compressed(path, density=density)
        records.append(dict(id=name, family=family, law=law, replicate=replicate,
            array_path=str(path.relative_to(run)), sha256=sha(path), metadata=metadata,
            statistics=density_summary(density, bounds, **config['regions'])))

    try:
        for law in config['laws']:
            print(f'Law {law}: reconstruct / ensemble / conditioning', flush=True)
            with np.load(source/f'law{law}/pair.npz') as pair:
                initial = pair['initial'].astype(float)
            samples = np.load(source/f'law{law}/attractor_samples.npy')
            store(f'occupation_{law}', 'OCCUPATION_PILOT_V1', law, None, initial,
                  dict(interpretation='accepted FE/voxel representation of regularized occupation law',
                       conditioning='none', source_group=f'historical-law{law}'))
            reconstructed = reconstruct(samples, bounds, config['histogram_shape'], shape,
                                        config['filter_width'])
            diagnostic = distance(initial, reconstructed, bounds)
            # FE projection/positivity versus reconstruction remains G01/G04 evidence gap.
            bootstrap = []
            for rep in range(config['replicates']):
                seed = config['seeds']['block_base']+100*law+rep
                cloud = block_resample(samples, config['block_length'], np.random.default_rng(seed))
                p = reconstruct(cloud, bounds, config['histogram_shape'], shape, config['filter_width'])
                bootstrap.append(p)
                store(f'occupation_block_{law}_{rep}', 'OCCUPATION_BLOCK_DIAGNOSTIC', law, rep, p,
                      dict(seed=seed, block_length=config['block_length'], independent_law=False,
                           interpretation='dependent-window resampling diagnostic; not a confidence interval'))
            truth_seed = config['seeds']['truth_base']+law
            truth_rng = np.random.default_rng(truth_seed)
            truth_initial = draw_density(initial, bounds, 1, truth_rng)
            truth_final, _ = evolve_sde(truth_initial, config['D'], config['dt'], config['steps'],
                                       truth_rng, bounds)
            noise_seed = config['seeds']['observation_base']+law
            epsilon = np.random.default_rng(noise_seed).standard_normal(3)
            observation_records.append(dict(law=law, truth_seed=truth_seed, noise_seed=noise_seed,
                truth_initial=truth_initial[0].tolist(), truth_final=truth_final[0].tolist(),
                epsilon=epsilon.tolist(), interpretation='computed independent stochastic truth, one observation time'))
            ensembles, conditioned = [], {}
            for rep in range(config['replicates']):
                seed = config['seeds']['ensemble_base']+100*law+rep
                rng = np.random.default_rng(seed)
                particles = draw_density(initial, bounds, config['particle_count'], rng)
                final, exits = evolve_sde(particles, config['D'], config['dt'], config['steps'], rng, bounds)
                np.savez_compressed(run/f'ensemble_particles_{law}_{rep}.npz', initial=particles, final=final)
                p = reconstruct(final, bounds, config['histogram_shape'], shape, config['filter_width'])
                ensembles.append(p)
                store(f'ensemble_{law}_{rep}', 'STOCHASTIC_ENSEMBLE_G00_V2', law, rep, p,
                      dict(seed=seed, count=len(final), time=config['horizon'], path_exits=exits,
                           interpretation='regularized finite-time Euler-Maruyama whole-space SDE ensemble law',
                           boundary_note='no reflecting simulation; zero observed exits does not certify boundary effects'))
                for name, dims in config['observation_maps'].items():
                    for variance in config['observation_variances']:
                        observation = truth_final[0,dims]+np.sqrt(variance)*epsilon[dims]
                        q, evidence = condition_density(p, bounds, dims, observation, variance)
                        key = f'{name}_R{variance}'
                        conditioned.setdefault(key, []).append(q)
                        store(f'posterior_{law}_{rep}_{key}', 'CONDITIONED_VOXEL_G00_V2', law, rep, q,
                              dict(truth_seed=truth_seed, noise_seed=noise_seed, dimensions=dims,
                                   observation=observation.tolist(), variance=variance, evidence=evidence,
                                   interpretation='voxel averages of piecewise-constant ensemble prior times Gaussian likelihood',
                                   conditioning='single truth-derived observation; not a sequential DA posterior',
                                   related_group=f'historical-law{law}', state_gaussian_fit=False))
            item = dict(law=law, reconstruction_vs_FE=diagnostic,
                        occupation_block_replicate_distance=distance(*bootstrap, bounds),
                        ensemble_replicate_distance=distance(*ensembles, bounds),
                        occupation_vs_ensemble=[distance(initial, p, bounds) for p in ensembles],
                        conditioned={})
            for key, qs in conditioned.items():
                item['conditioned'][key] = dict(replicate_distance=distance(*qs, bounds),
                    prior_to_conditioned=[distance(p,q,bounds) for p,q in zip(ensembles,qs)],
                    nearest_occupation_l1=[])
                for q in qs:
                    nearest = []
                    for other in config['laws']:
                        with np.load(source/f'law{other}/pair.npz') as pair:
                            nearest.append(distance(pair['initial'], q, bounds)['l1'])
                    item['conditioned'][key]['nearest_occupation_l1'].append(min(nearest))
            comparisons.append(item)
        statistics = [r['statistics'] for r in records]
        technical_checks = dict(
            density_mass=all(abs(s['mass']-1) <= config['thresholds']['mass_error_max'] for s in statistics),
            nonnegative=all(s['negative_mass'] == 0 for s in statistics),
            all_families_recorded=all(any(r['family']==family for r in records) for family in config['required_families']),
            complete_comparisons=len(comparisons)==len(config['laws']),
            no_target_generation_or_training=True)
        report = dict(experiment_id=config['id'], gate_id=config['gate_id'],
            predeclaration_commit=commit, kind='G00_ALIGNMENT_EVIDENCE_PENDING_OWNER_REVIEW',
            config_sha256=sha(run/'config.json'), technical_checks=technical_checks,
            technical_evidence_complete=all(technical_checks.values()), gate_status='OPEN',
            owner_population_approval='REQUIRED_AFTER_REPORT', records=records,
            comparisons=comparisons, observations=observation_records,
            runtime_seconds=time.monotonic()-started,
            limitations=config['limitations'], forbidden_claims=config['forbidden_claims'])
        (run/'report.json').write_text(json.dumps(report, indent=2)+'\n')
        provenance['output_hashes'] = {str(p.relative_to(run)):sha(p) for p in sorted(run.rglob('*'))
                                       if p.is_file() and p.name not in ('provenance.json','config.json','seal.json')}
        provenance.update(status='COMPLETED', diagnostics=technical_checks)
        validate_provenance(provenance)
        (run/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
        (run/'seal.json').write_text(json.dumps({**provenance['output_hashes'],
            'provenance.json':sha(run/'provenance.json'), 'config.json':sha(run/'config.json')}, indent=2)+'\n')
        print(json.dumps(dict(run=str(run), technical_checks=technical_checks,
                              gate_status='OPEN', seconds=report['runtime_seconds'])), flush=True)
    except BaseException as error:
        provenance.update(status='FAILED', diagnostics={'error':str(error)})
        (run/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    execute(parser.parse_args().run)
