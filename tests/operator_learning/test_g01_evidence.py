"""Portable G01 evidence and immutable repair-history checks, no local arrays."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'docs/operator_learning'


def test_g01_passed_all_six_initial_and_final_fields():
    path = BASE/'evidence/G01_REPRESENTATION_V2_20261005.json'
    report = json.loads(path.read_text())
    assert report['technical_status'] == 'PASSED'
    assert {(r['law'], r['stage']) for r in report['records']} == {
        (law, stage) for law in range(6) for stage in ('initial', 'final')}
    assert all(all(r['checks'].values()) for r in report['records'])
    gate = json.loads((BASE/'gates.json').read_text())[1]
    assert gate['adjudication']['evidence_sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert 'native' in gate['adjudication']['limitations'].lower()


def test_g01_failure_retained_and_no_threshold_relaxation():
    failed = json.loads((BASE/'evidence/G01_REPRESENTATION_V1_FAILED_20261005.json').read_text())
    assert failed['technical_status'] == 'FAILED'
    assert all(not r['checks']['reconstruction'] for r in failed['records'])
    configs = [json.loads((ROOT/f'experiments/operator_learning/OL-G01_representation_v{i}.json').read_text())
               for i in (1, 2)]
    assert configs[0]['thresholds'] == configs[1]['thresholds']
    assert configs[0]['inputs']['operator_learning/representation.py'] != configs[1]['inputs']['operator_learning/representation.py']
    state = json.loads((BASE/'state.json').read_text())
    assert not state['current_model_scientifically_qualified']
    assert not state['operator_surrogate_authorized_for_da']
    assert not state['operator_production_authorized']
