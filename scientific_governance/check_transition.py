"""Base-revision CI gate; never executes code from a candidate scientific run."""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def transitions(base, candidate):
    old = {g['id']: g for g in base}
    if (len(old)!=len(base) or len({g['id'] for g in candidate})!=len(candidate)
            or set(old) != {g['id'] for g in candidate}):
        raise ValueError('Gate catalogue identity changed; separate owner scope review required')
    return [g for g in candidate if g['decision_status']=='PASSED'
            and g != old[g['id']]]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',required=True)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--allowed-signers',type=Path)
    a=parser.parse_args()
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    from authority import parse, load
    base=parse(subprocess.check_output(['git','-C',str(a.root),'show',
                                       a.base+':docs/operator_learning/gates.json']))
    head=load(a.root/'docs/operator_learning/gates.json')
    changes=transitions(base,head)
    if changes and not a.allowed_signers:
        raise ValueError('Gate promotion blocked: owner-provisioned trust roots absent')
    if changes:
        # This package must be loaded from the BASE revision by trusted CI.
        sys.path.insert(0,str(Path(__file__).resolve().parent))
        from authority import verify_bundle, gate_identity, digest
        for gate in changes:
            result=verify_bundle(a.root/'scientific_governance/receipts'/gate['id'],
                                 a.allowed_signers,a.root)
            if result['gate_id']!=gate['id'] or result['report_sha256']!=gate['adjudication']['evidence_sha256']:
                raise ValueError('Catalogue is not bound to authenticated evidence')
            if result['gate_specification_sha256']!=gate_identity(gate):
                raise ValueError('Acceptance criteria differ from approved specification')
            if result['goal_sha256']!=digest(a.root/'scientific_governance/GOAL.md'):
                raise ValueError('Research objective changed')
            config=(a.root/gate['experiment_config']).resolve()
            if not config.is_relative_to(a.root.resolve()):
                raise ValueError('Experiment config escapes candidate checkout')
            if (result['config_sha256']!=gate['adjudication']['config_sha256']
                    or result['config_sha256']!=digest(config)
                    or result['source_commit']!=gate['adjudication']['predeclaration_commit']):
                raise ValueError('Approved configuration/source differs from catalogue')
    print('TRANSITION CONTROL: PASS; promotions='+str(len(changes)))


if __name__=='__main__':
    try:
        main()
    except (ValueError, OSError, KeyError) as error:
        sys.exit('TRANSITION CONTROL: BLOCKED: '+str(error))
