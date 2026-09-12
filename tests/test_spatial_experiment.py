from pathlib import Path

import numpy as np
import yaml

from same_mesh_q2_study import _sample_truncated_gaussian


ROOT = Path(__file__).resolve().parents[1]


def test_common_continuous_gaussian_sampler_is_bounded_and_reproducible():
    mean = np.array([0.0, 0.0, 0.0])
    covariance = np.eye(3)
    bounds = ((-0.5, 0.5),) * 3
    first, first_proposals = _sample_truncated_gaussian(
        mean, covariance, bounds, 200, np.random.default_rng(42)
    )
    second, second_proposals = _sample_truncated_gaussian(
        mean, covariance, bounds, 200, np.random.default_rng(42)
    )
    assert np.array_equal(first, second)
    assert first_proposals == second_proposals
    assert np.all(first >= -0.5)
    assert np.all(first <= 0.5)


def test_spatial_predeclaration_has_constant_ratio_and_one_common_grid():
    config = yaml.safe_load(
        (ROOT / "experiments/local-q2-cn-spatial-refinement.yaml").read_text()
    )
    study = config["study"]
    branches = study["branches"]
    cells = np.asarray([branch["cells"] for branch in branches])
    assert np.allclose(cells[1] / cells[0], 1.5)
    assert np.allclose(cells[2] / cells[1], 1.5)
    common_shape = tuple(study["common_comparison_grid"])
    for branch in branches:
        exported_shape = tuple(
            count * branch["export_subcells"] for count in branch["cells"]
        )
        assert exported_shape == common_shape
        assert branch["degree"] == 2
        assert branch["theta"] == 0.5
        assert branch["optimizer_backend"] == "osqp"
    assert study["initialization"] == "gaussian_projected"
    assert config["scientific_decision"]["temporal_safeguard_threshold"] == 0.00081
    assert config["scientific_decision"]["safeguard_dt"] == 0.000078125
