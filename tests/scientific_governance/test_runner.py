"""Runner mechanics only; mocked authority cannot establish authenticated execution."""
import hashlib
import json
import sys

import pytest

from scientific_governance import runner


@pytest.fixture
def setup(tmp_path,monkeypatch):
    checkout=tmp_path/'source';checkout.mkdir()
    source=dict(dirty=False,commit='a'*40,source_tree_sha256='b'*64,
                python='fixture',platform='fixture',packages=[])
    environment={k:source[k] for k in ['python','platform','packages']}
    spec=dict(source_commit=source['commit'],source_tree_sha256=source['source_tree_sha256'],
              environment_sha256=hashlib.sha256(json.dumps(environment,sort_keys=True).encode()).hexdigest(),
              approved_at='2020-01-01T00:00:00+00:00',
              retry_budget=0,exclusions=[],required_artifacts=['1.stdout','1.stderr','attempts.json'],
              attempts=[dict(id='success',command=[sys.executable,'-c','print("fixture")'],timeout_seconds=5),
                        dict(id='failure',command=[sys.executable,'-c','raise SystemExit(3)'],timeout_seconds=5)])
    path=tmp_path/'spec.json';path.write_text(json.dumps(spec))
    (tmp_path/'spec.json.sig').write_text('synthetic mocked signature')
    monkeypatch.setattr(runner,'signed_snapshot',lambda *a:(spec,'c'*64,'d'*64))
    monkeypatch.setattr(runner,'validate_spec',lambda x:x)
    monkeypatch.setattr(runner,'inventory',lambda root:source)
    return path,checkout,tmp_path/'output',spec,source


def test_attempts_preserve_failures_and_do_not_authorize(setup):
    path,checkout,output,*_=setup
    result=runner.execute(path,'mocked roots',checkout,output)
    assert [r['status'] for r in result['attempts']]==['COMPLETED','FAILED']
    assert result['attempts'][1]['exit_code']==3
    assert not result['promotion_authorized']
    assert result['status']=='UNSIGNED_CANDIDATE_EXECUTION'
    assert (output/'1.stdout').read_text()=='fixture\n'
    assert json.loads((output/'attempts.json').read_text())==result['attempts']


def test_missing_required_artifacts_reject_execution(setup):
    path,checkout,output,spec,_=setup
    spec['required_artifacts'].append('unproduced-density.npz')
    with pytest.raises(ValueError,match='Required evidence missing'):
        runner.execute(path,'mocked roots',checkout,output)


def test_retry_budget_and_source_changes_rejected(setup):
    path,checkout,output,spec,source=setup
    spec['retry_budget']=1
    with pytest.raises(ValueError,match='no retries'):
        runner.execute(path,'mocked roots',checkout,output)
    spec['retry_budget']=0
    source['dirty']=True
    with pytest.raises(ValueError,match='Source checkout'):
        runner.execute(path,'mocked roots',checkout,output)


def test_future_approval_rejected_before_dispatch(setup):
    path,checkout,output,spec,_=setup
    spec['approved_at']='2999-01-01T00:00:00+00:00'
    with pytest.raises(ValueError,match='future'):
        runner.execute(path,'mocked roots',checkout,output)
    assert not output.exists()
