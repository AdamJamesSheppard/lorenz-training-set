"""Fast predeclaration tests; no scientific trajectory run in CI."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_refinement_is_bounded_characterization():
    spec = importlib.util.spec_from_file_location('refinement', ROOT/'scripts/run_reconstruction_refinement.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    config = json.loads((ROOT/'experiments/operator_learning/OL-G02_reconstruction_refinement_v2.json').read_text())
    module.validate_design(config)
    assert config['thresholds']['negative_mass_max'] == 0
    assert len(config['seeds']['trajectory'])*len(config['comparison_shapes'])*8 == 96
    config['scientific_adjudication'] = 'PASSED'
    with pytest.raises(AssertionError):
        module.validate_design(config)
