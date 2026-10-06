"""Bounded occupation-density stability tools; no FEM, training or state closure."""
import numpy as np
from scipy.ndimage import convolve1d

from operator_learning.representation import trilinear_voxel_averages, vertex_mass


def lorenz_drift(x):
    return np.array([10*(x[1]-x[0]), x[0]*(28-x[2])-x[1],
                     x[0]*x[1]-(8/3)*x[2]])


def rk4_step(x, dt):
    a = lorenz_drift(x)
    b = lorenz_drift(x+.5*dt*a)
    c = lorenz_drift(x+.5*dt*b)
    d = lorenz_drift(x+dt*c)
    return x+dt*(a+2*b+2*c+d)/6


def dense_occupation(seed, spinup, window, dt):
    """Same historical scalar RK4 arithmetic; save every step in the SAME window."""
    if dt <= 0 or spinup < 0 or window <= 0:
        raise ValueError('Positive step/window and nonnegative spinup required')
    counts = [round(spinup/dt), round(window/dt)]
    if any(not np.isclose(n*dt, length, rtol=0, atol=1e-12)
           for n, length in zip(counts, [spinup, window])):
        raise ValueError('Window endpoints must align with time steps')
    x = np.random.default_rng(seed).uniform([-10, -10, 10], [10, 10, 30])
    initial = x.copy()
    for _ in range(counts[0]):
        x = rk4_step(x, dt)
    cloud = np.empty((counts[1], 3))
    for index in range(counts[1]):
        x = rk4_step(x, dt)
        cloud[index] = x
    return initial, cloud


def box_weights(cell_width, physical_width):
    """Exact overlap weights of a centred physical top-hat with histogram bins."""
    if not np.isfinite([cell_width, physical_width]).all() or min(cell_width, physical_width) <= 0:
        raise ValueError('Finite positive widths required')
    radius = int(np.ceil(physical_width/(2*cell_width)+.5))
    centres = np.arange(-radius, radius+1)*cell_width
    overlaps = np.maximum(0, np.minimum(centres+cell_width/2, physical_width/2)
                          - np.maximum(centres-cell_width/2, -physical_width/2))
    weights = overlaps/physical_width
    return weights/weights.sum()


def physical_bandwidth_density(samples, bounds, histogram_shape, physical_widths, shape):
    """Keep physical smoothing width fixed while varying histogram resolution.

    Zero exterior convolution, edge-padded vertex lifting and exact trilinear
    integrals. Vertex lifting still depends on the grid; it is measured explicitly.
    """
    samples = np.asarray(samples)
    if samples.ndim != 2 or samples.shape[1] != 3 or not np.isfinite(samples).all():
        raise ValueError('Finite xyz cloud required')
    if len(bounds) != 3 or len(histogram_shape) != 3 or len(physical_widths) != 3:
        raise ValueError('Three-dimensional contract required')
    smooth, _ = np.histogramdd(samples, bins=histogram_shape, range=bounds)
    if smooth.sum() != len(samples) or not len(samples):
        raise ValueError('Nonempty cloud inside box required; no clipping')
    for axis, ((lo, hi), n, width) in enumerate(zip(bounds, histogram_shape, physical_widths)):
        smooth = convolve1d(smooth, box_weights((hi-lo)/n, width), axis=axis, mode='constant')
    padded = np.pad(smooth, 1, mode='edge')
    vertices = sum(padded[i:i+histogram_shape[0]+1, j:j+histogram_shape[1]+1,
                          k:k+histogram_shape[2]+1]
                   for i in (0, 1) for j in (0, 1) for k in (0, 1))/8
    mass = vertex_mass(vertices, bounds)
    if mass <= 0 or vertices.min() < 0:
        raise ValueError('Nonnegative positive-mass reconstruction required')
    return trilinear_voxel_averages(vertices/mass, bounds, shape)


def dependence_diagnostic(values, max_lag, dt):
    """Biased ACF and first-nonpositive truncation; heuristic ESS, no mixing proof."""
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or not np.isfinite(values).all() or len(values) < 3:
        raise ValueError('Finite scalar sequence of length >=3 required')
    if max_lag < 1 or max_lag >= len(values) or dt <= 0:
        raise ValueError('Positive lag below sequence length and positive dt required')
    centred = values-values.mean()
    variance_sum = float(centred@centred)
    if variance_sum == 0:
        return dict(status='CONSTANT_OBSERVABLE_ESS_UNDEFINED', acf=None,
                    tau_steps=None, ess=None, truncation_lag=None, censored=None)
    acf = [1.0]+[float(centred[:-lag]@centred[lag:]/variance_sum)
                 for lag in range(1, max_lag+1)]
    stop = next((lag for lag in range(1, len(acf)) if acf[lag] <= 0), len(acf))
    tau = max(1., 1+2*sum(acf[1:stop]))
    return dict(status='HEURISTIC', acf=acf, tau_steps=tau, tau_time=tau*dt,
                ess=len(values)/tau, truncation_lag=stop,
                censored=stop == len(acf), warning='Observable-specific finite-window diagnostic; no stationarity or independence proof')


def histogram_physical_widths(bounds, shape, filter_width):
    return [filter_width*(hi-lo)/n for (lo, hi), n in zip(bounds, shape)]
