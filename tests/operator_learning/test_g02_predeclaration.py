"""G02 design safety fixtures; these do not execute scientific reconstructions."""
import json
from pathlib import Path

from operator_learning.governance import validate_predeclaration

ROOT = Path(__file__).resolve().parents[2]


def test_characterization_cannot_be_confused_with_qualification():
    path = ROOT/'experiments/operator_learning/OL-G02_reconstruction_characterization_v1.json'
    config = json.loads(path.read_text())
    validate_predeclaration(config)
    assert config['gate_id'] == 'OL-G02_RECONSTRUCTION_STABILITY'
    assert config['scientific_adjudication'] == 'OPEN_PENDING_RECONSTRUCTION_ERROR_BUDGET_AND_REVIEW'
    assert 'OPEN' in config['thresholds']['scientific_qualification']
    assert config['window'] == 10
    assert config['sampling_strides'][-1] == 1
    assert config['hardware']['gpu'] is False
    assert config['hardware']['mpi'] is False
    assert config['laws'] == list(range(6))


def test_qualification_budget_is_approved_and_g03_open_only_after_pass():
    base = ROOT/'docs/operator_learning'
    catalogue = json.loads((base/'gates.json').read_text())
    state = json.loads((base/'state.json').read_text())
    assert catalogue[2]['predeclared_thresholds']['tv_max'] == .01
    assert catalogue[2]['decision_status'] == 'PASSED'
    assert state['gates'][catalogue[3]['id']] == 'OPEN'
    assert not state['operator_surrogate_authorized_for_da']
    assert not state['operator_production_authorized']
