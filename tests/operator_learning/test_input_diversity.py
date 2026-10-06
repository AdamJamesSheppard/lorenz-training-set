import pytest

from scripts.run_input_diversity import resolution_margin, validate


def test_resolution_accounts_for_both_reconstruction_errors():
    r = resolution_margin(.2,.01,.01,1,1)
    assert r['finite_control_tv_lower'] == pytest.approx(.18-1e-10)
    assert r['resolved']
    r = resolution_margin(.01,.01,.01,1,1)
    assert r['signed_margin'] < 0
    assert r['finite_control_tv_lower'] == 0
    assert not r['resolved']


def test_nonunit_mass_is_disclosed_and_invalid_inputs_rejected():
    assert resolution_margin(.2,.01,.01,.999,1)['finite_control_tv_lower'] < .18
    with pytest.raises(ValueError):
        resolution_margin(float('nan'),.01,.01,1,1)
    with pytest.raises(ValueError,match='incomplete'):
        validate({})
