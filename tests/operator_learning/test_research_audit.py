"""Research traceability controls do not constitute scientific qualification."""
import json
from pathlib import Path

from scripts.audit_research_sources import validate, urls


ROOT = Path(__file__).resolve().parents[2]


def test_method_gate_and_source_links_resolve():
    assert validate(ROOT) == []


def test_failures_and_open_characterizations_are_preserved():
    audit = json.loads((ROOT / 'docs/research_audit/snapshot_20261006.json').read_text())
    assert len(audit['gates']) == 18
    g01 = audit['gates'][1]
    assert any(e['outcome'].startswith('FAILED_V1') for e in g01['historical_events'])
    assert any(e['outcome'].startswith('PASSED_V2') for e in g01['historical_events'])
    assert audit['gates'][2]['status'] == 'OPEN'
    assert all(g['status'] == 'LOCKED' for g in audit['gates'][3:])
    paper = next(r for r in audit['references'] if r['id'] == 'OL-FNO-PAPER')
    assert paper['provenance'].startswith('retrospective_addition')
    assert audit['history_url_changes']
    assert any(x['change'] == '-' for x in audit['history_url_changes'])
    assert len(audit['historical_decision_sections']) > 50
    assert any('OL-D005:' in s['heading'] for s in audit['historical_decision_sections'])


def test_urls_preserve_balanced_doi_parentheses():
    assert urls('[source](https://doi.org/10.x/a(1963)b).') == ['https://doi.org/10.x/a(1963)b']
