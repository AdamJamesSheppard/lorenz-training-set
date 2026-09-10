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
import numpy as np


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
            branch_dt=branch.get("dt",study["dt"])
            branch_common=["--cells",*map(str,study["cells"]),"--dt",str(branch_dt),
                "--t-final",str(study["final_time"]),"--seed",str(study["seed"])]
            branch_command=[
                sys.executable,str(ROOT/"same_mesh_q2_study.py"),"forecast",*branch_common,
                "--branch",str(branch["name"]),"--degree",str(branch["degree"]),
                "--certificate-mode",str(branch.get("certificate_mode","fixed")),
                "--certificate-max-depth",str(study["certificate_max_depth"]),
                "--initial-grid",str(initial_grid),"--mc-particles",str(particles),
                "--bootstrap",str(study["bootstrap_replicates"]),"--output",str(branch_dir),
            ]
            if not branch.get("apply_positivity",True):
                branch_command.append("--disable-positivity")
            if not branch.get("archive_raw",True):
                branch_command.append("--no-raw-archive")
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
    if returncode == 0 and kind == "same_mesh_q2_study":
        pairwise=[]
        for specification in study.get("pairwise_comparisons",[]):
            baseline=run_dir/str(specification["baseline"])
            challenger=run_dir/str(specification["challenger"])
            a=np.load(baseline/"final_q2_subcell_averages.npy")
            b=np.load(challenger/"final_q2_subcell_averages.npy")
            if a.shape != b.shape:
                raise ValueError("pairwise comparison arrays must have the same shape")
            bounds=study.get("bounds",[[-30.0,30.0],[-40.0,40.0],[-10.0,70.0]])
            volume=float(np.prod([float(hi)-float(lo) for lo,hi in bounds]))
            density_l1_lower_bound=float(np.abs(a-b).sum()*volume/a.size)
            a_report=json.loads((baseline/"report.json").read_text())
            b_report=json.loads((challenger/"report.json").read_text())
            a_error=float(a_report["comparisons_to_common_mc"]["final"]
                          ["covariance_accuracy"]["normalized_frobenius_error"])
            b_error=float(b_report["comparisons_to_common_mc"]["final"]
                          ["covariance_accuracy"]["normalized_frobenius_error"])
            limits=specification.get("limits",{})
            item={
                "name":str(specification["name"]),
                "baseline":str(specification["baseline"]),
                "challenger":str(specification["challenger"]),
                "subcell_average_l1_lower_bound":density_l1_lower_bound,
                "normalized_covariance_error_change":abs(b_error-a_error),
                "limits":limits,
            }
            item["passes"]={
                "l1":density_l1_lower_bound <= float(limits.get("l1",np.inf)),
                "covariance":abs(b_error-a_error) <= float(
                    limits.get("covariance_error_change",np.inf)
                ),
            }
            pairwise.append(item)
        if pairwise:
            (run_dir/"pairwise_comparisons.json").write_text(
                json.dumps(pairwise,indent=2)+"\n"
            )
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
