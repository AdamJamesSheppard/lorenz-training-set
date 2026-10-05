"""Small probability-law alignment diagnostics; no FEM or learning dependencies."""
import numpy as np
from scipy.ndimage import convolve
from scipy.special import ndtr


def normalize(p, bounds):
    p = np.asarray(p, dtype=float)
    volume = np.prod([(hi-lo)/n for (lo, hi), n in zip(bounds, p.shape)])
    if p.ndim != 3 or not np.isfinite(p).all() or p.min() < 0 or p.sum() <= 0:
        raise ValueError('Finite positive-volume 3D probability density required')
    return p / (p.sum()*volume)


def integrated_linear_basis(source_edges, target_edges):
    """Exact averages of 1D nodal hat functions on target intervals."""
    source_edges, target_edges = np.asarray(source_edges), np.asarray(target_edges)
    if np.any(np.diff(source_edges) <= 0) or np.any(np.diff(target_edges) <= 0):
        raise ValueError('Increasing edges required')
    if source_edges[0] != target_edges[0] or source_edges[-1] != target_edges[-1]:
        raise ValueError('Same physical interval required')
    matrix = np.zeros((len(target_edges)-1, len(source_edges)))
    for row, (a, b) in enumerate(zip(target_edges[:-1], target_edges[1:])):
        for col, (s, t) in enumerate(zip(source_edges[:-1], source_edges[1:])):
            left, right = max(a, s), min(b, t)
            if right > left:
                hat_right = ((right-s)**2-(left-s)**2)/(2*(t-s))
                matrix[row, col] += (right-left-hat_right)/(b-a)
                matrix[row, col+1] += hat_right/(b-a)
    return matrix


def reconstruct(samples, bounds, histogram_shape, target_shape, filter_width):
    """Historical compact histogram/trilinear recipe, exact conservative export."""
    samples = np.asarray(samples)
    histogram, edges = np.histogramdd(samples, bins=histogram_shape, range=bounds)
    if histogram.sum() != len(samples):
        raise ValueError('Out-of-box samples: no clipping or silent renormalization')
    kernel = np.ones((filter_width,)*3) / filter_width**3
    smooth = convolve(histogram, kernel, mode='constant')
    padded = np.pad(smooth, 1, mode='edge')
    vertices = sum(padded[i:i+histogram_shape[0]+1,
                          j:j+histogram_shape[1]+1,
                          k:k+histogram_shape[2]+1]
                   for i in (0, 1) for j in (0, 1) for k in (0, 1))/8
    matrices = [integrated_linear_basis(e, np.linspace(lo, hi, n+1))
                for e, (lo, hi), n in zip(edges, bounds, target_shape)]
    p = np.einsum('ai,bj,ck,ijk->abc', *matrices, vertices, optimize=True)
    return normalize(p, bounds)


def draw_density(p, bounds, count, rng):
    p = normalize(p, bounds)
    indices = np.unravel_index(rng.choice(p.size, size=count, p=p.ravel()/p.sum()), p.shape)
    return np.column_stack([lo+(indices[d]+rng.random(count))*(hi-lo)/p.shape[d]
                            for d, (lo, hi) in enumerate(bounds)])


def drift(x):
    return np.column_stack((10*(x[:, 1]-x[:, 0]),
                            x[:, 0]*(28-x[:, 2])-x[:, 1],
                            x[:, 0]*x[:, 1]-(8/3)*x[:, 2]))


def evolve_sde(initial, D, dt, steps, rng, bounds):
    """Euler--Maruyama whole-space SDE. Reject exits; no reflecting approximation."""
    x = np.array(initial, dtype=float, copy=True)
    B = np.sqrt(2)*np.linalg.cholesky(np.asarray(D, dtype=float))
    lower, upper = np.asarray(bounds)[:, 0], np.asarray(bounds)[:, 1]
    exits = 0
    for _ in range(steps):
        x += dt*drift(x) + np.sqrt(dt)*(rng.standard_normal(x.shape)@B.T)
        outside = np.any((x < lower) | (x > upper), axis=1)
        exits += int(outside.sum())
        if not np.isfinite(x).all() or outside.any():
            raise ValueError('SDE left diagnostic box; boundary modelling requires a new study')
    return x, exits


def condition_density(prior, bounds, dimensions, observation, variance):
    """Exact voxel integrals of piecewise-constant prior × independent likelihood.

    Gaussian observation noise; state density is never fitted to a Gaussian.
    """
    if variance <= 0 or len(set(dimensions)) != len(dimensions):
        raise ValueError('Positive variance and distinct coordinate observations required')
    prior = normalize(prior, bounds)
    weights = np.ones(prior.shape)
    for dim, value in zip(dimensions, observation):
        lo, hi = bounds[dim]
        edges = np.linspace(lo, hi, prior.shape[dim]+1)
        cdf = ndtr((edges-value)/np.sqrt(variance))
        averages = np.maximum(np.diff(cdf), 0)/np.diff(edges)
        reshape = [1, 1, 1]
        reshape[dim] = len(averages)
        weights *= averages.reshape(reshape)
    dv = np.prod([(hi-lo)/n for (lo, hi), n in zip(bounds, prior.shape)])
    evidence = float((prior*weights).sum()*dv)
    if not np.isfinite(evidence) or evidence <= 0:
        raise ValueError('Observation evidence vanished')
    return normalize(prior*weights, bounds), evidence


def block_resample(samples, block_length, rng):
    """Circular moving-block resample; diagnostic length, not an independence proof."""
    n = len(samples)
    starts = rng.integers(n, size=int(np.ceil(n/block_length)))
    indices = (starts[:, None] + np.arange(block_length)) % n
    return np.asarray(samples)[indices.ravel()[:n]]


def density_summary(p, bounds, boundary_layers, transition_width, tail_z):
    p = normalize(p, bounds)
    dv = np.prod([(hi-lo)/n for (lo, hi), n in zip(bounds, p.shape)])
    probability = p*dv
    coordinates = np.meshgrid(*[np.linspace(lo+(hi-lo)/(2*n), hi-(hi-lo)/(2*n), n)
                               for (lo, hi), n in zip(bounds, p.shape)], indexing='ij')
    mean = np.array([(probability*x).sum() for x in coordinates])
    covariance = np.array([[(probability*(x-mean[i])*(y-mean[j])).sum()
                           for j, y in enumerate(coordinates)] for i, x in enumerate(coordinates)])
    n = boundary_layers
    return dict(mass=float(p.sum()*dv), negative_mass=float(-p[p < 0].sum()*dv),
                positive_x_probability=float(probability[coordinates[0] > 0].sum()),
                transition_probability=float(probability[np.abs(coordinates[0]) < transition_width].sum()),
                tail_probability=float(probability[(coordinates[2] < tail_z[0]) |
                                                    (coordinates[2] > tail_z[1])].sum()),
                boundary_probability=float(1-probability[n:-n, n:-n, n:-n].sum()),
                effective_volume=float(1/(p*p).sum()/dv),
                mean=mean.tolist(), covariance=covariance.tolist())


def distance(a, b, bounds):
    a, b = normalize(a, bounds), normalize(b, bounds)
    dv = np.prod([(hi-lo)/n for (lo, hi), n in zip(bounds, a.shape)])
    marginals = []
    for dim in range(3):
        axes = tuple(d for d in range(3) if d != dim)
        marginals.append(float(.5*np.abs((a-b).sum(axis=axes)).sum()*dv))
    return dict(l1=float(np.abs(a-b).sum()*dv), marginal_tv=marginals)
