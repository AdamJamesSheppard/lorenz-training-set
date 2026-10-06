import numpy as np
import pytest

from operator_learning.reconstruction import (
    box_weights, dense_occupation, dependence_diagnostic,
    histogram_physical_widths, physical_bandwidth_density,
)
from operator_learning.representation import reconstruct_vertices, trilinear_voxel_averages


def test_top_hat_overlap_at_aligned_and_unaligned_widths():
    for width in [1., 2., 3., 4., 4.5]:
        w = box_weights(1., width)
        assert w.min() >= 0
        assert w.sum() == pytest.approx(1)
        assert np.array_equal(w, w[::-1])
    assert np.allclose(box_weights(1., 3.)[1:-1], [1/3]*3)
    assert np.allclose(box_weights(1., 2.)[1:-1], [.25, .5, .25])
    with pytest.raises(ValueError):
        box_weights(0, 3)


def test_physical_bandwidth_reproduces_original_recipe_to_roundoff():
    bounds = [(0, 2), (-1, 3), (1, 7)]
    h = (3, 4, 5)
    samples = np.array([[.2, .3, 1.4], [1.8, 2.9, 6.6]])
    vertices = reconstruct_vertices(samples, bounds, h, 3)
    expected = trilinear_voxel_averages(vertices, bounds, (5, 6, 7))
    actual = physical_bandwidth_density(samples, bounds, h,
                                        histogram_physical_widths(bounds, h, 3), (5, 6, 7))
    assert np.allclose(actual, expected, rtol=2e-14, atol=1e-15)
    assert actual.sum()*48/actual.size == pytest.approx(1)


def test_lorenz_sampling_reproducible_and_finite_window_count():
    first, cloud = dense_occupation(17, .01, .04, .001)
    second, repeat = dense_occupation(17, .01, .04, .001)
    assert np.array_equal(first, second)
    assert np.array_equal(cloud, repeat)
    assert cloud.shape == (40, 3)
    assert cloud[9::10].shape == (4, 3)
    with pytest.raises(ValueError):
        dense_occupation(17, .01, .0405, .001)


def test_acf_constant_has_no_invented_ess_and_slow_signal_correlated():
    assert dependence_diagnostic(np.ones(100), 20, .01)['ess'] is None
    x = np.sin(np.linspace(0, 4, 100))
    result = dependence_diagnostic(x, 20, .01)
    assert result['ess'] < 10
    assert result['acf'][1] > .9
    assert result['status'] == 'HEURISTIC'


def test_reconstruction_rejects_exits_without_clipping():
    with pytest.raises(ValueError):
        physical_bandwidth_density(np.array([[2., .3, .4]]), [(0, 1)]*3,
                                   (3, 4, 5), [1]*3, (5, 6, 7))
