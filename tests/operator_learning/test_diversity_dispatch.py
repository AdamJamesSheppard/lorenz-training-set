import copy
import json
from pathlib import Path

import pytest

from scripts.run_diversity_qualification import validate


def config():
    return json.loads(Path('experiments/operator_learning/OL-G03_diversity_qualification_v4.json').read_text())


def test_prospective_definition_validates():
    validate(config())


@pytest.mark.parametrize('key,value', [('windows', 3), ('shape', [30,36,36]),
                                      ('acceptance_rule', 'ALL_PAIRS_PASS')])
def test_frozen_design_cannot_change(key,value):
    c=copy.deepcopy(config())
    c[key]=value
    with pytest.raises(ValueError):
        validate(c)


def test_frozen_source_hashes_match():
    import hashlib
    for path,digest in config()['inputs'].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest
