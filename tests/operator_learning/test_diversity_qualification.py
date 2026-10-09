import pytest
from operator_learning.diversity_qualification import evaluate


def law(ident, source):
    return dict(id=ident, source=source, status='COMPLETED',
                reconstruction_tv_bound=.001, raw_mass=1., negative_mass=0.)


def run(laws, pairs):
    return evaluate(laws, pairs, ['a', 'b', 'c'],
                    reconstruction_tv_max=.01, mass_error_max=1e-10)


def evidence():
    # Duplicate laws remain present; both differ from the third law.
    return [law('a', 'one'), law('b', 'one'), law('c', 'two')], [
        dict(a='a', b='b', tv=0.), dict(a='a', b='c', tv=.2), dict(a='b', b='c', tv=.2)]


def test_duplicates_retained_without_coverage_claim():
    result = run(*evidence())
    assert result['review_status'] == 'ELIGIBLE_FOR_SCOPED_REVIEW'
    assert len(result['ambiguous_pairs']) == 1
    assert result['gate_status'] == 'OPEN'
    assert result['exclusions'] == []


def test_missing_attempt_or_pair_blocks_review():
    laws, pairs = evidence()
    assert run(laws[:-1], pairs)['failures']
    assert run(laws, pairs[:-1])['missing_pairs']


def test_failed_reconstruction_cannot_be_filtered():
    laws, pairs = evidence()
    laws[0]['reconstruction_tv_bound'] = .02
    assert run(laws, pairs)['review_status'] == 'FAILED_PROPOSED_CRITERIA'


def test_same_source_differences_do_not_supply_cross_source_witness():
    laws, pairs = evidence()
    for row in laws:
        row['source'] = 'one'
    assert len(run(laws, pairs)['unresolved_laws']) == 3


@pytest.mark.parametrize('tv', [float('nan'), -1., 1.1])
def test_invalid_tv_rejected(tv):
    laws, pairs = evidence()
    pairs[0]['tv'] = tv
    with pytest.raises(ValueError):
        run(laws, pairs)


def test_duplicate_pair_rejected():
    laws, pairs = evidence()
    with pytest.raises(ValueError):
        run(laws, pairs + pairs[:1])


@pytest.mark.parametrize('field,value', [
    ('raw_mass', 0.), ('raw_mass', float('inf')),
    ('negative_mass', 1e-15), ('negative_mass', -1.),
    ('reconstruction_tv_bound', float('nan')),
    ('reconstruction_tv_bound', -1.), ('source', ''), ('status', 'FAILED')])
def test_invalid_or_failed_control_never_supplies_witness(field, value):
    laws, pairs = evidence()
    laws[0][field] = value
    result = run(laws, pairs)
    assert result['review_status'] == 'FAILED_PROPOSED_CRITERIA'
    assert result['witnesses']['a'] == []
    assert result['actual_attempts'] == 3


def test_zero_margin_remains_ambiguous():
    laws, pairs = evidence()
    for pair in pairs:
        pair['tv'] = 0.
    result = evaluate(laws, pairs, ['a', 'b', 'c'],
                      reconstruction_tv_max=.01, mass_error_max=0.)
    assert not result['resolved_pairs']
    assert len(result['ambiguous_pairs']) == 3


def test_inputs_are_not_mutated_and_pair_order_is_irrelevant():
    import copy
    laws, pairs = evidence()
    before = copy.deepcopy((laws, pairs))
    result = run(laws, pairs)
    assert (laws, pairs) == before
    reversed_pairs = [dict(a=p['b'], b=p['a'], tv=p['tv']) for p in pairs]
    assert run(laws, reversed_pairs) == result


def test_cli_emits_open_status_without_rewriting_evidence(tmp_path):
    import json
    import subprocess
    import sys
    laws, pairs = evidence()
    path = tmp_path / 'evidence.json'
    payload = json.dumps(dict(laws=laws, pairs=pairs, expected_ids=['a', 'b', 'c'],
                              thresholds=dict(reconstruction_tv_max=.01, mass_error_max=1e-10)))
    path.write_text(payload)
    completed = subprocess.run([sys.executable, '-m', 'operator_learning.diversity_qualification',
                                str(path)], capture_output=True, text=True, check=True)
    assert json.loads(completed.stdout)['gate_status'] == 'OPEN'
    assert path.read_text() == payload
