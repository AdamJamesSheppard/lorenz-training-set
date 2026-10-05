import copy
import json
from pathlib import Path

import pytest

from operator_learning.governance import (
    check_repository, validate_predeclaration, validate_programme, validate_provenance,
)

ROOT = Path(__file__).resolve().parents[2]


def programme():
    base = ROOT / "docs/operator_learning"
    return tuple(json.loads((base / name).read_text())
                 for name in ("state.json", "gates.json", "generators.json"))


def test_canonical_repository():
    assert check_repository(ROOT) == []


def test_wrong_next_gate_rejected():
    state, gates, generators = programme()
    state['next_required_gate'] = gates[1]['id']
    assert 'NEXT_REQUIRED_GATE inconsistent' in validate_programme(state, gates, generators)


def test_locked_gate_cannot_be_opened_before_alignment():
    state, gates, generators = programme()
    gates[1]["decision_status"] = "OPEN"
    state["gates"][gates[1]["id"]] = "OPEN"
    assert "gate 1: prerequisite not passed" in validate_programme(state, gates, generators)


@pytest.mark.parametrize("field", ["operator_surrogate_authorized_for_da",
                                    "operator_production_authorized",
                                    "current_model_scientifically_qualified"])
def test_no_premature_authorization(field):
    state, gates, generators = programme()
    state[field] = True
    assert "authorization before qualification gates" in validate_programme(state, gates, generators)


def test_pass_requires_adjudication_and_thresholds():
    state, gates, generators = programme()
    # Explicit invalid fixture, independent of whether current G00 is predeclared.
    gates[0]['predeclared_thresholds'] = 'TO_BE_PREDECLARED_BEFORE_RUN'
    gates[0]["decision_status"] = "PASSED"
    state["gates"][gates[0]["id"]] = "PASSED"
    errors = validate_programme(state, gates, generators)
    assert "gate 0: passed without signed adjudication" in errors
    assert "gate 0: passed with undeclared thresholds" in errors


def test_unverified_generator_has_no_training_permission():
    state, gates, generators = programme()
    generators[0]["allowed_for_training"] = True
    assert validate_programme(state, gates, generators)


def test_draft_config_cannot_prepare():
    draft = json.loads((ROOT / "experiments/operator_learning/OL-G00_alignment_v1.json").read_text())
    with pytest.raises(ValueError):
        validate_predeclaration(draft)


def test_provenance_rejects_missing_or_invalid_hashes():
    with pytest.raises(ValueError):
        validate_provenance({})
    record = dict(experiment_id="fixture", gate_id="fixture", kind="software_fixture",
                  config_sha256="a"*64, git_commit="b"*40, git_dirty=False, git_status="",
                  command=["fixture"], runtime_versions={}, hardware={}, seeds=[],
                  input_hashes={}, output_hashes={"fixture": "c"*64}, checkpoint_hashes={},
                  diagnostics={}, status="COMPLETED")
    validate_provenance(record)
    bad = copy.deepcopy(record)
    bad["output_hashes"]["fixture"] = "broken"
    with pytest.raises(ValueError):
        validate_provenance(bad)
    record["output_hashes"] = {}
    with pytest.raises(ValueError):
        validate_provenance(record)
