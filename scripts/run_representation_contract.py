"""Execute frozen G01 against archived arrays; never launch FEM or training."""
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
from operator_learning.governance import validate_predeclaration, validate_provenance  # noqa: E402
from operator_learning.numerics import conservative_coarsen, density_l1  # noqa: E402
from operator_learning.representation import (  # noqa: E402
    decode_tensor, encode_tensor, reconstruct_vertices, trilinear_voxel_averages, vertex_mass,
)


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
        raise ValueError('Fresh prepared directory required; evidence never overwritten')
    if sha(run/'config.json') != provenance['config_sha256']:
        raise ValueError('Changed frozen config')
    commit = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    dirty = subprocess.check_output(['git', '-C', str(ROOT), 'status', '--porcelain'], text=True)
    if dirty or commit != provenance['git_commit']:
        raise ValueError('Clean predeclaration commit required')
    versions = dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__)
    if versions != config['runtime_versions']:
        raise ValueError(f'Runtime mismatch: {versions}')
    for name, digest in config['inputs'].items():
        if sha(ROOT/name) != digest:
            raise ValueError(f'Changed input: {name}')
    started = time.monotonic()
    provenance.update(status='RUNNING', actual_command=sys.argv, observed_runtime_versions=versions,
                      observed_hardware=dict(device='cpu', platform=platform.platform(),
                                             cpu_count=os.cpu_count()))
    (run/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    try:
        bounds, fine_shape, shape = config['bounds'], config['fine_shape'], config['learning_shape']
        volume = float(np.prod([hi-lo for lo, hi in bounds]))
        fine_dv, dv = volume/np.prod(fine_shape), volume/np.prod(shape)
        thresholds = config['thresholds']
        records = []
        for law in config['laws']:
            print(f'G01 law {law}: reconstruction, fine exports, float32 and tensor', flush=True)
            source = ROOT/config['source_run']/f'law{law}'
            samples = np.load(source/'attractor_samples.npy')
            vertices = reconstruct_vertices(samples, bounds, config['histogram_shape'], config['filter_width'])
            raw = np.fromfile(source/'empirical_prior.bin', dtype='<f8').reshape(vertices.shape)
            reconstruction_equal = bool(np.array_equal(vertices, raw))
            reconstructed = trilinear_voxel_averages(vertices, bounds, fine_shape)
            summary = json.loads((source/'mfem/mature_summary.json').read_text())
            with np.load(source/'pair.npz') as pair:
                for stage in ('initial', 'final'):
                    path = source/f'mfem/{stage}_q2_subcell_averages.bin'
                    if path.stat().st_size != int(np.prod(fine_shape))*8:
                        raise ValueError('Wrong raw file size')
                    fine = np.memmap(path, dtype='<f8', mode='r', shape=tuple(fine_shape), order='C')
                    coarse = conservative_coarsen(fine, shape)
                    density = pair[stage]
                    tensor = encode_tensor(density, volume)
                    mass = float(fine.sum()*fine_dv)
                    float32_budget = thresholds['float32_eps_multiplier']*float(np.finfo(np.float32).eps)*abs(mass)
                    float32_budget += volume*float(np.finfo(np.float32).smallest_subnormal)
                    record = dict(law=law, stage=stage, finite=bool(np.isfinite(fine).all()),
                        shape=list(density.shape), dtype=str(density.dtype), tensor_shape=list(tensor.shape),
                        reconstruction_bitwise_equal=reconstruction_equal, vertex_mass=vertex_mass(raw, bounds),
                        fine_mass=mass, fe_mass=float(summary[f'{stage}_mass']),
                        export_mass_error=abs(mass-summary[f'{stage}_mass']),
                        coarsening_mass_error=abs(float(coarse.sum()*dv)-mass),
                        negative_mass=float(np.maximum(-fine, 0).sum()*fine_dv),
                        pair_cast_bitwise_equal=bool(np.array_equal(coarse.astype(np.float32), density)),
                        float32_l1=density_l1(coarse, density.astype(float), dv),
                        tensor_roundtrip_l1=density_l1(density.astype(float), decode_tensor(tensor, volume), dv),
                        float32_budget=float32_budget)
                    if stage == 'initial':
                        record['initial_projection_export_l1'] = density_l1(reconstructed, fine, fine_dv)
                    checks = dict(
                        finite=record['finite'], reconstruction=reconstruction_equal,
                        vertex_mass=abs(record['vertex_mass']-1) <= thresholds['mass_error_max'],
                        fe_mass=abs(record['fe_mass']-1) <= thresholds['mass_error_max'],
                        export_mass=record['export_mass_error'] <= thresholds['mass_error_max'],
                        coarsening=record['coarsening_mass_error'] <= thresholds['mass_error_max'],
                        negativity=record['negative_mass'] <= thresholds['negative_mass_max'],
                        pair_identity=record['pair_cast_bitwise_equal'],
                        float32=record['float32_l1'] <= float32_budget,
                        tensor=record['tensor_roundtrip_l1'] <= float32_budget,
                        initial_projection=record.get('initial_projection_export_l1', 0) <= thresholds['projection_export_l1_max'])
                    record['checks'] = checks
                    records.append(record)
                    del fine
            del reconstructed
        passed = all(all(record['checks'].values()) for record in records)
        report = dict(experiment_id=config['id'], gate_id=config['gate_id'],
            technical_status='PASSED' if passed else 'FAILED', records=records,
            elapsed_seconds=time.monotonic()-started, limitations=config['limitations'],
            scientific_status='TECHNICAL_EVIDENCE_REQUIRES_SCOPED_ADJUDICATION')
        (run/'report.json').write_text(json.dumps(report, indent=2)+'\n')
        provenance.update(status='COMPLETED', diagnostics=dict(all_checks_passed=passed),
                          output_hashes={'report.json': sha(run/'report.json')})
        validate_provenance(provenance)
        (run/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
        seal = {name: sha(run/name) for name in ('config.json', 'report.json', 'provenance.json')}
        (run/'seal.json').write_text(json.dumps(seal, indent=2)+'\n')
        print(json.dumps(dict(status=report['technical_status'], elapsed=report['elapsed_seconds'])))
        return passed
    except Exception as error:
        provenance.update(status='FAILED', diagnostics={'exception': repr(error)})
        (run/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    args = parser.parse_args()
    sys.exit(0 if execute(args.run.resolve()) else 1)
