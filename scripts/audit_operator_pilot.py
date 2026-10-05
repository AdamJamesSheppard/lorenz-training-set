"""Retrospective six-law audit; source run is read-only, output must be NEW."""
import argparse
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from operator_learning.numerics import (  # noqa: E402
    boundary_mass, density_l1, nearest_target, normalized_probability,
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(source, output):
    import numpy as np
    import torch

    sys.path.insert(0, str(ROOT / "scripts"))
    from train_neural_pilot import Operator, metrics

    source, output = source.resolve(), output.resolve()
    if output.exists() or output == source or source in output.parents:
        raise ValueError("audit output must be new and outside historical evidence")
    manifest = json.loads((source / "manifest.json").read_text())
    hashes = {}
    for item in manifest:
        path = source / item["path"]
        hashes[item["path"]] = sha(path)
        if hashes[item["path"]] != item["sha256"]:
            raise ValueError("historical pair hash mismatch")
    original_hashes = json.loads((source / "input_sha256.json").read_text())
    trainer = ROOT / "scripts/train_neural_pilot.py"
    if sha(trainer) != original_hashes[str(trainer)]:
        raise ValueError("use original hashed training implementation for checkpoint audit")
    for name in ("config.json", "manifest.json", "evaluation.json", "training_history.json",
                 "training_device.json", "best_model.pt", "input_sha256.json", "git_commit.txt",
                 "git_status.txt", "status.json", "training_packages.txt"):
        hashes[name] = sha(source / name)
    config = json.loads((source / "config.json").read_text())
    recorded = json.loads((source / "evaluation.json").read_text())
    history = json.loads((source / "training_history.json").read_text())
    if len(manifest) != 6 or config["splits"] != [e["split"] for e in manifest]:
        raise ValueError("historical population/splits mismatch")
    summaries = []
    arrays = []
    for item in manifest:
        law = item["law"]
        for name in ("mfem/mature_summary.json", "acceptance.json", "prior_design.json",
                     "command.json", "prior_environment.json"):
            path = source / f"law{law}" / name
            hashes[str(path.relative_to(source))] = sha(path)
        summary = json.loads((source / f"law{law}/mfem/mature_summary.json").read_text())
        acceptance = json.loads((source / f"law{law}/acceptance.json").read_text())
        summaries.append(dict(law=law, summary=summary, acceptance=acceptance))
        with np.load(source / item["path"]) as pair:
            arrays.append({k: pair[k].copy() for k in ("initial", "final")})
    torch.set_num_threads(2)
    model = Operator().cpu().eval()
    checkpoint = torch.load(source / "best_model.pt", weights_only=True, map_location="cpu")
    model.load_state_dict(checkpoint["model"])
    inputs = [a["initial"].astype(float) for a in arrays]
    volume = 384000 / inputs[0].size
    distances = [[density_l1(a, b, volume) for b in inputs] for a in inputs]
    diagnostics = []
    with torch.no_grad():
        for index in (4, 5):
            x = torch.from_numpy(arrays[index]["initial"] * 384000)[None, None]
            y = torch.from_numpy(arrays[index]["final"] * 384000)[None, None]
            pred = model(x)
            p = normalized_probability(pred.numpy()[0, 0])
            q = normalized_probability(y.numpy()[0, 0])
            coordinates = [np.linspace(lo+(hi-lo)/(2*n), hi-(hi-lo)/(2*n), n)
                           for lo, hi, n in zip((-30, -40, -10), (30, 40, 70), p.shape)]
            def means(field):
                return [float((field * coordinates[k].reshape(
                    tuple(n if d == k else 1 for d, n in enumerate(field.shape)))).sum())
                    for k in range(3)]
            neighbor, target = nearest_target(inputs[:4], [a["final"] for a in arrays[:4]],
                                              inputs[index], volume)
            diagnostics.append(dict(law=index, split=manifest[index]["split"],
                cpu_metrics=metrics(pred, y),
                nearest_training_input_l1=min(distances[index][:4]),
                nearest_training_law=neighbor,
                nearest_target_l1=density_l1(target, arrays[index]["final"], volume),
                boundary_definition="outer four voxels of 60x72x72 learning grid, union",
                neural_boundary_probability=boundary_mass(p, 4),
                target_boundary_probability=boundary_mass(q, 4),
                neural_probability_on_recorded_target_zeros=float(p[q == 0].sum()),
                lobe_partition="x>0 (diagnostic convention)",
                neural_positive_x_probability=float(p[30:].sum()),
                target_positive_x_probability=float(q[30:].sum()),
                neural_mean=means(p), target_mean=means(q)))
    report = dict(schema_version=1, kind="RETROSPECTIVE_HISTORICAL_AUDIT_NOT_GATE_PASS",
        source_run=str(source.relative_to(ROOT)),
        source_commit=(source / "git_commit.txt").read_text().strip(),
        original_dirty_status=(source / "git_status.txt").read_text(),
        original_status=json.loads((source / "status.json").read_text()),
        classification="Data-generation and GPU-training feasibility demonstrated; restricted density-learning improvement observed; statistical fidelity and surrogate qualification open",
        original_test_inspected_date="2026-10-05",
        future_role="development if diagnostics guide tuning; require new untouched evaluation",
        pair_hashes_verified=True, historical_artifact_sha256=hashes,
        recorded_evaluation=recorded, law_summaries=summaries,
        summed_forecast_hours=sum(s["summary"]["runtime_seconds"] for s in summaries)/3600,
        history_summary=dict(epochs=len(history), first=history[0], last=history[-1],
                             best_validation=min(history, key=lambda row: row["validation"]),
                             checkpoint_epoch=checkpoint["epoch"]),
        initial_pairwise_l1=distances, additional_cpu_diagnostics=diagnostics,
        limitations=["Retrospective output hashing, not original sealing",
                     "Learning boundary region wider than original fine-grid acceptance layer",
                     "Exactly zero target voxels are representation-dependent",
                     "No new target, retraining, continuum proof or OL gate pass"],
        audit_provenance=dict(git_commit=subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip(),
            git_status=subprocess.check_output(["git", "-C", str(ROOT), "status", "--short"],
                                               text=True),
            command=sys.argv, python=platform.python_version(), numpy=np.__version__,
            torch=torch.__version__, device="cpu", script_sha256=sha(Path(__file__)),
            trainer_sha256=sha(trainer)))
    output.mkdir(parents=True, exist_ok=False)
    out = output / "audit.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    (output / "seal.json").write_text(json.dumps({"audit.json": sha(out)}, indent=2) + "\n")
    print(json.dumps(dict(output=str(out), sha256=sha(out), qualification=False)))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    audit(args.source, args.output)
