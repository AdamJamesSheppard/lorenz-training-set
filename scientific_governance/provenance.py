"""Complete committed project-tree/environment inventory, not selective imports."""
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys


def inventory(root):
    root=Path(root)
    def git(*args):
        return subprocess.check_output(['git','-C',str(root),*args])
    names=git('ls-files','-z').decode().split('\0')
    files={}
    for name in names:
        if not name:
            continue
        path=root/name
        if path.is_symlink() or not path.is_file():
            raise ValueError('Uninventoried symlink/submodule/missing path: '+name)
        files[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    return dict(commit=git('rev-parse','HEAD').decode().strip(),
                dirty=bool(git('status','--porcelain')),files=files,
                source_tree_sha256=hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest(),
                python=platform.python_version(),platform=platform.platform(),
                packages=subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True).splitlines())
