import numpy as np
import pytest

from operator_learning.numerics import (
    boundary_mass, conservative_coarsen, density_l1, group_split, nearest_target,
    normalized_probability,
)


def test_conservative_export_and_l1():
    p = np.arange(8*6*4, dtype=float).reshape(8, 6, 4)
    q = conservative_coarsen(p, (4, 3, 2))
    assert q.mean() == p.mean()
    assert density_l1(q, q+1, 2) == 48
    with pytest.raises(ValueError):
        conservative_coarsen(p, (3, 3, 2))


def test_probability_and_boundary():
    p = np.zeros((6, 6, 6))
    p[2:4, 2:4, 2:4] = 1
    assert normalized_probability(p).sum() == 1
    assert boundary_mass(p, 1) == 0
    assert np.isclose(boundary_mass(np.ones((6, 6, 6)), 1), 1-64/216)
    with pytest.raises(ValueError):
        normalized_probability(-p)


def test_nearest_baseline_only_uses_training_targets():
    x = [np.zeros((2, 2, 2)), np.ones((2, 2, 2))]
    targets = [a+10 for a in x]
    index, result = nearest_target(x, targets, np.full((2, 2, 2), .9), 1)
    assert index == 1
    np.testing.assert_array_equal(result, targets[1])


def test_group_split_reproducible_no_window_leakage():
    groups = ["a", "b", "a", "c", "d"]
    split = group_split(groups, 17, (2, 1, 1))
    assert split == group_split(groups, 17, (2, 1, 1))
    assert split[0] == split[2]
    assert set(split) == {"train", "validation", "test"}
