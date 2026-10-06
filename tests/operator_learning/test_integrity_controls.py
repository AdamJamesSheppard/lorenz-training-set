"""Policy visibility and complete gate coverage; no semantic-honesty guarantee."""
import json
from pathlib import Path

from operator_learning.governance import validate_integrity_documents

ROOT = Path(__file__).resolve().parents[2]


def test_all_current_gates_have_integrity_boundaries():
    gates = json.loads((ROOT/'docs/operator_learning/gates.json').read_text())
    assert len(gates) == 18
    assert validate_integrity_documents(ROOT, gates) == []


def test_missing_policy_and_links_fail_closed(tmp_path):
    errors = validate_integrity_documents(tmp_path, [])
    assert 'missing cross-stage scientific-integrity policy' in errors
    assert 'missing gate integrity audit' in errors
    assert any('AGENTS.md' in error for error in errors)


def test_gate_coverage_and_boundaries_are_checked(tmp_path):
    # Explicit software fixture; temporary files are not project scientific evidence.
    from shutil import copytree, copy2
    copytree(ROOT/'docs', tmp_path/'docs', ignore=lambda path, names: [n for n in names if n not in {
        'operator_learning', 'MATH_PROTOCOL.md', 'README.md', 'GOVERNANCE.md',
        'INTEGRITY_GATE_AUDIT_20261006.md'}])
    for name in ('AGENTS.md', 'README.md', 'SCIENTIFIC_INTEGRITY.md'):
        copy2(ROOT/name, tmp_path/name)
    gates = [{'id': 'OL-G99_FIXTURE'}]
    errors = validate_integrity_documents(tmp_path, gates)
    assert 'gate integrity audit missing: OL-G99_FIXTURE' in errors
