import hashlib
import json

import pytest
from scientific_governance.archive import export


def test_archive_is_complete_and_refuses_overwrite(tmp_path):
    src=tmp_path/'source';src.mkdir();(src/'data').write_bytes(b'evidence')
    (src/'seal.json').write_text(json.dumps({'data':hashlib.sha256(b'evidence').hexdigest()}))
    dst=tmp_path/'archive'
    assert export(src,dst)['security_status']=='LOCAL_COPY_ONLY_NOT_INDEPENDENT_IMMUTABLE_STORAGE'
    assert (dst/'data').read_bytes()==b'evidence'
    with pytest.raises(FileExistsError):export(src,dst)


def test_bad_seal_rejected_before_archive_created(tmp_path):
    src=tmp_path/'source';src.mkdir();(src/'data').write_bytes(b'altered')
    (src/'seal.json').write_text(json.dumps({'data':'a'*64}))
    dst=tmp_path/'archive'
    with pytest.raises(ValueError):export(src,dst)
    assert not dst.exists()


def test_parent_symlink_escape_rejected(tmp_path):
    src=tmp_path/'source';src.mkdir()
    outside=tmp_path/'outside';outside.mkdir();(outside/'data').write_bytes(b'private')
    (src/'linked').symlink_to(outside,target_is_directory=True)
    (src/'seal.json').write_text(json.dumps({'linked/data':hashlib.sha256(b'private').hexdigest()}))
    with pytest.raises(ValueError,match='Unsafe'):
        export(src,tmp_path/'archive')


def test_changed_source_during_copy_rejected(tmp_path,monkeypatch):
    import scientific_governance.archive as module
    src=tmp_path/'source';src.mkdir();(src/'data').write_bytes(b'evidence')
    (src/'seal.json').write_text(json.dumps({'data':hashlib.sha256(b'evidence').hexdigest()}))
    original=module.shutil.copyfileobj
    def racing_copy(inp,out):
        (src/'data').write_bytes(b'changed!')
        return original(inp,out)
    monkeypatch.setattr(module.shutil,'copyfileobj',racing_copy)
    with pytest.raises(ValueError,match='copy mismatch'):
        export(src,tmp_path/'archive')
