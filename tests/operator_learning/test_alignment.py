import numpy as np
import pytest

from operator_learning.alignment import (
    block_resample, condition_density, draw_density, evolve_sde,
    integrated_linear_basis, normalize, reconstruct,
)


def test_exact_affine_voxel_averages_and_partition_of_unity():
    source = np.linspace(-2, 3, 8)
    target = np.linspace(-2, 3, 10)
    matrix = integrated_linear_basis(source, target)
    np.testing.assert_allclose(matrix.sum(axis=1), 1, atol=1e-14)
    np.testing.assert_allclose(matrix@source, (target[1:]+target[:-1])/2, atol=1e-14)


def test_conditioning_keeps_full_non_gaussian_density_and_mass():
    box = [(-4,4)]*3
    p = np.zeros((8,8,8))
    p[1:3, 2:4, 3:5] = 1
    p[5:7, 2:4, 3:5] = 1
    p = normalize(p, box)
    q, evidence = condition_density(p, box, [0], [-2.], 1.)
    assert evidence > 0 and abs(q.sum()-1) < 1e-12
    assert q[:4].sum() > p[:4].sum()
    assert np.all(q[p == 0] == 0)


def test_sampling_and_sde_reproducibility_and_zero_drift_noise_covariance():
    box = [(-100,100)]*3
    p = np.ones((4,4,4))
    a = draw_density(p, box, 20, np.random.default_rng(7))
    b = draw_density(p, box, 20, np.random.default_rng(7))
    np.testing.assert_array_equal(a, b)
    D = np.array([[1,.4,.2],[.4,1,.3],[.2,.3,1]])
    dt = .001
    x, exits = evolve_sde(np.zeros((100000,3)), D, dt, 1, np.random.default_rng(11), box)
    assert exits == 0
    np.testing.assert_allclose(np.cov(x.T)/(2*dt), D, atol=.015)


def test_compact_reconstruction_normalizes_and_rejects_box_exits():
    box = [(-4,4)]*3
    cloud = np.random.default_rng(8).uniform(-2,2,(200,3))
    p = reconstruct(cloud, box, [5,5,5], [8,8,8], 3)
    assert p.min() >= 0 and abs(p.sum()-1) < 1e-12
    with pytest.raises(ValueError):
        reconstruct(np.array([[20,0,0]]), box, [5,5,5], [8,8,8], 3)
    np.testing.assert_array_equal(block_resample(cloud, 10, np.random.default_rng(4)),
                                  block_resample(cloud, 10, np.random.default_rng(4)))
