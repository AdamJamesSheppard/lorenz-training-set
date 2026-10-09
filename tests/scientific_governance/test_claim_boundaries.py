import json
from pathlib import Path


def test_every_gate_has_three_distinct_scientific_propositions():
    root=Path(__file__).resolve().parents[2]
    gates=json.loads((root/'docs/operator_learning/gates.json').read_text())
    claims=json.loads((root/'scientific_governance/claim_boundaries.json').read_text())
    assert set(claims)=={g['id'] for g in gates}
    for record in claims.values():
        assert set(record)=={'demonstrated','not_demonstrated','advances_goal'}
        assert all(isinstance(x,str) and x.strip() for x in record.values())
        assert len(set(record.values()))==3
