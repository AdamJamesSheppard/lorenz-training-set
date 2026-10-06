"""Fast graph/search tests, with positive and negative outcomes equally covered."""
import copy
import json
from pathlib import Path

import pytest

from operator_learning.research_graph import (
    GRAPH_PATH, build_graph, check_graph, outcome_status, search, validate_graph, walk,
)


ROOT = Path(__file__).resolve().parents[2]


def graph():
    return json.loads((ROOT / GRAPH_PATH).read_text())


def test_graph_is_deterministic_current_and_structurally_sound():
    first = build_graph(ROOT)
    assert first == build_graph(ROOT)
    assert validate_graph(first) == []
    assert check_graph(ROOT) == []


def test_success_failure_open_and_authorization_are_all_present():
    data = graph()
    assert any('OL-D006' in n['id'] for n in search(data, kind='outcome', status='PASSED'))
    assert any('OL-D005' in n['id'] for n in search(data, kind='outcome', status='FAILED'))
    assert any('OL-G02' in n['id'] for n in search(data, kind='gate', status='OPEN'))
    assert len(search(data, kind='gate')) == 18
    assert all(n['status'] == 'NOT_AUTHORIZED' for n in search(data, kind='authorization'))
    assert search(data, 'OSQP', kind='source')


def test_source_to_success_path_retains_edge_attribution():
    path = walk(graph(), 'source:OL-NUMPY', 5, target='outcome:OL-D006:PASSED_V2_UNCHANGED_THRESHOLDS',
                relations=['informed_by', 'tested_by', 'adjudicates', 'has_outcome'])
    assert path and all(e['attribution'] for e in path)
    assert len(path) == 5


def test_no_process_or_component_promotion():
    assert outcome_status('COMPLETED') == 'TECHNICAL_COMPLETED'
    assert outcome_status(True, 'all_predeclared_gates_passed') == 'PASSED'
    assert outcome_status(False, 'positivity_gate_passed') == 'FAILED'
    assert outcome_status(0, 'optimizer_failures') == 'RECORDED'
    assert outcome_status('a future candidate may pass') == 'RECORDED'


def test_invalid_edges_are_rejected():
    data = copy.deepcopy(graph())
    data['edges'][0]['target'] = 'missing:id'
    data['edges'][1]['attribution'] = ''
    errors = validate_graph(data)
    assert any('dangling' in e for e in errors)
    assert any('unattributed' in e for e in errors)


def test_bfs_terminates_on_cycles_and_honors_depth_and_direction():
    tiny = dict(nodes=[dict(id=x) for x in 'abc'], edges=[
        dict(source='a', target='b', relation='references'),
        dict(source='b', target='a', relation='references'),
        dict(source='b', target='c', relation='supports')])
    assert len(walk(tiny, 'a', 10)) == 3
    assert walk(tiny, 'a', 1, target='c') is None
    assert walk(tiny, 'c', 10, direction='out', target='a') is None
    assert walk(tiny, 'a', 10, target='c', relations=['references']) is None
    with pytest.raises(ValueError):
        walk(tiny, 'unknown', 1)
