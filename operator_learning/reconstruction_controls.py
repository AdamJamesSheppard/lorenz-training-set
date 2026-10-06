"""Non-Gaussian diagnostic controls, never an implicit production-law replacement."""
import numpy as np

from operator_learning.reconstruction import rk4_step


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
