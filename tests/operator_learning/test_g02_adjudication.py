"""Portable characterization provenance cannot promote scientific qualification."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'docs/operator_learning'
PREFIX = 'G02_CHARACTERIZATION_20261006'


def test_portable_artifacts_match_original_seal():
    seal = json.loads((BASE / 'evidence' / f'{PREFIX}_SEAL.json').read_text())
    for name in ('config', 'provenance'):
        payload = (BASE / 'evidence' / f'{PREFIX}_{name.upper()}.json').read_bytes()
        assert hashlib.sha256(payload).hexdigest() == seal[f'{name}.json']
    provenance = json.loads((BASE / 'evidence' / f'{PREFIX}_PROVENANCE.json').read_text())
    assert provenance['status'] == 'COMPLETED'
    assert provenance['diagnostics']['technical_checks_passed']
    assert provenance['diagnostics']['gate_passed'] is False


def test_historical_characterization_never_becomes_qualification():
    config = json.loads((BASE / 'evidence' / f'{PREFIX}_CONFIG.json').read_text())
    assert 'OPEN' in config['thresholds']['scientific_qualification']
    proposal = (BASE / 'RECONSTRUCTION_QUALIFICATION_PROPOSAL_V2.md').read_text()
    assert 'DRAFT, NOT EXECUTABLE PREDECLARATION' in proposal
    assert 'TO_BE_PREDECLARED_BEFORE_RUN' in proposal


def test_scoped_v5_adjudication_and_portable_hashes():
    prefix = 'G02_QUALIFICATION_V5_20261006'
    seal = json.loads((BASE/'evidence'/f'{prefix}_SEAL.json').read_text())
    for name in ('config', 'provenance', 'report'):
        payload = (BASE/'evidence'/f'{prefix}_{name.upper()}.json').read_bytes()
        assert hashlib.sha256(payload).hexdigest() == seal[f'{name}.json']
    state = json.loads((BASE/'state.json').read_text())
    assert state['gates']['OL-G02_RECONSTRUCTION_STABILITY'] == 'PASSED'
    assert state['gates']['OL-G03_INPUT_DIVERSITY'] == 'OPEN'
    assert state['next_required_gate'] == 'OL-G03_INPUT_DIVERSITY'
    assert state['operator_surrogate_authorized_for_da'] is False
    report = json.loads((BASE/'evidence'/f'{prefix}_REPORT.json').read_text())
    assert len(report['records']) == 6 and report['exclusions'] == []
    for row in report['records']:
        assert row['candidate_pass']
        for bound in row['bounds']:
            assert (bound['total_tv_upper'] <= .01) == (bound['count'] == 20000)
