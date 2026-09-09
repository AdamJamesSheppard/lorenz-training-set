#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def package_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def git_text(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, text=True, capture_output=True
    ).stdout.strip()


def main(config_path: Path) -> int:
    source = config_path.resolve()
    config = yaml.safe_load(source.read_text())
    if config.get("kind") != "forecast":
        raise SystemExit("only kind=forecast is executable; research plans are specifications")

    run_id = str(config["id"])
    if not run_id or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for ch in run_id):
        raise SystemExit("experiment id must contain only letters, digits, '-' and '_'")
    created_at = datetime.now(timezone.utc)
    run_stamp = created_at.strftime("%Y%m%dT%H%M%SZ")
    run_dir = ROOT / "runs" / run_id / run_stamp
    if run_dir.exists():
        raise SystemExit(f"run instance already exists: {run_dir}")
    run_dir.mkdir(parents=True)
    shutil.copy2(source, run_dir / "config.yaml")

    solver = config["solver"]
    initial = config["initial_density"]
    command = [
        sys.executable,
        str(ROOT / "solver.py"),
        "--cells", *map(str, solver["cells"]),
        "--degree", str(solver["degree"]),
        "--dt", str(solver["dt"]),
        "--theta", str(solver["theta"]),
        "--t-final", str(solver["final_time"]),
        "--initialization", str(solver["initialization"]),
        "--quadrature-degree", str(solver["quadrature_degree"]),
        "--mean", *map(str, initial["mean"]),
        "--std", *map(str, initial["standard_deviation"]),
    ]
    ranks = int(config.get("execution", {}).get("mpi_ranks", 1))
    if ranks > 1:
        command = ["mpiexec", "-n", str(ranks), *command]

    provenance = {
        "created_utc": created_at.isoformat(),
        "config_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "git_commit": git_text("rev-parse", "HEAD"),
        "git_dirty": bool(git_text("status", "--porcelain")),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "packages": {
            name: package_version(name)
            for name in ("fenics-dolfinx", "fenics-basix", "fenics-ufl", "numpy", "mpi4py", "petsc4py")
        },
        "command": command,
    }
    (run_dir / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")

    with (run_dir / "stdout.log").open("w") as output:
        completed = subprocess.run(command, cwd=ROOT, text=True, stdout=output, stderr=subprocess.STDOUT)
    (run_dir / "status.json").write_text(
        json.dumps({"returncode": completed.returncode, "passed": completed.returncode == 0}, indent=2)
        + "\n"
    )
    print(run_dir)
    return completed.returncode


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: run_experiment.py experiments/<name>.yaml")
    raise SystemExit(main(Path(sys.argv[1])))
