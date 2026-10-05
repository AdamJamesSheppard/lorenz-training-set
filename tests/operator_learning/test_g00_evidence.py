"""Portable G00 decision/integrity tests; no local run payloads needed."""
import json
from pathlib import Path

from operator_learning.governance import validate_programme

BASE = Path(__file__).resolve().parents[2] / 'docs/operator_learning'


def test_g00_evidence_complete_without_approval_or_qualification():
    report = json.loads((BASE/'evidence/G00_ALIGNMENT_V2_20261005.json').read_text())
    assert report['technical_evidence_complete'] and all(report['technical_checks'].values())
    assert report['gate_status'] == 'OPEN'
    assert report['owner_population_approval'] == 'REQUIRED_AFTER_REPORT'
    assert len(report['comparisons']) == 6
    assert len(report['records']) == 102
    assert sum(r['family']=='CONDITIONED_VOXEL_G00_V2' for r in report['records']) == 72
    for comparison in report['comparisons']:
        for condition in comparison['conditioned'].values():
            assert all(d['l1'] > comparison['ensemble_replicate_distance']['l1']
                       for d in condition['prior_to_conditioned'])


def test_owner_approval_cannot_be_implicitly_fabricated():
    state = json.loads((BASE/'state.json').read_text())
    gates = json.loads((BASE/'gates.json').read_text())
    generators = json.loads((BASE/'generators.json').read_text())
    assert gates[0]['adjudication']['approver']
    assert gates[0]['decision_status'] == 'PASSED'
    assert all(not g['allowed_for_training'] for g in generators)
    gates[0]['adjudication']['approver'] = None
    state['gates'][gates[0]['id']] = 'PASSED'
    assert 'gate 0: blank adjudication fields' in validate_programme(state, gates, generators)
