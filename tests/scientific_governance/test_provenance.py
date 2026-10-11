import hashlib
import subprocess

from scientific_governance.provenance import inventory


def test_inventory_covers_transitive_modules_and_detects_changes(tmp_path):
    def git(*args):
        subprocess.run(['git','-C',str(tmp_path),*args],check=True,capture_output=True)
    git('init')
    (tmp_path/'main.py').write_text('import helper\n')
    (tmp_path/'helper.py').write_text('import nested\n')
    (tmp_path/'nested.py').write_text('VALUE=1\n')
    git('add','.')
    git('-c','user.name=Test Fixture','-c','user.email=fixture@example.invalid',
        '-c','commit.gpgsign=false','commit','-m','Synthetic provenance fixture')
    first=inventory(tmp_path)
    assert not first['dirty']
    assert set(first['files'])=={'main.py','helper.py','nested.py'}
    assert first['files']['nested.py']==hashlib.sha256(b'VALUE=1\n').hexdigest()
    (tmp_path/'nested.py').write_text('VALUE=2\n')
    second=inventory(tmp_path)
    assert second['dirty']
    assert second['source_tree_sha256']!=first['source_tree_sha256']
