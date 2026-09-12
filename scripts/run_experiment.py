#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
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
    if kind not in {
        "forecast", "same_mesh_q2_study", "local_projection_study",
        "local_projection_optimizer_validation",
    }:
        raise SystemExit(
            "unsupported executable experiment kind"
        )

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
    numerical_threads = int(config.get("execution", {}).get("numerical_threads", 0))
    child_environment = os.environ.copy()
    if numerical_threads > 0:
        for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
            child_environment[name] = str(numerical_threads)
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
    elif kind == "same_mesh_q2_study":
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
                "--theta",str(branch.get("theta",1.0)),
                "--ksp-rtol",str(branch.get("ksp_rtol",study.get("ksp_rtol",1.0e-10))),
                "--ksp-atol",str(branch.get("ksp_atol",study.get("ksp_atol",1.0e-13))),
                "--certificate-mode",str(branch.get("certificate_mode","fixed")),
                "--certificate-max-depth",str(study["certificate_max_depth"]),
                "--initial-grid",str(initial_grid),"--mc-particles",str(particles),
                "--bootstrap",str(study["bootstrap_replicates"]),"--output",str(branch_dir),
            ]
            if not branch.get("apply_positivity",True):
                branch_command.append("--disable-positivity")
            if branch.get("positivity_method") == "local_qp":
                branch_command.extend([
                    "--local-projection",
                    "--local-optimizer-backend", str(branch.get("optimizer_backend", "osqp")),
                    "--local-optimizer-ftol", str(branch.get("optimizer_ftol", 1.0e-10)),
                    "--local-maximum-iterations", str(branch.get("maximum_iterations", 10_000)),
                ])
            if not branch.get("archive_raw",True):
                branch_command.append("--no-raw-archive")
            branch_ranks=int(branch.get("mpi_ranks",ranks))
            if branch_ranks>1:
                branch_command=["mpiexec","-n",str(branch_ranks),*branch_command]
            commands.append((str(branch["name"]),branch_command,ROOT))
    elif kind == "local_projection_study":
        study = config["study"]
        for item in study["inputs"]:
            item_output = run_dir / str(item["name"])
            command = [
                sys.executable,
                str(ROOT / "local_projection_study.py"),
                "--input-subcells", str(ROOT / str(item["input_subcells"])),
                "--mc-particles", str(ROOT / str(study["mc_particles"])),
                "--output", str(item_output),
                "--cells", *map(str, study["cells"]),
                "--dt", str(item["dt"]),
                "--final-time", str(study["final_time"]),
                "--certificate-max-depth", str(study["certificate_max_depth"]),
                "--optimizer-ftol", str(study["optimizer_ftol"]),
                "--optimizer-backend", str(study.get("optimizer_backend", "osqp")),
                "--feasibility-tolerance", str(study["feasibility_tolerance"]),
                "--normalized-positivity-margin", str(study["normalized_positivity_margin"]),
                "--maximum-iterations", str(study["maximum_iterations"]),
                "--bootstrap", str(study["bootstrap_replicates"]),
                "--seed", str(study["seed"]),
            ]
            if ranks > 1:
                command = ["mpiexec", "-n", str(ranks), *command]
            commands.append((str(item["name"]), command, ROOT))
    else:
        study = config["study"]
        command = [
            sys.executable, str(ROOT / "local_projection_optimizer_study.py"),
            "--input-subcells", *[str(ROOT / str(path)) for path in study["input_subcells"]],
            "--output", str(run_dir / "validation"),
            "--cells", *map(str, study["cells"]),
            "--dt", str(study["dt"]),
            "--certificate-max-depth", str(study["certificate_max_depth"]),
            "--optimizer-ftol", str(study["optimizer_ftol"]),
            "--oracle-ftol", str(study["oracle_ftol"]),
            "--feasibility-tolerance", str(study["feasibility_tolerance"]),
            "--osqp-maximum-iterations", str(study["osqp_maximum_iterations"]),
            "--oracle-maximum-iterations", str(study["oracle_maximum_iterations"]),
            "--random-problems", str(study["random_problems"]),
            "--seed", str(study["seed"]),
            "--objective-agreement-tolerance", str(study["objective_agreement_tolerance"]),
            "--coefficient-agreement-tolerance", str(study["coefficient_agreement_tolerance"]),
            "--minimum-speedup", str(study["minimum_speedup"]),
        ]
        commands.append(("validation", command, ROOT))

    provenance = {
        "created_utc": created_at.isoformat(),
        "config_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "git_commit": git_text("rev-parse", "HEAD"),
        "git_dirty": bool(git_text("status", "--porcelain")),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "packages": {
            name: package_version(name)
            for name in (
                "fenics-dolfinx", "fenics-basix", "fenics-ufl", "numpy",
                "mpi4py", "petsc4py", "osqp",
            )
        },
        "commands": [command for _,command,_ in commands],
        "numerical_threads_per_rank": numerical_threads or None,
    }
    (run_dir / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")

    returncode=0
    for label,command,cwd in commands:
        with (run_dir/f"{label}.log").open("w") as output:
            completed=subprocess.run(
                command, cwd=cwd, text=True, stdout=output,
                stderr=subprocess.STDOUT, env=child_environment,
            )
        if completed.returncode:
            returncode=completed.returncode
            break
    if returncode == 0 and kind == "same_mesh_q2_study":
        pairwise=[]
        observed_order = None
        observed_orders = []
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
        if len(pairwise) >= 2:
            for first_item, second_item in zip(pairwise[:-1], pairwise[1:]):
                first = float(first_item["subcell_average_l1_lower_bound"])
                second = float(second_item["subcell_average_l1_lower_bound"])
                value = (
                    float(np.log2(first / second))
                    if first > 0.0 and second > 0.0 else None
                )
                observed_orders.append({
                    "first_comparison": first_item["name"],
                    "second_comparison": second_item["name"],
                    "l1_ratio": first / second if second > 0.0 else None,
                    "observed_order": value,
                })
            observed_order = observed_orders[-1]["observed_order"]
            (run_dir / "observed_timestep_order.json").write_text(
                json.dumps({
                    **observed_orders[-1],
                    "observed_order": observed_order,
                    "all_consecutive_orders": observed_orders,
                    "interpretation": "Consecutive-level numerical diagnostic; no asymptotic-regime proof.",
                }, indent=2) + "\n"
            )
        decision_specification = config.get("scientific_decision")
        if decision_specification is not None:
            branch_results = []
            for branch in study["branches"]:
                branch_name = str(branch["name"])
                branch_report = json.loads((run_dir / branch_name / "report.json").read_text())
                steps = branch_report["limiter_steps"]
                maximum_step_mass_change = max(
                    (abs(float(step["mass_after"]) - float(step["mass_before"])) for step in steps),
                    default=0.0,
                )
                maximum_step_negative_mass = max(
                    (float(step["final_quadrature_negative_mass"]) for step in steps),
                    default=0.0,
                )
                final_diagnostics = branch_report["final_stage_diagnostics"]["final"]
                covariance = branch_report["comparisons_to_common_mc"]["final"][
                    "covariance_accuracy"
                ]
                branch_gates = {
                    "every_step_whole_cell_positive": all(
                        bool(step["whole_cell_positivity_certified"]) for step in steps
                    ),
                    "maximum_step_mass_change": maximum_step_mass_change
                    <= float(decision_specification["maximum_step_mass_change"]),
                    "maximum_negative_mass": max(
                        maximum_step_negative_mass,
                        float(final_diagnostics["negative_mass"]),
                    ) <= float(decision_specification["maximum_negative_mass"]),
                    "absolute_mass_error": abs(float(final_diagnostics["mass"]) - 1.0)
                    <= float(decision_specification["maximum_absolute_mass_error"]),
                    "covariance_error_to_mc_p95_ratio": float(
                        covariance["pde_error_to_mc_noise_p95_ratio"]
                    ) <= float(
                        decision_specification["maximum_covariance_error_to_mc_p95_ratio"]
                    ),
                }
                branch_results.append({
                    "branch": branch_name,
                    "measured": {
                        "maximum_step_mass_change": maximum_step_mass_change,
                        "maximum_step_negative_mass": maximum_step_negative_mass,
                        "final_negative_mass": float(final_diagnostics["negative_mass"]),
                        "absolute_mass_error": abs(float(final_diagnostics["mass"]) - 1.0),
                        "covariance_error_to_mc_p95_ratio": float(
                            covariance["pde_error_to_mc_noise_p95_ratio"]
                        ),
                    },
                    "gates": branch_gates,
                    "passes": all(branch_gates.values()),
                })
            pairwise_gates = {
                item["name"]: (
                    float(item["subcell_average_l1_lower_bound"])
                    <= float(decision_specification["maximum_adjacent_density_l1"])
                    and all(bool(value) for value in item["passes"].values())
                )
                for item in pairwise
            }
            positive_order_required = bool(
                decision_specification.get("require_positive_observed_order", False)
            )
            order_gate = (
                not positive_order_required
                or (observed_order is not None and observed_order > 0.0)
            )
            all_passed = (
                all(item["passes"] for item in branch_results)
                and all(pairwise_gates.values())
                and order_gate
            )
            scientific_decision = {
                "classification": (
                    "PASSED_PREDECLARED_DYNAMIC_GATES"
                    if all_passed else "FAILED_PREDECLARED_DYNAMIC_GATES"
                ),
                "all_gates_passed": all_passed,
                "branch_results": branch_results,
                "pairwise_density_gates": pairwise_gates,
                "observed_timestep_order": observed_order,
                "all_consecutive_observed_orders": observed_orders,
                "positive_observed_order_gate": order_gate,
                "thresholds": decision_specification,
                "dataset_generation_authorized": False,
                "interpretation": (
                    "Startup-state dynamic diagnostic only; passing advances the candidate to "
                    "spatial, full-SPD, and mature-state certification."
                ),
            }
            (run_dir / "scientific_decision.json").write_text(
                json.dumps(scientific_decision, indent=2) + "\n"
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
