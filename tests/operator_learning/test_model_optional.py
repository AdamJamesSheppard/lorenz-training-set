"""Tiny CPU software fixture only; Torch is optional outside training runtime."""
import importlib.util
from pathlib import Path

import pytest


def test_historical_model_forward_backward():
    torch = pytest.importorskip("torch")
    path = Path(__file__).resolve().parents[2] / "scripts/train_neural_pilot.py"
    spec = importlib.util.spec_from_file_location("historical_operator_fixture", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    torch.set_num_threads(2)
    torch.manual_seed(17)
    model = module.Operator()
    density = torch.rand(1, 1, 8, 8, 8)
    result = model(density)
    assert bool(torch.isfinite(result).all()) and float(result.min().detach()) >= 0
    assert abs(float(result.mean().detach())-1) < 1e-6
    result.square().mean().backward()
    assert all(p.grad is not None and bool(torch.isfinite(p.grad).all()) for p in model.parameters())
