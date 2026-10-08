import numpy as np
import pytest
from scripts.run_window_local_control import window_start
from operator_learning.reconstruction_controls import restart_path


def test_saved_boundary_uses_previous_endpoint_not_first_sample():
    initial=np.array([1.,2.,3.])
    fine=np.arange(36).reshape(12,3)
    assert np.array_equal(window_start(initial,fine,0,4),initial)
    assert np.array_equal(window_start(initial,fine,1,4),fine[3])
    assert np.array_equal(window_start(initial,fine,2,4),fine[7])
    with pytest.raises(ValueError):
        window_start(initial,fine,3,4)


def test_restart_preserves_exact_saved_fine_window():
    initial=np.array([1.,2.,20.])
    fine=restart_path(initial,.03,.001)
    start=window_start(initial,fine,1,10)
    assert np.array_equal(restart_path(start,.01,.001),fine[10:20])
