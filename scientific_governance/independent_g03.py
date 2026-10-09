"""Read-only, separately implemented G03 raw-field arithmetic audit.

Method SG-G03-RAW-1: direct rectangular-cell integration and TV = half the
integral of the absolute difference of separately normalized fields. This is
an engineering verification implementation of the TV definition, not another
trajectory integrator or independent execution authority. Mathematical source:
https://ccanonne.github.io/files/compx270-chap11.pdf (TV metric/triangle inequality).
The seal must be authenticated externally: an editable local hash list supplies
integrity relative to that list, never authenticity or scientific approval.
No producer modules are imported and no archived evidence is modified.
"""
import argparse
import hashlib
from itertools import combinations
import json
from pathlib import Path
import re

import numpy as np


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _close(actual, recorded, label, tolerance=2e-12):
    _require(np.isfinite(recorded) and abs(actual-recorded) <= tolerance,
             f'{label}: recomputed {actual!r}, recorded {recorded!r}')


def _safe(root, name):
    path = Path(name)
    _require(not path.is_absolute() and '..' not in path.parts, 'Unsafe artifact path')
    result = root / path
    _require(result.resolve().is_relative_to(root), 'Artifact escapes run directory')
    _require(not result.is_symlink() and result.is_file(), f'Missing/linked artifact: {name}')
    return result


def verify(run, seal_name='seal.json'):
    """Fail closed on discrepancies; return arithmetic findings, never approval.

    Loads at most the four fields of one law plus one final field per law.
    For v4 this is approximately 70 MiB, independent of trajectory payload size.
    """
    root = Path(run).resolve(strict=True)
    seal = json.loads(_safe(root, seal_name).read_text())
    _require(isinstance(seal, dict) and seal, 'Empty seal')
    for name, expected_hash in seal.items():
        _require(isinstance(expected_hash, str) and re.fullmatch('[0-9a-f]{64}', expected_hash),
                 'Invalid SHA256')
        digest = hashlib.sha256()
        with _safe(root, name).open('rb') as stream:
            for block in iter(lambda: stream.read(1024*1024), b''):
                digest.update(block)
        _require(digest.hexdigest() == expected_hash, f'Artifact hash mismatch: {name}')
    config = json.loads(_safe(root, 'config.json').read_text())
    report = json.loads(_safe(root, 'report.json').read_text())
    seeds, windows = config['seeds']['trajectory'], config['windows']
    _require(seeds and len(set(seeds)) == len(seeds) and windows > 0, 'Invalid population')
    expected_ids = [f'seed{s}_window{w}' for s in seeds for w in range(windows)]
    required = {'config.json', 'provenance.json', 'report.json', 'partial_report.json'}
    required.update(f'seed{s}_fine.npz' for s in seeds)
    required.update(f'{i}_{suffix}.npz' for i in expected_ids for suffix in ('control', 'densities'))
    _require(set(seal) == required, 'Incomplete or unexpected seal artifact ledger')
    laws = report['laws']
    _require(len(laws) == len(expected_ids) and {r['id'] for r in laws} == set(expected_ids),
             'Missing, duplicate or unexpected law')
    _require(report['exclusions'] == [], 'Excluded attempts')
    shape = tuple(config['shape'])
    _require(len(shape) == 3 and all(n > 0 for n in shape), 'Invalid grid shape')
    bounds = np.asarray(config['bounds'], dtype=float)
    _require(bounds.shape == (3, 2) and np.isfinite(bounds).all()
             and (bounds[:, 1] > bounds[:, 0]).all(), 'Invalid physical bounds')
    volume = float(np.prod((bounds[:, 1]-bounds[:, 0])/shape))
    tolerance = config['thresholds']['mass_error_max']
    within_expected, fields, by_id = {}, {}, {}
    for row in laws:
        ident = row['id']
        _require(row['status'] == 'COMPLETED', f'Failed attempt: {ident}')
        _require(ident == f"seed{row['source']}_window{row['window']}", 'Law/source mismatch')
        _require(row['path'] == ident+'_densities.npz', 'Wrong density artifact')
        raw = row['raw']
        _require(len(raw) == 4 and {r['phase'] for r in raw} == set(range(4)), 'Missing raw phase')
        raw = {r['phase']: r for r in raw}
        with np.load(_safe(root, row['path']), allow_pickle=False) as archive:
            _require(set(archive.files) == {f'phase{i}' for i in range(4)}, 'Wrong phase keys')
            normalized = []
            for phase in range(4):
                field = np.asarray(archive[f'phase{phase}'], dtype=float)
                _require(field.shape == shape and np.isfinite(field).all(), 'Invalid field shape/value')
                _require((field >= 0).all(), 'Negative density')
                mass = float(np.sum(field, dtype=np.float64)*volume)
                _require(mass > 0 and abs(mass-1) <= tolerance, 'Grid mass failed')
                _close(mass, raw[phase]['mass'], 'Raw/grid mass', tolerance)
                _require(abs(raw[phase]['mass']-1) <= tolerance, 'Recorded raw mass failed')
                _close(0., raw[phase]['negative_mass'], 'Recorded negative mass', 0.)
                normalized.append(field/mass)
            fields[ident] = normalized[3]
            for a, b in combinations(range(4), 2):
                within_expected[(ident, a, b)] = float(np.sum(np.abs(normalized[a]-normalized[b]))*volume/2)
        _close(raw[3]['mass'], row['raw_mass'], 'Final raw mass', 0.)
        _close(0., row['negative_mass'], 'Law negative mass', 0.)
        bound = row['reconstruction_tv_bound']
        _require(np.isfinite(bound) and 0 <= bound <= config['thresholds']['reconstruction_tv_max'],
                 'Reconstruction control failed')
        _close(bound, row['bound']['total_tv_upper'], 'Bound summary', 0.)
        by_id[ident] = row
    _require(report['expected_within'] == len(within_expected), 'Wrong within denominator')
    seen = set()
    for row in report['within']:
        key = (row['law'], *row['phases'])
        _require(key in within_expected and key not in seen, 'Missing/duplicate/invalid within pair')
        seen.add(key)
        _close(within_expected[key], row['tv'], 'Within-law TV')
    _require(seen == set(within_expected), 'Missing within pairs')
    pair_keys = set(combinations(sorted(expected_ids), 2))
    _require(report['expected_pairs'] == len(pair_keys), 'Wrong between denominator')
    margins, seen = {}, set()
    for pair in report['pairs']:
        key = tuple(sorted((pair['a'], pair['b'])))
        _require(key in pair_keys and key not in seen, 'Missing/duplicate/invalid between pair')
        seen.add(key)
        a, b = key
        tv = float(np.sum(np.abs(fields[a]-fields[b]))*volume/2)
        _close(tv, pair['tv'], 'Between-law TV')
        _close(2*tv, pair['metrics']['l1'], 'Between-law L1')
        same = by_id[a]['source'] == by_id[b]['source']
        _require(pair['family'] == ('WITHIN_SOURCE' if same else 'CROSS_SOURCE'), 'Wrong pair family')
        # Arithmetic follows the frozen finite-control rule, not a continuum theorem.
        margins[key] = (pair['tv']-by_id[a]['reconstruction_tv_bound']-by_id[b]['reconstruction_tv_bound']
                        -abs(by_id[a]['raw_mass']-1)-abs(by_id[b]['raw_mass']-1)-tolerance)
    _require(seen == pair_keys, 'Missing between pairs')
    evaluation = report['evaluation']
    resolved = evaluation['resolved_pairs'] + evaluation['ambiguous_pairs']
    _require(len(resolved) == len(pair_keys), 'Missing margin records')
    checked = set()
    for record in resolved:
        key = tuple(sorted(record['pair']))
        _require(key in margins and key not in checked, 'Invalid/duplicate margin record')
        checked.add(key)
        _close(margins[key], record['signed_margin'], 'Signed margin')
    expected_witnesses = {i: sorted(j for j in expected_ids if j != i
                                  and by_id[i]['source'] != by_id[j]['source']
                                  and margins[tuple(sorted((i, j)))] > 0) for i in expected_ids}
    _require(evaluation['witnesses'] == {i: evaluation['witnesses'][i] for i in expected_ids}, 'Witness IDs')
    _require(all(sorted(evaluation['witnesses'][i]) == expected_witnesses[i] for i in expected_ids),
             'Incorrect witness ledger')
    return dict(status='RAW_ARRAY_ARITHMETIC_VERIFIED', artifacts=len(seal), laws=len(laws),
                within_pairs=len(within_expected), between_pairs=len(pair_keys),
                minimum_signed_margin=min(margins.values()), automatic_promotion=False,
                limitations=['Seal authenticity requires an external trusted digest',
                             'Controls are reported finite bounds, not independently reintegrated',
                             'Field reconstruction is not regenerated from trajectories',
                             'Separate algorithm; same operator/credentials may remain'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('--seal', default='seal.json')
    args = parser.parse_args()
    try:
        result = verify(args.run, args.seal)
    except (ValueError, KeyError, OSError, TypeError) as error:
        print(json.dumps(dict(status='REJECTED', error=str(error), automatic_promotion=False)))
        return 1
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
