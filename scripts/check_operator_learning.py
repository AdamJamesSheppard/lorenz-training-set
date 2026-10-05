"""Fast governance checks only; no solver, Torch, training or ignored evidence."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from operator_learning.governance import check_repository  # noqa: E402

if __name__ == "__main__":
    errors = check_repository(ROOT)
    for error in errors:
        print(error)
    print("OPERATOR GOVERNANCE: " + ("FAIL" if errors else "PASS (not scientific qualification)"))
    raise SystemExit(bool(errors))
