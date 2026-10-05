import numpy as np
import pytest

from operator_learning.representation import (
    decode_tensor, encode_tensor, q2_box_average, reconstruct_vertices,
    trilinear_voxel_averages, vertex_mass,
)


def test_asymmetric_axes_and_conservative_hat_integration():
    bounds = [(0, 2), (-1, 3), (1, 7)]
    x, y, z = np.meshgrid(np.linspace(0, 2, 3), np.linspace(-1, 3, 4),
                          np.linspace(1, 7, 5), indexing='ij')
    vertices = 10+x+2*y+3*z
    voxels = trilinear_voxel_averages(vertices, bounds, (5, 6, 7))
    assert voxels.shape == (5, 6, 7)
    assert voxels.mean()*48 == pytest.approx(vertex_mass(vertices, bounds), abs=1e-10)
    assert voxels[0, 0, 0] == pytest.approx(10+.2+2*(-1+4/12)+3*(1+6/14))


def test_reconstruction_positive_normalized_and_rejects_exits():
    bounds = [(0, 1)]*3
    p = reconstruct_vertices(np.array([[.2, .3, .4], [.8, .9, .6]]), bounds, (3, 4, 5), 3)
    assert p.min() >= 0
    assert vertex_mass(p, bounds) == pytest.approx(1)
    with pytest.raises(ValueError):
        reconstruct_vertices(np.array([[2., .3, .4]]), bounds, (3, 4, 5), 3)


def test_tensor_scaling_has_no_hidden_normalization():
    p = np.arange(24, dtype=np.float32).reshape(2, 3, 4)/100
    u = encode_tensor(p, 384000)
    assert u.shape == (1, 1, 2, 3, 4)
    assert u.dtype == np.float32
    assert np.allclose(decode_tensor(u, 384000), p, rtol=2*np.finfo(np.float32).eps)
    with pytest.raises(ValueError):
        encode_tensor(p.astype(float), 384000)


def test_q2_exact_quadrature_and_hanging_child_volume_weights():
    f = lambda x, y, z: (1+x+x*x)*(2+y*y)*(3+z+z*z)
    whole = q2_box_average(f, [0]*3, [1]*3)
    assert whole == pytest.approx((1+.5+1/3)*(2+1/3)*(3+.5+1/3))
    children = [q2_box_average(f, [i/2, j/2, k/2], [(i+1)/2, (j+1)/2, (k+1)/2])
                for i in (0, 1) for j in (0, 1) for k in (0, 1)]
    assert sum(children)/8 == pytest.approx(whole)
