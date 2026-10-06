import numpy as np
import pytest

from scripts.run_reconstruction_qualification import bounds, validate


def test_all_phases_and_matching_integration_times():
    fine = np.zeros((32, 3))
    fine[:, 0] = np.arange(32)*.001
    coarse = fine[1::2].copy()
    result = bounds(fine, coarse, 8, [1, 1, 1])
    assert len(result['sampling_tv_upper']) == 4
    assert len(result['aligned_integration_tv_upper']) == 2
    assert max(result['aligned_integration_tv_upper']) == 0
    assert result['total_tv_upper'] > 0


def test_qualification_rejects_undeclared_configuration():
    with pytest.raises(ValueError, match='incomplete'):
        validate({'candidate_count': 20000})
