"""Portable G03 evidence and canonical adjudication; no scientific simulation."""
import hashlib
import json
from pathlib import Path

from operator_learning.diversity_qualification import evaluate

ROOT = Path(__file__).resolve().parents[2]
PREFIX = ROOT/'docs/operator_learning/evidence/G03_QUALIFICATION_V4_20261009'


def load(suffix):
    return json.loads(Path(str(PREFIX)+suffix).read_text())


def test_portable_evidence_matches_original_seal():
    seal=load('_seal.json')
    for suffix, name in [('_report.json','report.json'),('_config.json','config.json'),
                         ('_provenance.json','provenance.json')]:
        assert hashlib.sha256(Path(str(PREFIX)+suffix).read_bytes()).hexdigest()==seal[name]


def test_frozen_g03_criteria_and_scope():
    report=load('_report.json'); config=load('_config.json')
    ids=[f'seed{s}_window{w}' for s in config['seeds']['trajectory'] for w in range(2)]
    actual=evaluate(report['laws'],report['pairs'],ids,**config['thresholds'])
    assert json.loads(json.dumps(actual))==report['evaluation']
    assert actual['review_status']=='ELIGIBLE_FOR_SCOPED_REVIEW'
    assert len(report['within'])==144 and len(report['pairs'])==276
    assert report['exclusions']==[] and actual['failures']==[]
    # Producer reports are preserved; only the separate adjudication promotes.
    assert report['gate_status']=='OPEN'
    state=json.loads((ROOT/'docs/operator_learning/state.json').read_text())
    assert state['gates']['OL-G03_INPUT_DIVERSITY']=='PASSED'
    assert state['next_required_gate']=='OL-G04_REFERENCE_TARGET_APPLICABILITY'
    assert state['current_model_scientifically_qualified'] is False
    assert state['operator_production_authorized'] is False


def test_baseline_and_original_failures_preserved():
    before=json.loads((ROOT/'docs/operator_learning/evidence/G03_RESEARCH_UPDATES_BEFORE_OL_D032.json').read_text())
    g=next(x for x in before['updates'] if x['gate_id']=='OL-G03_INPUT_DIVERSITY')
    assert g['status']=='OPEN'
    assert any(x['status']=='FAILED_SUFFICIENT_BOUND' and x['cases']==12
               for x in g['component_outcomes'])
