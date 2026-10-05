"""Physical density metrics and simple baseline diagnostics; NumPy only."""
import hashlib
import numpy as np


def conservative_coarsen(density, shape):
    density = np.asarray(density)
    if density.ndim != 3 or len(shape) != 3 or any(n <= 0 for n in shape):
        raise ValueError("positive 3D shape required")
    factors = tuple(a // b for a, b in zip(density.shape, shape))
    if any(a != b * f for a, b, f in zip(density.shape, shape, factors)):
        raise ValueError("grids must be aligned integer refinements")
    return density.reshape(shape[0], factors[0], shape[1], factors[1],
                           shape[2], factors[2]).mean(axis=(1, 3, 5))


def density_l1(a, b, voxel_volume):
    a, b = np.asarray(a), np.asarray(b)
    if a.shape != b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError("finite matched representations required")
    if not np.isfinite(voxel_volume) or voxel_volume <= 0:
        raise ValueError("positive voxel volume required")
    return float(np.abs(a - b).sum() * voxel_volume)


def normalized_probability(density):
    density = np.asarray(density, dtype=np.float64)
    if not np.isfinite(density).all() or np.any(density < 0) or density.sum() <= 0:
        raise ValueError("nonnegative finite nonempty density required")
    return density / density.sum()


def boundary_mass(probability, layers):
    p = normalized_probability(probability)
    if layers < 1 or any(2 * layers >= n for n in p.shape) or p.ndim != 3:
        raise ValueError("boundary must leave an interior")
    return float(p.sum() - p[layers:-layers, layers:-layers, layers:-layers].sum())


def nearest_target(training_inputs, training_targets, query, voxel_volume):
    if not training_inputs or len(training_inputs) != len(training_targets):
        raise ValueError("matched nonempty training population required")
    index = int(np.argmin([density_l1(x, query, voxel_volume) for x in training_inputs]))
    return index, training_targets[index]


def group_split(groups, seed, counts):
    """Deterministic group-level split; related windows must share a group ID."""
    unique = sorted(set(groups))
    if sum(counts) != len(unique) or len(counts) != 3 or min(counts) < 0:
        raise ValueError("counts must cover unique groups")
    order = sorted(unique, key=lambda g: hashlib.sha256(f"{seed}:{g}".encode()).hexdigest())
    labels = ["train"] * counts[0] + ["validation"] * counts[1] + ["test"] * counts[2]
    assignment = dict(zip(order, labels))
    return [assignment[g] for g in groups]
