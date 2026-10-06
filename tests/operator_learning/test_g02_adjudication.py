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


def test_characterization_adjudication_leaves_qualification_pending():
    state = json.loads((BASE / 'state.json').read_text())
    assert state['gates']['OL-G02_RECONSTRUCTION_STABILITY'] == 'OPEN'
    assert state['gates']['OL-G03_INPUT_DIVERSITY'] == 'LOCKED'
    assert 'OL-D009' in state['last_adjudicated_evidence']
    proposal = (BASE / 'RECONSTRUCTION_QUALIFICATION_PROPOSAL_V2.md').read_text()
    assert 'DRAFT, NOT EXECUTABLE PREDECLARATION' in proposal
    assert 'TO_BE_PREDECLARED_BEFORE_RUN' in proposal
