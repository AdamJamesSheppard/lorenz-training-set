"""Adversarial raw-evidence mutations; no producer helper functions used."""
import hashlib
from itertools import combinations
import json

import numpy as np
import pytest

from scientific_governance.independent_g03 import verify


def dump(path, value):
    path.write_text(json.dumps(value))


def reseal(root):
    dump(root/'seal.json', {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in root.iterdir() if p.name != 'seal.json'})


@pytest.fixture
def evidence(tmp_path):
    config = dict(seeds=dict(trajectory=[1, 2]), windows=1, shape=[2, 1, 1],
                  bounds=[[0, 2], [0, 1], [0, 1]],
                  thresholds=dict(mass_error_max=1e-10, reconstruction_tv_max=.01))
    laws, within, fields = [], [], {}
    for seed in [1, 2]:
        ident = f'seed{seed}_window0'
        field = np.array([.8, .2] if seed == 1 else [.2, .8]).reshape(2, 1, 1)
        fields[ident] = field
        np.savez(tmp_path/f'{ident}_densities.npz', **{f'phase{p}': field for p in range(4)})
        np.savez(tmp_path/f'{ident}_control.npz', coarse=np.zeros((2, 3)))
        np.savez(tmp_path/f'seed{seed}_fine.npz', fine=np.zeros((4, 3)))
        laws.append(dict(id=ident, source=str(seed), window=0, status='COMPLETED',
                         path=ident+'_densities.npz', reconstruction_tv_bound=.001,
                         bound=dict(total_tv_upper=.001), raw_mass=1., negative_mass=0.,
                         raw=[dict(phase=p, mass=1., negative_mass=0.) for p in range(4)]))
        within.extend(dict(law=ident, phases=[a,b], tv=0.) for a,b in combinations(range(4),2))
    ids = [r['id'] for r in laws]
    report = dict(laws=laws, within=within, exclusions=[], expected_within=12, expected_pairs=1,
                  pairs=[dict(a=ids[0], b=ids[1], tv=.6, metrics=dict(l1=1.2), family='CROSS_SOURCE')],
                  evaluation=dict(resolved_pairs=[dict(pair=ids, signed_margin=.6-.001-.001-1e-10)],
                                  ambiguous_pairs=[], witnesses={ids[0]: [ids[1]],ids[1]: [ids[0]]}))
    for name, value in [('config.json',config),('report.json',report),('partial_report.json',{}),('provenance.json',{})]:
        dump(tmp_path/name,value)
    reseal(tmp_path)
    return tmp_path


def test_valid_read_only(evidence):
    before = {p.name:p.read_bytes() for p in evidence.iterdir()}
    assert verify(evidence)['between_pairs'] == 1
    assert before == {p.name:p.read_bytes() for p in evidence.iterdir()}


@pytest.mark.parametrize('mutation', ['missing_law','missing_pair','tv','denominator','within',
                                     'margin','raw_mass','witness','duplicate_within'])
def test_report_mutations_rejected_even_when_resealed(evidence, mutation):
    path = evidence/'report.json'
    report = json.loads(path.read_text())
    if mutation == 'missing_law': report['laws'].pop()
    if mutation == 'missing_pair': report['pairs'].clear()
    if mutation == 'tv': report['pairs'][0]['tv'] = .4
    if mutation == 'denominator': report['expected_pairs'] = 2
    if mutation == 'within': report['within'][0]['tv'] = .1
    if mutation == 'margin': report['evaluation']['resolved_pairs'][0]['signed_margin'] = .9
    if mutation == 'raw_mass': report['laws'][0]['raw'][0]['mass'] = .5
    if mutation == 'witness': report['evaluation']['witnesses']['seed1_window0'] = []
    if mutation == 'duplicate_within': report['within'][-1] = report['within'][0]
    dump(path,report)
    reseal(evidence)
    with pytest.raises(ValueError): verify(evidence)


@pytest.mark.parametrize('kind', ['negative','mass','shape','nan'])
def test_bad_fields_rejected_after_reseal(evidence, kind):
    field = np.array([.8,.2]).reshape(2,1,1)
    if kind == 'negative': field[1] = -.1
    if kind == 'mass': field *= 2
    if kind == 'shape': field = field.reshape(1,2,1)
    if kind == 'nan': field[0] = np.nan
    np.savez(evidence/'seed1_window0_densities.npz', **{f'phase{p}':field for p in range(4)})
    reseal(evidence)
    with pytest.raises(ValueError): verify(evidence)


def test_corruption_rejected(evidence):
    with (evidence/'seed1_fine.npz').open('ab') as stream: stream.write(b'corruption')
    with pytest.raises(ValueError,match='hash mismatch'): verify(evidence)


def test_omitted_seal_entry_rejected(evidence):
    seal = json.loads((evidence/'seal.json').read_text())
    del seal['seed1_fine.npz']
    dump(evidence/'seal.json',seal)
    with pytest.raises(ValueError,match='ledger'): verify(evidence)


def test_unsafe_path_rejected(evidence):
    seal = json.loads((evidence/'seal.json').read_text())
    seal['../escape'] = 'a'*64
    dump(evidence/'seal.json',seal)
    with pytest.raises(ValueError,match='Unsafe'): verify(evidence)
