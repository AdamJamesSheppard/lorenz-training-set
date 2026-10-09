"""Prospective G03 evidence evaluator; never changes programme status.

Bounds are finite reconstruction controls, not continuum error certificates.
The proposed witness rule demonstrates non-collapse only, not training coverage.
"""
from itertools import combinations
import math


def evaluate(laws, pairs, expected_ids, *, reconstruction_tv_max, mass_error_max):
    """Keep all attempts; require complete evidence and cross-source witnesses.

    Each law: id, source, status, reconstruction_tv_bound, raw_mass,
    negative_mass. Each pair: a, b, tv. TV uses normalized learning-grid laws.
    Thresholds must be frozen by the caller before generating new evidence.
    """
    for value in (reconstruction_tv_max, mass_error_max):
        if not math.isfinite(value) or value < 0:
            raise ValueError('Finite nonnegative thresholds required')
    expected = list(expected_ids)
    if not expected or len(set(expected)) != len(expected):
        raise ValueError('Nonempty unique expected law IDs required')
    rows = list(laws)
    ids = [row['id'] for row in rows]
    if len(set(ids)) != len(ids):
        raise ValueError('Duplicate attempt identifiers')
    if set(ids) - set(expected):
        raise ValueError('Unexpected attempts require a new experiment definition')
    by_id = {row['id']: row for row in rows}
    failures = []
    for ident in expected:
        row = by_id.get(ident)
        if row is None:
            failures.append({'id': ident, 'reason': 'MISSING_ATTEMPT'})
            continue
        if row.get('status') != 'COMPLETED':
            failures.append({'id': ident, 'reason': 'FAILED_ATTEMPT'})
            continue
        values = [row.get(k) for k in ('reconstruction_tv_bound', 'raw_mass', 'negative_mass')]
        if (not all(isinstance(v, (int, float)) and math.isfinite(v) for v in values)
                or values[0] < 0 or values[1] <= 0 or values[2] < 0
                or not row.get('source')):
            failures.append({'id': ident, 'reason': 'INVALID_CONTROL'})
        elif (values[0] > reconstruction_tv_max or abs(values[1]-1) > mass_error_max
              or values[2] != 0):
            failures.append({'id': ident, 'reason': 'CONTROL_GATE_FAILED'})
    invalid = {f['id'] for f in failures}
    seen, resolved, ambiguous = set(), [], []
    witnesses = {ident: [] for ident in expected}
    for pair in pairs:
        a, b, tv = pair['a'], pair['b'], pair['tv']
        if a == b or a not in expected or b not in expected:
            raise ValueError('Invalid pair identity')
        key = tuple(sorted((a, b)))
        if key in seen:
            raise ValueError('Duplicate pair evidence')
        seen.add(key)
        if not isinstance(tv, (int, float)) or not math.isfinite(tv) or not 0 <= tv <= 1:
            raise ValueError('TV must be finite and between zero and one')
        if a in invalid or b in invalid:
            ambiguous.append(dict(pair=key, reason='INVALID_OR_MISSING_CONTROL'))
            continue
        left, right = by_id[a], by_id[b]
        lower = tv-left['reconstruction_tv_bound']-right['reconstruction_tv_bound']
        lower -= abs(left['raw_mass']-1)+abs(right['raw_mass']-1)+mass_error_max
        record = dict(pair=key, measured_tv=tv, signed_margin=lower)
        (resolved if lower > 0 else ambiguous).append(record)
        if lower > 0 and left['source'] != right['source']:
            witnesses[a].append(b)
            witnesses[b].append(a)
    missing_pairs = sorted(set(combinations(sorted(expected), 2))-seen)
    unsupported = [ident for ident in expected if not witnesses[ident]]
    eligible = not (failures or missing_pairs or unsupported)
    return dict(
        review_status='ELIGIBLE_FOR_SCOPED_REVIEW' if eligible else 'FAILED_PROPOSED_CRITERIA',
        gate_status='OPEN', automatic_promotion=False, expected_attempts=len(expected),
        actual_attempts=len(rows), failures=failures, missing_pairs=missing_pairs,
        unresolved_laws=unsupported, witnesses=witnesses, resolved_pairs=resolved,
        ambiguous_pairs=ambiguous, exclusions=[],
        claim_scope='Finite-control cross-source non-collapse; no coverage or continuum claim')


if __name__ == '__main__':
    import argparse
    import json
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence', type=Path,
                        help='JSON with laws, pairs, expected_ids and thresholds')
    args = parser.parse_args()
    data = json.loads(args.evidence.read_text())
    print(json.dumps(evaluate(data['laws'], data['pairs'], data['expected_ids'],
                              **data['thresholds']), indent=2, allow_nan=False))
