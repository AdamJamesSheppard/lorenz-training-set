#!/usr/bin/env python3
"""Write a reproducibility manifest for numerical-closure evidence files."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import dolfinx
import basix
import ufl
import osqp
from mpi4py import MPI
from petsc4py import PETSc


ROOT = Path(__file__).resolve().parent
CODE_GLOBS = ("*.py", "lorenz_fpe/*.py", "tests/*.py")
EVIDENCE = (
    "POSITIVITY_AUDIT.md",
    "PRODUCTION_READINESS.md",
    "monte_carlo_uncertainty_20x24x24.json",
    "monte_carlo_fixed_dt_20x24x24.json",
    "monte_carlo_uncertainty_30x36x36.json",
    "crank_nicolson_mc_20x24x24.json",
    "separate_convergence_report.json",
    "limiter_impact_20x24x24.json",
    "mature_da_report.json",
    "mature_forecast_validation.json",
    "scaling_rank1.json", "scaling_rank2.json", "scaling_rank4.json", "scaling_rank8.json",
    "scaling_30_rank1.json", "scaling_30_rank8.json", "validation_report.json",
    "validation_repair_report.json", "boundary_flux_report.json", "higher_order_report.json",
    "q1_fine_bayesian_update_report.json", "q2_bayesian_update_subcell_report.json",
    "q2_common_law_subcell_monte_carlo.json", "independent_reference_refined_report.json",
    "mc_timestep_same_initial_law.json", "mature_da_projected_report.json",
    "scaling_q2_20_rank1.json", "scaling_q2_20_rank8.json",
    "METHOD_SELECTION_REPORT.md", "method_selection_report.json",
    "same_mesh_q2_falsification_report.json", "same_mesh_q2_corrected_report.json",
    "unlimited_q2_timestep_report.json", "unlimited_q2_crank_nicolson_report.json",
    "corrected_q2_crank_nicolson_report.json",
    "local_q2_positivity_projection_report.json",
    "local_q2_projection_performance_report.json",
    "local_q2_optimizer_validation_report.json",
    "local_q2_dynamic_projection_report.json",
    "local_q2_tight_refinement_report.json",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_revision() -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
            text=True, capture_output=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def extract_configuration(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    keys = ("configuration", "config", "particles", "mpi_ranks", "cells", "dt", "seed")
    return {key: data[key] for key in keys if key in data}


def command_output(command: list[str]) -> str | None:
    try:
        return subprocess.run(command,check=True,text=True,capture_output=True).stdout.strip() or None
    except (OSError,subprocess.CalledProcessError):
        return None


def main() -> None:
    code = sorted({p for pattern in CODE_GLOBS for p in ROOT.glob(pattern) if p.is_file()})
    evidence = [ROOT / name for name in EVIDENCE if (ROOT / name).is_file()]
    current_decision = json.loads(
        (ROOT / "method_selection_report.json").read_text()
    )["classification"]
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "decision": current_decision,
        "workspace": str(ROOT),
        "git_revision": git_revision(),
        "version_fallback": "SHA-256 file hashes are authoritative when git_revision is null.",
        "software": {
            "python": sys.version,
            "platform": platform.platform(),
            "dolfinx": dolfinx.__version__,
            "basix": basix.__version__,
            "ufl": ufl.__version__,
            "petsc": ".".join(map(str, PETSc.Sys.getVersion())),
            "osqp": osqp.__version__,
            "mpi_library": MPI.Get_library_version().strip(),
            "manifest_mpi_size": MPI.COMM_WORLD.size,
            "cpu": command_output(["lscpu"]),
            "gpu": command_output(["nvidia-smi","--query-gpu=name,memory.total","--format=csv,noheader"]),
        },
        "code_sha256": {str(path.relative_to(ROOT)): sha256(path) for path in code},
        "evidence": {
            str(path.relative_to(ROOT)): {
                "sha256": sha256(path),
                "configuration": extract_configuration(path),
            }
            for path in evidence
        },
        "common_model": {
            "lorenz": {"sigma": 10.0, "rho": 28.0, "beta": 8.0 / 3.0},
            "B": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
            "domain": [[-30.0, 30.0], [-40.0, 40.0], [-10.0, 70.0]],
            "space": "discontinuous tensor-product Q1 baseline and experimental Q2 on affine hexahedra",
            "fluxes": "upwind advection; full-tensor SIPG diffusion",
            "time": "theta method; theta=1 unless evidence configuration says otherwise",
            "limiter": "global KKT cell-average projection plus Bernstein scaling (Q1 whole cell; Q2 on 2x2x2 control subcells)",
            "recommended_export_subcells_per_axis": {"Q1":2,"Q2":3},
        },
        "principal_mc_seeds": [20260908,20260909,20260910],
        "mature_da_seed": 71023,
    }
    (ROOT / "experiment_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
