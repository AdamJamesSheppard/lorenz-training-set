"""Independent approval protocol. No key generation, signing or gate mutation.

Public trust roots must be supplied by the owner outside the candidate checkout.
Signatures authenticate exact bytes; they do not prove scientific truth.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROLES = ('owner', 'executor', 'verifier')
HEX = re.compile(r'[0-9a-f]{64}\Z')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def gate_identity(gate):
    """Bind scientific content; mutable status/evidence location is separate."""
    content={k:v for k,v in gate.items() if k not in
             {'decision_status','adjudication','evidence_run'}}
    return hashlib.sha256(json.dumps(content,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def load(path):
    return parse(Path(path).read_bytes())


def parse(payload):
    def unique(items):
        data = {}
        for key, value in items:
            if key in data:
                raise ValueError('Duplicate JSON key: '+key)
            data[key] = value
        return data
    return json.loads(payload, object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def validate_spec(spec):
    required = {'id', 'gate_id', 'question', 'population', 'hypotheses', 'primary_metric',
                'acceptance_rule', 'failure_rule', 'attempts', 'retry_budget', 'exclusions',
                'data_allocation', 'required_artifacts', 'limitations', 'propositions',
                'goal_sha256', 'source_commit', 'source_tree_sha256', 'environment_sha256',
                'gate_specification_sha256', 'config_sha256', 'approved_at'}
    if not required <= spec.keys() or any(spec[k] in (None, '', []) for k in required-{'retry_budget','exclusions'}):
        raise ValueError('Incomplete scientific specification')
    if set(spec['propositions']) != {'demonstrated', 'not_demonstrated', 'advances_goal'}:
        raise ValueError('Three scientific propositions required')
    if not all(isinstance(v,str) and v.strip() for v in spec['propositions'].values()):
        raise ValueError('Blank proposition')
    if type(spec['retry_budget']) is not int or spec['retry_budget'] < 0:
        raise ValueError('Explicit nonnegative retry budget required')
    ids = [x['id'] for x in spec['attempts']]
    if len(ids) != len(set(ids)) or not ids:
        raise ValueError('Nonempty unique attempt ledger required')
    for key in ['goal_sha256','source_tree_sha256','environment_sha256',
                'gate_specification_sha256','config_sha256']:
        if not isinstance(spec[key],str) or not HEX.fullmatch(spec[key]):
            raise ValueError('Invalid digest: '+key)
    if not re.fullmatch('[0-9a-f]{40}',spec['source_commit']):
        raise ValueError('Exact committed source revision required')
    from datetime import datetime
    if datetime.fromisoformat(spec['approved_at']).tzinfo is None:
        raise ValueError('Timezone-aware approval timestamp required')
    return spec


def signed_snapshot(document, signature, allowed_signers, role, checkout):
    if role not in ROLES:
        raise ValueError('Unknown trust role')
    root, keys = Path(checkout).resolve(), Path(allowed_signers).resolve()
    if keys.is_relative_to(root):
        raise ValueError('Trust root must be provisioned outside the checkout')
    # Distinct keys are necessary, not sufficient for independent operators.
    mapping = {}
    key_bytes=keys.read_bytes()
    for line in key_bytes.decode().splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        parts = line.split()
        if len(parts) != 3 or parts[0] not in ROLES or parts[0] in mapping:
            raise ValueError('Use one unoptioned SSH public key per trust role')
        mapping[parts[0]] = tuple(parts[1:])
    if set(mapping) != set(ROLES) or len(set(mapping.values())) != 3:
        raise ValueError('Three distinct owner/executor/verifier keys required')
    payload=Path(document).read_bytes()
    signature_bytes=Path(signature).read_bytes()
    from tempfile import TemporaryDirectory
    with TemporaryDirectory(prefix='lorenz-signature-') as directory:
        frozen_keys=Path(directory)/'allowed_signers'
        frozen_sig=Path(directory)/'signature'
        frozen_keys.write_bytes(key_bytes);frozen_sig.write_bytes(signature_bytes)
        result = subprocess.run(['ssh-keygen','-Y','verify','-f',str(frozen_keys),'-I',role,
                                 '-n','lorenz-scientific-governance-v1','-s',str(frozen_sig)],
                                input=payload,capture_output=True)
    if result.returncode:
        raise ValueError('Signature rejected for '+role)
    return (parse(payload),hashlib.sha256(payload).hexdigest(),
            hashlib.sha256(signature_bytes).hexdigest())


def verify_signature(document, signature, allowed_signers, role, checkout):
    return signed_snapshot(document,signature,allowed_signers,role,checkout)[0]


def verify_bundle(directory, allowed_signers, checkout):
    """Require signed specification, execution, verification and final approval."""
    directory = Path(directory)
    snapshots={}
    def receipt(name, role):
        snapshots[name]=signed_snapshot(directory/(name+'.json'),directory/(name+'.json.sig'),
                                        allowed_signers,role,checkout)
        return snapshots[name][0]
    spec = validate_spec(receipt('spec','owner'))
    execution = receipt('execution','executor')
    verification = receipt('verification','verifier')
    approval = receipt('approval','owner')
    expected = dict(spec_sha256=snapshots['spec'][1],
                    execution_sha256=snapshots['execution'][1],
                    verification_sha256=snapshots['verification'][1])
    if execution.get('spec_sha256') != expected['spec_sha256']:
        raise ValueError('Execution specification mismatch')
    if execution.get('spec_signature_sha256') != snapshots['spec'][2]:
        raise ValueError('Executor must bind the exact approved specification signature')
    from datetime import datetime
    started=datetime.fromisoformat(execution['started_at'])
    if started.tzinfo is None or started < datetime.fromisoformat(spec['approved_at']):
        raise ValueError('Execution predates specification approval')
    if verification.get('execution_sha256') != expected['execution_sha256']:
        raise ValueError('Verifier execution mismatch')
    if verification.get('spec_sha256') != expected['spec_sha256']:
        raise ValueError('Verifier specification mismatch')
    if any(approval.get(k) != v for k,v in expected.items()):
        raise ValueError('Owner approval does not bind exact evidence chain')
    if approval.get('gate_id') != spec['gate_id'] or approval.get('claim') != spec['propositions']['demonstrated']:
        raise ValueError('Approval claim/scope mismatch')
    if approval.get('decision') != 'APPROVE' or verification.get('decision') != 'VERIFIED':
        raise ValueError('No verified owner-approved scientific result')
    if execution.get('source_commit') != spec['source_commit']:
        raise ValueError('Executed source mismatch')
    for name in ['source_tree_sha256','environment_sha256']:
        if execution.get(name) != spec[name]:
            raise ValueError('Executed environment/source manifest mismatch')
    attempts = execution.get('attempts',[])
    wanted = [x['id'] for x in spec['attempts']]
    if [x['id'] for x in attempts] != wanted:
        raise ValueError('Attempt ledger mismatch; no missing or reordered cases')
    if any(x.get('status') != 'COMPLETED' for x in attempts):
        raise ValueError('Failed attempts preclude qualification')
    for record in [execution, verification]:
        for key in ['archive_manifest_sha256','report_sha256']:
            if not HEX.fullmatch(str(record.get(key,''))):
                raise ValueError('Missing immutable evidence identity')
    if execution['archive_manifest_sha256'] != verification['archive_manifest_sha256']:
        raise ValueError('Verifier used a different archive')
    if verification.get('producer_report_sha256') != execution['report_sha256']:
        raise ValueError('Verifier did not attest the same producer report')
    if spec['retry_budget'] != 0 or spec['exclusions'] or execution.get('retries') != [] or execution.get('exclusions') != []:
        raise ValueError('Protocol v1 permits no retries or exclusions')
    if not execution.get('archive_uri') or verification.get('independence') != 'SEPARATE_IMPLEMENTATION_AND_OPERATOR':
        raise ValueError('Archive or verifier independence not attested')
    return dict(gate_id=spec['gate_id'],claim=approval['claim'],status='AUTHENTICATED_APPROVAL',
                spec_sha256=expected['spec_sha256'],report_sha256=execution['report_sha256'],
                gate_specification_sha256=spec['gate_specification_sha256'],
                config_sha256=spec['config_sha256'],goal_sha256=spec['goal_sha256'],
                source_commit=spec['source_commit'])
