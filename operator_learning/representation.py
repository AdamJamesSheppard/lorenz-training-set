"""Explicit archived occupation-density representation contract; no FEM execution."""
import numpy as np
from scipy.ndimage import convolve

from operator_learning.alignment import integrated_linear_basis


def vertex_mass(vertices, bounds):
    vertices = np.asarray(vertices, dtype=np.float64)
    if vertices.ndim != 3 or min(vertices.shape) < 2 or not np.isfinite(vertices).all():
        raise ValueError('Finite three-dimensional nodal field required')
    weights = [np.ones(n) for n in vertices.shape]
    for weight in weights:
        weight[[0, -1]] = .5
    cell_volume = np.prod([(hi-lo)/(n-1) for (lo, hi), n in zip(bounds, vertices.shape)])
    return float(np.einsum('ijk,i,j,k', vertices, *weights)*cell_volume)


def reconstruct_vertices(samples, bounds, histogram_shape, filter_width):
    samples = np.asarray(samples)
    if samples.ndim != 2 or samples.shape[1] != 3 or not np.isfinite(samples).all():
        raise ValueError('Finite xyz samples required')
    histogram, _ = np.histogramdd(samples, bins=histogram_shape, range=bounds)
    if histogram.sum() != len(samples):
        raise ValueError('Out-of-domain samples; no clipping')
    kernel = np.ones((filter_width,)*3, dtype=np.float64)/filter_width**3
    padded = np.pad(convolve(histogram, kernel, mode='constant'), 1, mode='edge')
    vertices = sum(padded[i:i+histogram_shape[0]+1, j:j+histogram_shape[1]+1,
                          k:k+histogram_shape[2]+1]
                   for i in (0, 1) for j in (0, 1) for k in (0, 1))/8
    mass = vertex_mass(vertices, bounds)
    if mass <= 0 or vertices.min() < 0:
        raise ValueError('Positive mass and nonnegative density required')
    return vertices/mass


def trilinear_voxel_averages(vertices, bounds, shape):
    matrices = [integrated_linear_basis(np.linspace(lo, hi, n), np.linspace(lo, hi, m+1))
                for (lo, hi), n, m in zip(bounds, vertices.shape, shape)]
    return np.einsum('ai,bj,ck,ijk->abc', *matrices, vertices, optimize=True)


def encode_tensor(density, volume):
    density = np.asarray(density)
    if density.ndim != 3 or density.dtype != np.float32 or volume <= 0:
        raise ValueError('float32 xyz density and positive volume required')
    if not np.isfinite(density).all() or density.min() < 0:
        raise ValueError('Finite nonnegative input required')
    return (density*np.float32(volume))[None, None]


def decode_tensor(tensor, volume):
    if tensor.ndim != 5 or tensor.shape[:2] != (1, 1) or volume <= 0:
        raise ValueError('One batch, one density channel and positive volume required')
    return tensor[0, 0].astype(np.float64)/volume


def q2_box_average(function, lower, upper):
    """Tensor three-point Gauss cell average, exact for coordinatewise Q2."""
    nodes, weights = np.polynomial.legendre.leggauss(3)
    axes = [lo+(nodes+1)*(hi-lo)/2 for lo, hi in zip(lower, upper)]
    values = function(*np.meshgrid(*axes, indexing='ij'))
    return float(np.einsum('ijk,i,j,k', values, weights, weights, weights)/8)
