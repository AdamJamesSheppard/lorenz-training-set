"""Tracked retrospective evidence integrity; no local payload or Torch needed."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def report():
    base = ROOT / 'docs/operator_learning/evidence'
    seals = json.loads((base / 'seals.json').read_text())
    path = base / 'PILOT_20261004T133438Z.json'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == seals[path.name]
    return json.loads(path.read_text())


def test_historical_operational_acceptance_and_provenance():
    data = report()
    assert data['pair_hashes_verified'] is True
    assert data['audit_provenance']['git_status'] == ''
    assert data['kind'] == 'RETROSPECTIVE_HISTORICAL_AUDIT_NOT_GATE_PASS'
    assert len(data['law_summaries']) == 6
    for entry in data['law_summaries']:
        summary = entry['summary']
        assert summary['steps'] == 320
        assert summary['whole_cell_positivity_certified']
        assert summary['maximum_uncertified_cells'] == 0
        assert summary['optimizer_failures'] == summary['fallbacks'] == 0
        assert summary['maximum_absolute_mass_error'] < 1e-10
        assert all(entry['acceptance']['gates'].values())


def test_pilot_errors_preserved_without_qualification():
    data = report()
    test = data['recorded_evaluation']['results'][-1]
    assert test['operator']['l1'] < test['persistence']['l1']
    assert test['operator']['relative_covariance_error'] > test['persistence']['relative_covariance_error']
    assert data['history_summary']['checkpoint_epoch'] == 99
    assert data['original_test_inspected_date'] == '2026-10-05'
    assert data['additional_cpu_diagnostics'][-1]['neural_boundary_probability'] > .01
