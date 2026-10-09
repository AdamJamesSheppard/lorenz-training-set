import json
from pathlib import Path
import subprocess
import sys


def test_unsigned_promotion_is_blocked_by_standalone_base_checker(tmp_path):
    repo=tmp_path/'candidate';(repo/'docs/operator_learning').mkdir(parents=True)
    gates=repo/'docs/operator_learning/gates.json'
    gates.write_text(json.dumps([dict(id='OL-G04_REFERENCE_TARGET_APPLICABILITY',decision_status='OPEN')]))
    def git(*args):
        return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.DEVNULL).decode().strip()
    git('init');git('add','.')
    git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid',
        '-c','commit.gpgsign=false','commit','-m','Synthetic base')
    base=git('rev-parse','HEAD')
    script=Path(__file__).resolve().parents[2]/'scientific_governance/check_transition.py'
    command=[sys.executable,'-I',str(script),'--base',base,'--root',str(repo)]
    assert subprocess.run(command,capture_output=True).returncode==0
    gates.write_text(json.dumps([dict(id='OL-G04_REFERENCE_TARGET_APPLICABILITY',decision_status='PASSED')]))
    result=subprocess.run(command,capture_output=True,text=True)
    assert result.returncode!=0
    assert 'trust roots absent' in result.stderr
