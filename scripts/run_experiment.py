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
    kind=config.get("kind")
    if kind not in {"forecast","same_mesh_q2_study"}:
        raise SystemExit("executable kinds are forecast and same_mesh_q2_study")

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

    ranks = int(config.get("execution", {}).get("mpi_ranks", 1))
    commands=[]
    if kind=="forecast":
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
        if ranks > 1:
            command = ["mpiexec", "-n", str(ranks), *command]
        commands.append(("forecast",command,run_dir))
    else:
        study=config["study"]
        common=["--cells",*map(str,study["cells"]),"--dt",str(study["dt"]),
            "--t-final",str(study["final_time"]),"--seed",str(study["seed"])]
        reference=run_dir/"reference"
        commands.append(("reference",[
            sys.executable,str(ROOT/"same_mesh_q2_study.py"),"prepare",*common,
            "--particles",str(study["monte_carlo_paths"]),"--mc-dt",str(study["mc_dt"]),
            "--output",str(reference),
        ],ROOT))
        initial_grid=reference/"initial_q1_subcell_averages.npy"
        particles=reference/"mc_final_particles.npy"
        for branch in study["branches"]:
            branch_dir=run_dir/str(branch["name"])
            branch_command=[
                sys.executable,str(ROOT/"same_mesh_q2_study.py"),"forecast",*common,
                "--branch",str(branch["name"]),"--degree",str(branch["degree"]),
                "--certificate-mode",str(branch.get("certificate_mode","fixed")),
                "--certificate-max-depth",str(study["certificate_max_depth"]),
                "--initial-grid",str(initial_grid),"--mc-particles",str(particles),
                "--bootstrap",str(study["bootstrap_replicates"]),"--output",str(branch_dir),
            ]
            branch_ranks=int(branch.get("mpi_ranks",ranks))
            if branch_ranks>1:
                branch_command=["mpiexec","-n",str(branch_ranks),*branch_command]
            commands.append((str(branch["name"]),branch_command,ROOT))

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
        "commands": [command for _,command,_ in commands],
    }
    (run_dir / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")

    returncode=0
    for label,command,cwd in commands:
        with (run_dir/f"{label}.log").open("w") as output:
            completed=subprocess.run(command,cwd=cwd,text=True,stdout=output,stderr=subprocess.STDOUT)
        if completed.returncode:
            returncode=completed.returncode
            break
    (run_dir / "status.json").write_text(
        json.dumps({"returncode":returncode,"passed":returncode==0},indent=2)
        + "\n"
    )
    print(run_dir)
    return returncode


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: run_experiment.py experiments/<name>.yaml")
    raise SystemExit(main(Path(sys.argv[1])))
