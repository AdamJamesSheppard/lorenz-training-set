"""Service-side runner prototype: signed spec, explicit attempts, no promotion.

Deploy only in an isolated execution account without owner/verifier keys or final
evaluation access. Running this under the implementing account is NOT trusted.
Output receipts remain UNSIGNED until the independent service signs them.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

from scientific_governance.authority import digest, validate_spec, signed_snapshot
from scientific_governance.provenance import inventory


def execute(spec_path,signers,checkout,output):
    checkout,output=Path(checkout).resolve(),Path(output).resolve()
    spec,spec_digest,spec_signature_digest=signed_snapshot(spec_path,str(spec_path)+'.sig',signers,'owner',checkout)
    spec=validate_spec(spec)
    if datetime.fromisoformat(spec['approved_at'])>datetime.now(timezone.utc):
        raise ValueError('Specification approval lies in the future')
    source=inventory(checkout)
    if (source['dirty'] or source['commit']!=spec['source_commit']
            or source['source_tree_sha256']!=spec['source_tree_sha256']):
        raise ValueError('Source checkout must match approved complete manifest')
    environment={k:source[k] for k in ['python','platform','packages']}
    import hashlib
    if hashlib.sha256(json.dumps(environment,sort_keys=True).encode()).hexdigest()!=spec['environment_sha256']:
        raise ValueError('Runtime environment differs')
    if spec['retry_budget']!=0 or spec['exclusions']:
        raise ValueError('Prototype supports no retries or exclusions; separate reviewed runner required')
    if output.is_relative_to(checkout):
        raise ValueError('Evidence output must be outside the source checkout')
    output.mkdir(parents=True,exist_ok=False)
    started=datetime.now(timezone.utc).isoformat()
    rows=[]
    for attempt in spec['attempts']:
        command=attempt['command']
        if not isinstance(command,list) or not command or not all(isinstance(v,str) for v in command):
            raise ValueError('Explicit argument-vector command required')
        command=[v.replace('{output}',str(output)) for v in command]
        row=dict(id=attempt['id'],status='STARTED',command=command,
                 started=datetime.now(timezone.utc).isoformat())
        rows.append(row)
        (output/'attempts.json').write_text(json.dumps(rows,indent=2)+'\n')
        try:
            result=subprocess.run(command,cwd=checkout,capture_output=True,timeout=attempt['timeout_seconds'])
            (output/(str(len(rows))+'.stdout')).write_bytes(result.stdout)
            (output/(str(len(rows))+'.stderr')).write_bytes(result.stderr)
            row.update(status='COMPLETED' if result.returncode==0 else 'FAILED',exit_code=result.returncode)
        except (OSError,subprocess.TimeoutExpired) as error:
            for suffix,attribute in [('stdout','stdout'),('stderr','stderr')]:
                (output/(str(len(rows))+'.'+suffix)).write_bytes(getattr(error,attribute,None) or b'')
            row.update(status='FAILED',error=str(error))
        row['finished']=datetime.now(timezone.utc).isoformat()
        (output/'attempts.json').write_text(json.dumps(rows,indent=2)+'\n')
    after=inventory(checkout)
    if after['dirty'] or after['source_tree_sha256']!=source['source_tree_sha256']:
        raise ValueError('Execution modified the approved source tree')
    for name in spec['required_artifacts']:
        path=Path(name)
        if (path.is_absolute() or '..' in path.parts
                or not (output/path).resolve().is_relative_to(output)
                or not (output/path).is_file()):
            raise ValueError('Required evidence missing or unsafe: '+str(name))
    manifest={}
    for path in output.rglob('*'):
        if path.is_symlink():
            raise ValueError('Symlinks prohibited in execution evidence')
        if path.is_file():
            manifest[str(path.relative_to(output))]=digest(path)
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return dict(status='UNSIGNED_CANDIDATE_EXECUTION',spec_sha256=spec_digest,
                spec_signature_sha256=spec_signature_digest,started_at=started,
                retries=[],exclusions=[],
                source_commit=source['commit'],source_tree_sha256=source['source_tree_sha256'],
                environment_sha256=spec['environment_sha256'],attempts=rows,
                archive_manifest_sha256=digest(output/'manifest.json'),
                required_artifacts_verified=spec['required_artifacts'],
                promotion_authorized=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['spec','signers','checkout','output']:
        p.add_argument('--'+name,required=True,type=Path)
    a=p.parse_args();print(json.dumps(execute(a.spec,a.signers,a.checkout,a.output),indent=2))
