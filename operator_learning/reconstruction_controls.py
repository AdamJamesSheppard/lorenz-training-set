"""Non-Gaussian diagnostic controls, never an implicit production-law replacement."""
import numpy as np

from operator_learning.reconstruction import rk4_step


def paired_box_l1_bound(samples_a, samples_b, widths):
    """Whole-space L1 upper bound for equally weighted, paired box mixtures.

    Each pair's exact kernel L1 is twice one minus its relative overlap.
    The triangle inequality bounds the mixture difference by their mean.
    No grid, normalization or empirical independence assumption is involved.
    Pairing must be supplied explicitly (e.g. matching physical sample times).
    This is an upper bound, not an estimator of the actual mixture difference.
    """
    a, b, w = (np.asarray(x, dtype=float) for x in (samples_a, samples_b, widths))
    if a.ndim != 2 or a.shape[1] != 3 or not len(a) or b.shape != a.shape:
        raise ValueError('Equal nonempty paired xyz clouds required')
    if w.shape != (3,) or not np.isfinite(w).all() or np.any(w <= 0):
        raise ValueError('Finite positive xyz box widths required')
    if not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('Finite paired points required')
    overlap = np.prod(np.maximum(0, 1-np.abs(a-b)/w), axis=1)
    return float(np.mean(2*(1-overlap)))


def restart_path(initial, window, dt):
    if dt <= 0 or window <= 0 or not np.isclose(round(window/dt)*dt, window, atol=1e-12, rtol=0):
        raise ValueError('Positive aligned window and timestep required')
    state = np.asarray(initial, dtype=float).copy()
    if state.shape != (3,) or not np.isfinite(state).all():
        raise ValueError('Finite common xyz initial state required')
    path = np.empty((round(window/dt), 3))
    for i in range(len(path)):
        state = rk4_step(state, dt)
        path[i] = state
    return path


def box_transfer(source_edges, target_edges, width):
    """Exact voxel-average density of a uniform source cell convolved with a box.

    Columns represent unit source-cell probability, not density values. Integrate
    (1/width) 1{|x-y|<=width/2} over the source/target rectangles using the
    second primitive H(z)=max(z,0)^2/2; divide by both interval lengths.
    """
    s, t = np.asarray(source_edges)[:-1][None, :], np.asarray(source_edges)[1:][None, :]
    a, b = np.asarray(target_edges)[:-1][:, None], np.asarray(target_edges)[1:][:, None]
    if width <= 0 or np.any(t <= s) or np.any(b <= a):
        raise ValueError('Positive widths and ordered edges required')

    def rectangle(shift):
        h = lambda x: .5*np.maximum(x, 0)**2
        return h(b-s+shift)-h(a-s+shift)-h(b-t+shift)+h(a-t+shift)

    result = (rectangle(width/2)-rectangle(-width/2))/(width*(t-s)*(b-a))
    if result.min() < -1e-10:
        raise ValueError('Unexpected analytic cancellation error')
    # Roundoff-only floor, bounded above and recorded as such in study protocol.
    return np.maximum(result, 0)


def exact_box_histogram_density(samples, bounds, histogram_shape, widths, shape):
    """Exact continuous histogram→top-hat→voxel control, without vertex lifting.

    This differs from the historical law recipe. It is a labelled diagnostic;
    raw mass is returned, and no silent boundary renormalization is performed.
    """
    cloud = np.asarray(samples)
    if cloud.ndim != 2 or cloud.shape[1] != 3 or not len(cloud) or not np.isfinite(cloud).all():
        raise ValueError('Finite nonempty xyz samples required')
    hist, edges = np.histogramdd(cloud, bins=histogram_shape, range=bounds)
    if hist.sum() != len(cloud):
        raise ValueError('No clipping of out-of-box samples')
    matrices = [box_transfer(e, np.linspace(lo, hi, n+1), w)
                for e, (lo, hi), n, w in zip(edges, bounds, shape, widths)]
    density = np.einsum('ai,bj,ck,ijk->abc', *matrices, hist/len(cloud), optimize=True)
    dv = np.prod([(hi-lo)/n for (lo, hi), n in zip(bounds, shape)])
    return density, float(density.sum()*dv)


def empirical_box_density(samples, bounds, widths, shape):
    """Exact voxel integrals of the empirical measure convolved with a box.

    Sum individual box/voxel overlap volumes. No histogram, state refit,
    normalization or support masking. Kernel mass outside the box is reported.
    This is a finite-sample regularized-law control, not continuum truth.
    """
    cloud = np.asarray(samples, dtype=float)
    bounds, widths, shape = np.asarray(bounds), np.asarray(widths), np.asarray(shape)
    if cloud.ndim != 2 or cloud.shape[1] != 3 or not len(cloud) or not np.isfinite(cloud).all():
        raise ValueError('Finite nonempty xyz samples required')
    if bounds.shape != (3, 2) or widths.shape != (3,) or shape.shape != (3,):
        raise ValueError('Three-dimensional contract required')
    if np.any(widths <= 0) or np.any(shape <= 0) or np.any(shape != shape.astype(int)):
        raise ValueError('Positive kernel widths and integer grid shape required')
    lower, upper = bounds[:, 0], bounds[:, 1]
    if np.any(upper <= lower) or np.any(cloud < lower) or np.any(cloud > upper):
        raise ValueError('Ordered box and in-box samples required; no clipping')
    shape = shape.astype(int)
    spacing = (upper-lower)/shape
    probability = np.zeros(tuple(shape), dtype=float)
    scale = 1/(len(cloud)*np.prod(widths))
    for point in cloud:
        left, right = point-widths/2, point+widths/2
        starts = np.maximum(0, np.floor((left-lower)/spacing).astype(int))
        stops = np.minimum(shape, np.ceil((right-lower)/spacing).astype(int))
        overlaps = []
        for axis in range(3):
            indices = np.arange(starts[axis], stops[axis])
            edges = lower[axis]+indices*spacing[axis]
            overlaps.append(np.maximum(0, np.minimum(edges+spacing[axis], right[axis])-
                                          np.maximum(edges, left[axis])))
        slices = tuple(slice(a, b) for a, b in zip(starts, stops))
        probability[slices] += (overlaps[0][:, None, None]*overlaps[1][None, :, None]*
                               overlaps[2][None, None, :])*scale
    return probability/np.prod(spacing), float(probability.sum())
