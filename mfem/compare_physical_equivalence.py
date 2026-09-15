#!/usr/bin/env python3
"""Compare conservative physical exports from DOLFINx and MFEM."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def metrics(reference: np.ndarray, candidate: np.ndarray) -> dict[str, float]:
    difference = candidate - reference
    reference_l1 = float(np.abs(reference).sum())
    reference_linf = float(np.abs(reference).max())
    return {
        "absolute_l1_integral": float(np.abs(difference).sum()),
        "relative_l1": float(np.abs(difference).sum() / max(reference_l1, np.finfo(float).tiny)),
        "absolute_linf": float(np.abs(difference).max()),
        "relative_linf": float(np.abs(difference).max() / max(reference_linf, np.finfo(float).tiny)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_directory", type=Path)
    parser.add_argument("nx", type=int)
    parser.add_argument("ny", type=int)
    parser.add_argument("nz", type=int)
    args = parser.parse_args()
    shape = (args.nx * 3, args.ny * 3, args.nz * 3)
    dolfinx_directory = args.run_directory / "dolfinx"
    mfem_directory = args.run_directory / "mfem"
    export_pairs = [
        ("state", "state"), ("action", "operator_action"),
        ("cn", "raw_cn_step"), ("qp", "qp_corrected_cn_step")
    ]
    if (mfem_directory / "advection_0.bin").exists():
        export_pairs.extend([
            ("advection", "advection_action"),
            ("diffusion", "diffusion_action"),
            ("advection_volume", "advection_volume_action"),
            ("advection_face", "advection_face_action"),
        ])
    comparisons: dict[str, list[dict[str, float]]] = {
        report_name: [] for _, report_name in export_pairs
    }
    artifacts: dict[str, str] = {}
    for test in range(4):
        for exported, report_name in export_pairs:
            reference_path = dolfinx_directory / f"{exported}_{test}.npy"
            candidate_path = mfem_directory / f"{exported}_{test}.bin"
            reference = np.load(reference_path)
            candidate = np.fromfile(candidate_path, dtype=np.float64).reshape(shape)
            comparisons[report_name].append(metrics(reference, candidate))
            artifacts[str(reference_path.relative_to(args.run_directory))] = sha256(reference_path)
            artifacts[str(candidate_path.relative_to(args.run_directory))] = sha256(candidate_path)

    limits = {
        "state_relative_l1": 1.0e-12,
        "operator_action_relative_l1": 1.0e-7,
        "raw_cn_step_relative_l1": 1.0e-7,
        "qp_corrected_cn_step_relative_l1": 1.0e-7,
    }
    maxima = {
        name: max(item["relative_l1"] for item in values)
        for name, values in comparisons.items()
    }
    gates = {
        "physical_state_mapping": maxima["state"] <= limits["state_relative_l1"],
        "operator_action": maxima["operator_action"] <= limits["operator_action_relative_l1"],
        "raw_cn_step": maxima["raw_cn_step"] <= limits["raw_cn_step_relative_l1"],
        "qp_corrected_cn_step": (
            maxima["qp_corrected_cn_step"]
            <= limits["qp_corrected_cn_step_relative_l1"]
        ),
    }
    passed = all(gates.values())
    report = {
        "status": "PASSED_PREDECLARED_PHYSICAL_EQUIVALENCE_GATES" if passed else "FAILED_PREDECLARED_PHYSICAL_EQUIVALENCE_GATES",
        "scope": "uniform conforming Q2 physical-basis diagnostic",
        "mesh": [args.nx, args.ny, args.nz],
        "common_export_shape": list(shape),
        "common_export_semantics": "exact Q2 averages over aligned 3x3x3 subvoxels per FE cell",
        "test_fields": 4,
        "limits": limits,
        "maxima": maxima,
        "gates": gates,
        "comparisons": comparisons,
        "artifacts_sha256": artifacts,
        "next_action": (
            "run the production-mesh one-step gate, then authorize the full uniform mature equivalence forecast"
            if passed
            else "diagnose the first failed mapping/operator/CN stage; keep local-QP, mature forecast and AMR locked"
        ),
    }
    output = args.run_directory / "physical_equivalence_report.json"
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "maxima": maxima, "gates": gates}, indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
