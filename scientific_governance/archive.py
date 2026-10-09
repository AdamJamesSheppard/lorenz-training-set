"""Verified write-once local export. External WORM/ACL enforcement is required."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def export(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if destination.is_relative_to(source) or source.is_relative_to(destination):
        raise ValueError('Archive must be a separate location')
    if (source/'seal.json').is_symlink():
        raise ValueError('Linked seal prohibited')
    seal_bytes=(source/'seal.json').read_bytes()
    seal=json.loads(seal_bytes)
    if not isinstance(seal,dict) or not seal or 'seal.json' in seal:
        raise ValueError('Invalid artifact seal')
    for name,digest in seal.items():
        p=Path(name)
        if (p.is_absolute() or '..' in p.parts or (source/p).is_symlink()
                or not (source/p).resolve().is_relative_to(source)):
            raise ValueError('Unsafe sealed path')
        if hashlib.sha256((source/p).read_bytes()).hexdigest()!=digest:
            raise ValueError('Artifact mismatch: '+name)
    destination.mkdir(parents=True,exist_ok=False)
    # Never overwrite or delete an existing archive, even after a partial failure.
    for name in [*seal,'seal.json']:
        target=destination/name
        target.parent.mkdir(parents=True,exist_ok=True)
        if name=='seal.json':
            with target.open('xb') as out:
                out.write(seal_bytes)
        else:
            with (source/name).open('rb') as inp,target.open('xb') as out:
                shutil.copyfileobj(inp,out)
        expected=hashlib.sha256(seal_bytes).hexdigest() if name=='seal.json' else seal[name]
        if hashlib.sha256(target.read_bytes()).hexdigest()!=expected:
            raise ValueError('Archive copy mismatch')
    return dict(path=str(destination),artifacts=len(seal),
                seal_sha256=hashlib.sha256((destination/'seal.json').read_bytes()).hexdigest(),
                security_status='LOCAL_COPY_ONLY_NOT_INDEPENDENT_IMMUTABLE_STORAGE')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path);p.add_argument('destination',type=Path)
    a=p.parse_args();print(json.dumps(export(a.source,a.destination),indent=2))
