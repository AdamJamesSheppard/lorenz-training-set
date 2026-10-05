"""Freeze a committed predeclaration; never automatically execute its command."""
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from operator_learning.governance import (  # noqa: E402
    check_repository, validate_predeclaration, validate_provenance,
)


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def prepare(source):
    source = source.resolve()
    config_bytes = source.read_bytes()
    config = json.loads(config_bytes)
    validate_predeclaration(config)
    errors = check_repository(ROOT)
    if errors:
        raise ValueError("governance inconsistency: " + "; ".join(errors))
    state = json.loads((ROOT / "docs/operator_learning/state.json").read_text())
    if state["gates"].get(config["gate_id"]) != "OPEN":
        raise ValueError("only the current OPEN gate may be prepared")
    relative = str(source.relative_to(ROOT))
    git("ls-files", "--error-unmatch", relative)
    if git("status", "--porcelain"):
        raise ValueError("commit predeclaration and all source changes before preparing")
    if subprocess.check_output(["git", "-C", str(ROOT), "show", f"HEAD:{relative}"]) != config_bytes:
        raise ValueError("config differs from predeclaration commit")
    for path, expected in config["inputs"].items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
            raise ValueError(f"input hash mismatch: {path}")
    record = dict(experiment_id=config["id"], gate_id=config["gate_id"], kind=config["kind"],
                  config_sha256=hashlib.sha256(config_bytes).hexdigest(),
                  git_commit=git("rev-parse", "HEAD"), git_dirty=False, git_status="",
                  command=config["command"], runtime_versions=config["runtime_versions"],
                  hardware=config["hardware"], seeds=config["seeds"],
                  input_hashes=config["inputs"], output_hashes={}, checkpoint_hashes={},
                  diagnostics={}, status="PREPARED_NOT_EXECUTED")
    validate_provenance(record)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out = ROOT / "runs/operator-learning" / config["id"] / stamp
    out.mkdir(parents=True, exist_ok=False)
    (out / "config.json").write_bytes(config_bytes)
    (out / "provenance.json").write_text(json.dumps(record, indent=2) + "\n")
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    print(prepare(args.config))
