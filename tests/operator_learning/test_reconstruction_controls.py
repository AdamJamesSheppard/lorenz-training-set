import numpy as np
import pytest

from operator_learning.reconstruction_controls import (
    box_transfer, exact_box_histogram_density, restart_path, empirical_box_density,
)


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


def test_empirical_box_analytic_uniform_cube_and_boundary_loss():
    density, mass = empirical_box_density([[0, 0, 0]], [(-2, 2)]*3, [2]*3, [4]*3)
    expected = np.zeros((4,)*3)
    expected[1:3, 1:3, 1:3] = 1/8
    assert np.array_equal(density, expected)
    assert mass == pytest.approx(1)
    _, mass = empirical_box_density([[-2]*3], [(-2, 2)]*3, [2]*3, [4]*3)
    assert mass == pytest.approx(1/8)  # Raw boundary loss never renormalized away.


def test_empirical_box_linear_mixture_and_exact_conservative_coarsening():
    bounds = [(-2, 2)]*3
    cloud = np.array([[.1, .2, .3], [.3, -.2, .1]])
    p, _ = empirical_box_density(cloud, bounds, [1]*3, [8]*3)
    a, _ = empirical_box_density(cloud[:1], bounds, [1]*3, [8]*3)
    b, _ = empirical_box_density(cloud[1:], bounds, [1]*3, [8]*3)
    assert np.allclose(p, (a+b)/2)
    coarse, _ = empirical_box_density(cloud, bounds, [1]*3, [4]*3)
    assert np.allclose(p.reshape(4, 2, 4, 2, 4, 2).mean(axis=(1, 3, 5)), coarse)
