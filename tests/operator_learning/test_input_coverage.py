import json
from pathlib import Path

import numpy as np
import pytest

from scripts.run_input_coverage import boundary_probability, grouped_coverage, validate


def test_group_allocation_keeps_windows_together_and_reports_missing():
    laws=[dict(id=f'{g}:{w}',seed=g) for g in range(3) for w in range(2)]
    pairs=[dict(laws=[a['id'],b['id']],tv=.1) for a in laws[:2] for b in laws[2:]]
    result=grouped_coverage(laws,pairs,[0,1,2],[1])[0]
    assert result['selected_groups']==[0]
    assert result['attempted_queries']==4
    assert result['measured_queries']==4
    assert all(x['law'].split(':')[0]!='0' for x in result['rows'])
    unresolved=grouped_coverage(laws,pairs,[0,1,2],[1],{'0:0','1:0'})[0]
    assert unresolved['attempted_queries']==4
    assert unresolved['measured_queries']==1
    with pytest.raises(ValueError):
        grouped_coverage(laws,pairs,[0,0,1],[1])


def test_common_boundary_integrates_uniform_voxels_on_different_grids():
    for shape in [(3,4,5),(6,8,10)]:
        p=np.ones(shape)/8
        assert boundary_probability(p,[(0,2)]*3,[.2]*3)==pytest.approx(1-.8**3)
    with pytest.raises(ValueError):
        boundary_probability(np.ones((2,2,2)),[(0,2)]*3,[0,.1,.1])


def test_config_has_complete_frozen_group_scope():
    root=Path(__file__).resolve().parents[2]
    config=json.loads((root/'experiments/operator_learning/OL-G03_input_coverage_characterization_v2.json').read_text())
    validate(config)
    config['group_orders'][0][0]=config['group_orders'][0][1]
    with pytest.raises(ValueError,match='permutations'):
        validate(config)
