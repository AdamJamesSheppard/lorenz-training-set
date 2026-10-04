"""Conservative neural training export must preserve physical voxel mass."""
import importlib.util
from pathlib import Path
import sys

import numpy as np


def test_aligned_coarsening_preserves_mass():
    path = Path(__file__).resolve().parents[1]/'mfem/run_neural_pilot.py'
    sys.path.insert(0, str(path.parent))
    try:
        spec = importlib.util.spec_from_file_location('neural_pilot_export', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    # A nonconstant broadcast view avoids allocating a full fine-grid fixture.
    p = np.broadcast_to(np.arange(180)[:, None, None], (180,216,216))
    q = module.coarsen(p)
    assert q.shape == (60,72,72)
    assert np.isclose(q.mean(), p.mean(), atol=1e-12)
    np.testing.assert_allclose(q[:,0,0], np.arange(60)*3+1)


def test_sampled_prior_is_positive_normalized_and_reproducible():
    path=Path(__file__).resolve().parents[1]/'mfem/run_neural_pilot.py'
    sys.path.insert(0,str(path.parent))
    try:
        spec=importlib.util.spec_from_file_location('pilot_prior_test',path)
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    _,cloud=module.attractor_samples(10,spinup=.01,window=.05)
    _,again=module.attractor_samples(10,spinup=.01,window=.05)
    np.testing.assert_array_equal(cloud,again)
    vertices=module.vertex_density(cloud)
    assert vertices.shape==(46,55,55) and vertices.min()>=0
    weights=[np.ones(n) for n in vertices.shape]
    for weight in weights:
        weight[[0,-1]]=.5
    mass=np.einsum('ijk,i,j,k',vertices,*weights)*384000/(45*54*54)
    assert abs(mass-1)<1e-12
