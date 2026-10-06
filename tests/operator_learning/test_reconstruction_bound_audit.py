import hashlib
import json

import numpy as np
import pytest

from scripts import audit_reconstruction_bounds as module


def test_aligned_times_and_seal_verification(tmp_path, monkeypatch):
    source = tmp_path / 'source'
    source.mkdir()
    # Synthetic fixture tests indexing only, never scientific Lorenz evidence.
    fine = np.zeros((20000, 3))
    fine[::2, 0] = .1
    np.savez(source / 'seed1_paths.npz', dt0005=fine, dt001=fine[1::2])
    (source / 'config.json').write_text(json.dumps({
        'physical_widths': [1, 1, 1], 'seeds': {'trajectory': [1]}}))
    seal = {name: hashlib.sha256((source/name).read_bytes()).hexdigest()
            for name in ('config.json', 'seed1_paths.npz')}
    (source / 'seal.json').write_text(json.dumps(seal))
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    monkeypatch.setattr(module.subprocess, 'check_output', lambda *a, **k: '')
    monkeypatch.setattr(module, 'sha', lambda p: (
        hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else '0'*64))
    report = module.audit(source)
    assert report['worst_aligned_integration_l1_upper'] == 0
    assert report['worst_sampling_l1_upper']['5000'] > 0
    assert report['gate_status'] == 'OPEN'
    assert report['scientific_qualification'] is False
    assert report['exclusions'] == []
    (source / 'config.json').write_text('{}')
    with pytest.raises(ValueError, match='seal mismatch'):
        module.audit(source)
