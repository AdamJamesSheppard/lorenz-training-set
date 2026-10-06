import numpy as np
import pytest

from operator_learning.reconstruction_controls import box_transfer, exact_box_histogram_density, restart_path


def test_box_transfer_analytic_triangle_and_mass():
    # Uniform[-1,1] convolved with uniform[-1,1]: triangular density.
    edges = np.array([-3., -2., -1., 0., 1., 2., 3.])
    density = box_transfer([-1., 1.], edges, 2)[:, 0]
    assert np.allclose(density, [0, .125, .375, .375, .125, 0], atol=1e-14)
    assert density.sum() == pytest.approx(1)


def test_exact_histogram_preserves_interior_mass_and_reports_boundary_loss():
    samples = np.array([[0., 0., 0.]])
    p, mass = exact_box_histogram_density(samples, [(-5, 5)]*3, (10,)*3, [2]*3, (20,)*3)
    assert mass == pytest.approx(1)
    assert p.min() >= 0
    _, mass = exact_box_histogram_density(np.array([[-4.9]*3]), [(-5, 5)]*3, (10,)*3, [2]*3, (20,)*3)
    assert 0 < mass < 1  # No hiding out-of-domain smoothing mass by normalization.


def test_restart_uses_identical_state_and_matching_times():
    x = np.array([1., 2., 20.])
    a = restart_path(x, .02, .001)
    b = restart_path(x, .02, .0005)
    assert a.shape == (20, 3)
    assert np.linalg.norm(a-b[1::2]) < 1e-6
    assert np.array_equal(x, [1, 2, 20])
