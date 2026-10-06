"""Fail-closed authority checks; scientific compliance still requires review."""
from pathlib import Path
from shutil import copy2

from operator_learning.governance import validate_traceability_requirement


ROOT = Path(__file__).resolve().parents[2]


def test_requirement_and_entry_points_are_mandatory():
    assert validate_traceability_requirement(ROOT) == []


def test_missing_requirement_fails(tmp_path):
    errors = validate_traceability_requirement(tmp_path)
    assert 'missing mandatory research-traceability requirement' in errors
    assert any('authority pointer' in e for e in errors)


def test_missing_pointer_fails_even_with_policy(tmp_path):
    copy2(ROOT / 'RESEARCH_TRACEABILITY.md', tmp_path)
    (tmp_path / 'AGENTS.md').write_text('Task instructions without research authority.')
    errors = validate_traceability_requirement(tmp_path)
    assert any(e.endswith('AGENTS.md') for e in errors)
    assert 'missing mandatory research-traceability requirement' not in errors
