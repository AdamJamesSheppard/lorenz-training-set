"""Documentation safeguards; these tests do not qualify an assimilation method."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_full_density_contract_is_discoverable():
    contract = ROOT / 'docs/BAYESIAN_ASSIMILATION_CONTRACT.md'
    text = contract.read_text()
    for term in ('Kalman', 'EnKF', '3DVar', '4DVar', 'Gaussian-mixture',
                 '0<Z_k<\\infty', 'G02 passed', 'Smoothing', 'assumption-free'):
        assert term in text
    for relative in ('AGENTS.md', 'SCIENTIFIC_INTEGRITY.md',
                     'docs/PROJECT_STATE.md', 'docs/operator_learning/README.md',
                     'docs/operator_learning/PROBLEM.md'):
        assert 'BAYESIAN_ASSIMILATION_CONTRACT.md' in (ROOT / relative).read_text()


def test_reserved_approval_does_not_promote_g02():
    import json
    state = json.loads((ROOT / 'docs/operator_learning/state.json').read_text())
    assert state['gates']['OL-G02_RECONSTRUCTION_STABILITY'] == 'PASSED'
    assert state['operator_surrogate_authorized_for_da'] is False
    text = (ROOT / 'docs/operator_learning/RECONSTRUCTION_CANDIDATE_APPROVAL_V2.md').read_text()
    assert 'not a scientific G02 pass' in text
    assert 'potentially discontinuous' in text
