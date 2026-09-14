import json
from pathlib import Path

import numpy as np
import yaml

from same_mesh_q2_study import (
    _condition_mixture_on_z,
    _model,
    _sample_truncated_gaussian,
    _sample_truncated_mixture,
)


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


def test_full_spd_predeclarations_reconstruct_diffusion_and_fix_reference_seed():
    controlled = yaml.safe_load(
        (ROOT / "experiments/local-q2-cn-full-spd-controlled.yaml").read_text()
    )
    hierarchy = yaml.safe_load(
        (ROOT / "experiments/local-q2-cn-full-spd-spatial-refinement.yaml").read_text()
    )
    expected = np.array([[1.0, 0.4, 0.2], [0.4, 1.0, 0.3], [0.2, 0.3, 1.0]])
    for config in (controlled, hierarchy):
        study = config["study"]
        assert np.allclose(_model(study["noise_matrix"]).diffusion, expected, atol=1e-14)
        assert np.linalg.eigvalsh(expected).min() > 0.0
        assert study["monte_carlo_paths"] == 1_000_000
        assert study["bootstrap_replicates"] == 1_000
        assert study["bootstrap_seed"] == 20261910
    assert len(controlled["study"]["branches"]) == 1
    assert len(hierarchy["study"]["branches"]) == 3


def test_mature_bimodal_predeclaration_is_full_spd_and_common_grid():
    config = yaml.safe_load(
        (ROOT / "experiments/mature-state-decision.yaml").read_text()
    )
    study=config["study"]
    expected=np.array([[1.0,0.4,0.2],[0.4,1.0,0.3],[0.2,0.3,1.0]])
    assert config["kind"] == "mature_full_spd_q2_study"
    assert study["initialization"] == "mixture_projected"
    assert np.allclose(_model(study["noise_matrix"]).diffusion,expected,atol=1e-14)
    assert study["monte_carlo_paths"] == 1_000_000
    assert study["bootstrap_replicates"] == 1_000
    assert study["observation_variance"] > 0.0
    for branch in study["branches"]:
        assert tuple(np.asarray(branch["cells"])*branch["export_subcells"]) == tuple(
            study["common_comparison_grid"]
        )


def test_fine_graded_predeclaration_aligns_both_comparators_to_common_grid():
    config=yaml.safe_load(
        (ROOT/"experiments/mature-graded-fine-comparison.yaml").read_text()
    )
    design=json.loads(
        (ROOT/"experiments/mature-graded-fine-axes.json").read_text()
    )
    branch=config["study"]["branches"][0]
    assert config["kind"]=="mature_graded_q2_study"
    assert tuple(branch["cells"])==(58,68,56)
    assert tuple(branch["common_export_grid"])==(180,216,216)
    assert branch["comparator_report"]
    assert branch["secondary_comparator_report"]
    for name,count in zip(("x","y","z"),branch["cells"]):
        edges=design["edge_indices"][name]
        assert len(edges)==count+1
        assert all(right>left for left,right in zip(edges,edges[1:]))
        assert set(np.diff(edges))=={2,6}
    dof_ratio=np.prod(branch["cells"])/np.prod((60,72,72))
    assert dof_ratio<=config["scientific_decision"]["comparator_limits"][
        "maximum_dg_dof_ratio"
    ]


def test_z_conditioning_and_truncated_mixture_sampling_preserve_lobe_symmetry():
    reflection=np.diag([-1.0,-1.0,1.0])
    mean=np.array([8.0,8.0,25.0]); covariance=np.diag([2.0,2.0,3.0])
    mixture={"weights":[0.5,0.5],"means":[mean.tolist(),(reflection@mean).tolist()],
             "covariances":[covariance.tolist(),(reflection@covariance@reflection).tolist()],
             "construction":"test"}
    posterior=_condition_mixture_on_z(mixture,24.0,4.0)
    assert np.allclose(posterior["weights"],[0.5,0.5])
    samples,proposals=_sample_truncated_mixture(
        posterior,((-30.0,30.0),(-40.0,40.0),(-10.0,70.0)),5000,
        np.random.default_rng(14),
    )
    assert proposals>=len(samples)
    assert abs(np.mean(samples[:,0]>0.0)-0.5)<0.04
