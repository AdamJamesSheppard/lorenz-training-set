"""Fast design/ledger controls, not execution of scientific characterization."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_empirical_control_remains_characterization_with_120_comparisons():
    spec = importlib.util.spec_from_file_location('empirical_runner', ROOT/'scripts/run_reconstruction_empirical.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    config = json.loads((ROOT/'experiments/operator_learning/OL-G02_reconstruction_empirical_v4.json').read_text())
    module.validate_design(config)
    source = (ROOT/'scripts/run_reconstruction_empirical.py').read_text()
    assert 'len(records) != 120' in source
    assert 'expected_comparisons=120' in source
    assert '132' not in source
    config['scientific_adjudication'] = 'PASSED'
    with pytest.raises(ValueError):
        module.validate_design(config)
