#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lorenz_fpe import Lorenz63Model  # noqa: E402


def main() -> int:
    decision = json.loads((ROOT / "method_selection_report.json").read_text())
    boundary = json.loads((ROOT / "boundary_flux_report.json").read_text())
    diffusion = Lorenz63Model().diffusion

    mass_errors = [abs(float(row["mass_error"])) for row in boundary["rows"]]
    l1_errors = [float(row["l1_error"]) for row in boundary["rows"]]
    observed_orders = [
        np.log(l1_errors[i - 1] / l1_errors[i])
        / np.log(
            boundary["rows"][i]["cells_per_axis"]
            / boundary["rows"][i - 1]["cells_per_axis"]
        )
        for i in range(1, len(l1_errors))
    ]

    checks = {
        "diffusion_symmetric": bool(np.allclose(diffusion, diffusion.T, atol=1e-14)),
        "diffusion_positive_semidefinite": bool(np.linalg.eigvalsh(diffusion).min() >= -1e-14),
        "boundary_mass_error_ok": bool(max(mass_errors) <= 1e-9),
        "boundary_l1_decreases": bool(
            all(b < a for a, b in zip(l1_errors, l1_errors[1:]))
        ),
        "boundary_order_ok": bool(min(observed_orders) >= 1.9),
        "dataset_block_consistent": (
            decision["classification"] == "INSUFFICIENT_EVIDENCE"
            and decision["large_neural_operator_dataset"] == "NO"
        ),
    }
    result = {
        "passed": all(checks.values()),
        "method_certified": False,
        "classification": decision["classification"],
        "checks": checks,
        "metrics": {
            "diffusion_eigenvalues": np.linalg.eigvalsh(diffusion).tolist(),
            "maximum_boundary_mass_error": max(mass_errors),
            "minimum_observed_boundary_l1_order": min(observed_orders),
            "best_same_law_covariance_error": decision["same_initial_law_forecast"][
                "normalized_covariance_error"
            ],
            "covariance_error_to_mc_noise_ratio": decision["same_initial_law_forecast"][
                "ratio"
            ],
        },
        "interpretation": (
            "The tested invariants and evidence consistency pass. This does not certify "
            "a production forecast method; the method-selection state remains insufficient evidence."
        ),
    }

    output = ROOT / "results" / "math_checks.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
