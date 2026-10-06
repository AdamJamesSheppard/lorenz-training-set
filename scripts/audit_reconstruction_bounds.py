"""Read-only, post-hoc finite-control bounds; never adjudicates G02."""
import argparse
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from operator_learning.reconstruction_controls import paired_box_l1_bound  # noqa: E402


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(source):
    source = Path(source).resolve()
    config = json.loads((source / 'config.json').read_text())
    seal = json.loads((source / 'seal.json').read_text())
    for name, digest in seal.items():
        if sha(source / name) != digest:
            raise ValueError(f'Source seal mismatch: {name}')
    widths = config['physical_widths']
    records = []
    for seed in config['seeds']['trajectory']:
        path = source / f'seed{seed}_paths.npz'
        if path.name not in seal:
            raise ValueError('Unsealed input path')
        with np.load(path, allow_pickle=False) as saved:
            fine, coarse = saved['dt0005'], saved['dt001']
            if fine.shape != (20000, 3) or coarse.shape != (10000, 3):
                raise ValueError('Expected source path contract changed')
            # restart_path stores t=dt,...,window. Same physical times are
            # coarse[j] and fine[2*j+1], not repeated coarse versus full fine.
            integration = paired_box_l1_bound(coarse, fine[1::2], widths)
            sampling = {}
            for count in (5000, 10000):
                stride = len(fine) // count
                sampling[str(count)] = [paired_box_l1_bound(
                    np.repeat(fine[phase::stride], stride, axis=0), fine, widths)
                    for phase in range(stride)]
            records.append(dict(seed=seed, input_sha256=seal[path.name],
                                aligned_integration_l1_upper=integration,
                                sampling_phase_l1_upper=sampling))
    worst = {str(count): max(max(row['sampling_phase_l1_upper'][str(count)])
                            for row in records) for count in (5000, 10000)}
    return dict(kind='POST_HOC_FINITE_CONTROL_ANALYSIS', gate_status='OPEN',
                scientific_qualification=False,
                source_run=str(source.relative_to(ROOT)),
                source_seal_sha256=sha(source / 'seal.json'),
                verified_artifacts=len(seal), attempted_seeds=len(records),
                exclusions=[], physical_widths=widths, records=records,
                worst_sampling_l1_upper=worst,
                worst_sampling_tv_upper={key: value/2 for key, value in worst.items()},
                worst_aligned_integration_l1_upper=max(
                    row['aligned_integration_l1_upper'] for row in records),
                git_commit=subprocess.check_output(
                    ['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip(),
                git_status=subprocess.check_output(
                    ['git', '-C', str(ROOT), 'status', '--porcelain'], text=True),
                analysis_source_hashes={name: sha(ROOT/name) for name in (
                    'scripts/audit_reconstruction_bounds.py',
                    'operator_learning/reconstruction_controls.py')},
                runtime=dict(python=platform.python_version(), numpy=np.__version__,
                             platform=platform.platform(), device='cpu'),
                command=sys.argv,
                limitations=[
                    'Bounds evaluated in floating point without interval error enclosure',
                    'Same six development windows; no fresh qualification population',
                    'Finite paired controls; no exact-trajectory or continuum bound',
                    'Sampling coupling bound can be loose; no independence assumed',
                    'Whole-space box-mixture bounds; truncation and FE transfer separate',
                    'No predeclared scientific budget; no retrospective gate pass'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    print(json.dumps(audit(parser.parse_args().source), indent=2, allow_nan=False))
