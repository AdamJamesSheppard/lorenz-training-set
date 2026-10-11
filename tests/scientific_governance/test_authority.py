"""Synthetic keys only. Tests establish protocol behavior, never real approval."""
import copy
import json
from pathlib import Path
import subprocess

import pytest

from scientific_governance.authority import digest, gate_identity, validate_spec, verify_bundle, verify_signature
from scientific_governance.check_transition import transitions


@pytest.fixture
def bundle(tmp_path):
    checkout=tmp_path/'checkout';checkout.mkdir()
    directory=checkout/'receipts';directory.mkdir()
    keys=tmp_path/'keys';keys.mkdir()
    allowed=keys/'allowed_signers'
    lines=[]
    for role in ['owner','executor','verifier']:
        key=keys/role
        subprocess.run(['ssh-keygen','-q','-t','ed25519','-N','','-f',str(key)],check=True)
        lines.append(role+' '+' '.join(Path(str(key)+'.pub').read_text().split()[:2]))
    allowed.write_text('\n'.join(lines)+'\n')
    def write(name,record,role):
        path=directory/(name+'.json');path.write_text(json.dumps(record,sort_keys=True))
        signature=Path(str(path)+'.sig')
        if signature.exists():
            signature.unlink()  # Disposable test fixture, never research evidence.
        subprocess.run(['ssh-keygen','-Y','sign','-f',str(keys/role),'-n',
                        'lorenz-scientific-governance-v1',str(path)],check=True,capture_output=True)
    spec=dict(id='synthetic',gate_id='OL-G04_REFERENCE_TARGET_APPLICABILITY',question='fixture',
              population='fixture',hypotheses=['failure','success'],primary_metric='fixture',
              acceptance_rule='fixture',failure_rule='fixture',attempts=[dict(id='a')],
              retry_budget=0,exclusions=[],data_allocation='fixture',required_artifacts=['fixture'],
              limitations='fixture',propositions=dict(demonstrated='fixture',not_demonstrated='utility',advances_goal='fixture'),
              source_commit='a'*40,approved_at='2026-10-10T00:00:00+00:00',
              **{k:'a'*64 for k in ['goal_sha256','source_tree_sha256','environment_sha256',
                                    'gate_specification_sha256','config_sha256']})
    write('spec',spec,'owner')
    execution=dict(spec_sha256=digest(directory/'spec.json'),
                   spec_signature_sha256=digest(directory/'spec.json.sig'),
                   started_at='2026-10-10T00:01:00+00:00',source_commit=spec['source_commit'],
                   source_tree_sha256=spec['source_tree_sha256'],environment_sha256=spec['environment_sha256'],
                   attempts=[dict(id='a',status='COMPLETED')],retries=[],exclusions=[],
                   archive_manifest_sha256='b'*64,report_sha256='c'*64,archive_uri='fixture://not-real')
    write('execution',execution,'executor')
    verification=dict(spec_sha256=digest(directory/'spec.json'),
                      execution_sha256=digest(directory/'execution.json'),decision='VERIFIED',
                      archive_manifest_sha256='b'*64,report_sha256='d'*64,producer_report_sha256='c'*64,
                      independence='SEPARATE_IMPLEMENTATION_AND_OPERATOR')
    write('verification',verification,'verifier')
    approval=dict(spec_sha256=digest(directory/'spec.json'),execution_sha256=digest(directory/'execution.json'),
                  verification_sha256=digest(directory/'verification.json'),decision='APPROVE',
                  gate_id=spec['gate_id'],claim='fixture')
    write('approval',approval,'owner')
    return directory,allowed,checkout,write,execution,verification,approval


def test_authentication_chain_validates_synthetic_bundle(bundle):
    d,k,c,*_=bundle
    assert verify_bundle(d,k,c)['status']=='AUTHENTICATED_APPROVAL'


@pytest.mark.parametrize('mutation',['missing_attempt','altered_hash','retry','changed_report','backdate'])
def test_authenticated_but_inconsistent_evidence_rejected(bundle,mutation):
    d,k,c,write,execution,verification,approval=bundle
    if mutation=='missing_attempt':execution['attempts']=[]
    if mutation=='altered_hash':execution['spec_sha256']='f'*64
    if mutation=='retry':execution['retries']=[dict(id='a')]
    if mutation=='changed_report':verification['producer_report_sha256']='f'*64
    if mutation=='backdate':execution['started_at']='2026-10-09T00:00:00+00:00'
    write('execution',execution,'executor')
    verification['execution_sha256']=digest(d/'execution.json')
    write('verification',verification,'verifier')
    approval['execution_sha256']=digest(d/'execution.json')
    approval['verification_sha256']=digest(d/'verification.json')
    write('approval',approval,'owner')
    with pytest.raises(ValueError):verify_bundle(d,k,c)


def test_forged_owner_receipt_rejected(bundle):
    d,k,c,write,_,_,approval=bundle
    write('approval',approval,'executor')
    with pytest.raises(ValueError):verify_bundle(d,k,c)


def test_editable_repository_trust_roots_rejected(bundle):
    d,k,c,*_=bundle
    local=c/'allowed_signers';local.write_text(k.read_text())
    with pytest.raises(ValueError):verify_bundle(d,local,c)


def test_changed_criteria_even_after_pass_requires_new_authentication():
    gate=dict(id='a',decision_status='PASSED',predeclared_thresholds=1)
    altered=copy.deepcopy(gate);altered['predeclared_thresholds']=2
    assert transitions([gate],[altered])==[altered]
    assert gate_identity(gate)!=gate_identity(altered)


def test_historical_unchanged_pass_is_not_retroactively_invalidated():
    gate=dict(id='a',decision_status='PASSED')
    assert transitions([gate],[gate])==[]


def test_duplicate_gate_identity_cannot_hide_a_transition():
    gate=dict(id='a',decision_status='PASSED')
    with pytest.raises(ValueError):transitions([gate],[gate,gate])


def test_document_is_parsed_from_authenticated_snapshot(bundle,monkeypatch):
    import scientific_governance.authority as module
    d,k,c,*_=bundle
    original=module.subprocess.run
    def racing_verify(*args,**kwargs):
        result=original(*args,**kwargs)
        (d/'approval.json').write_text('{"decision":"UNSIGNED_REPLACEMENT"}')
        return result
    monkeypatch.setattr(module.subprocess,'run',racing_verify)
    approved=verify_signature(d/'approval.json',d/'approval.json.sig',k,'owner',c)
    assert approved['decision']=='APPROVE'
