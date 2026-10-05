"""Legacy config changes cannot silently dispatch different-looking physics."""
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]


def legacy():
    path = ROOT / 'mfem/run_neural_pilot.py'
    sys.path.insert(0, str(path.parent))
    try:
        spec = importlib.util.spec_from_file_location('legacy_contract_fixture', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


@pytest.mark.parametrize('field,value', [('horizon', .1), ('steps', 640),
    ('trajectories', 7), ('D', [[1,0,0],[0,1,0],[0,0,1]]),
    ('export_grid', [30,36,36]), ('resume_available_GiB', 4)])
def test_unsupported_legacy_config_rejected(field, value):
    pytest.importorskip('scipy')
    module = legacy()
    config = json.loads((ROOT / 'experiments/neural-pilot.json').read_text())
    module.validate_historical_config(config)
    config[field] = value
    with pytest.raises(ValueError):
        module.validate_historical_config(config)


def test_historical_relaunch_blocked_by_default(monkeypatch):
    pytest.importorskip('scipy')
    monkeypatch.delenv('LORENZ_ALLOW_HISTORICAL_PILOT', raising=False)
    with pytest.raises(RuntimeError, match='opt-in'):
        legacy().main()
