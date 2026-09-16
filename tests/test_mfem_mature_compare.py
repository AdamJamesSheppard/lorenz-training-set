"""Small exact checks for the conservative common-grid comparison."""

import numpy as np

from mfem.compare_mature_equivalence import VOLUME, statistics


def test_uniform_voxel_statistics() -> None:
    values = np.ones((2, 2, 2), dtype=float)
    result = statistics(values)
    assert np.isclose(result["mass"], VOLUME)
    np.testing.assert_allclose(result["mean"], [0.0, 0.0, 30.0], atol=1e-12)
    np.testing.assert_allclose(
        result["covariance"], np.diag([225.0, 400.0, 400.0]), atol=1e-12
    )
