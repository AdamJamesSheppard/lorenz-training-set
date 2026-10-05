"""Dependency-free canonical-state, predeclaration and provenance validation."""
import json
import re
from pathlib import Path

UNDECLARED = "TO_BE_PREDECLARED_BEFORE_RUN"
GATE_FIELDS = {
    "id", "question", "scientific_motivation", "prerequisites",
    "frozen_experiment_definition", "evidence_required", "metrics",
    "predeclared_thresholds", "pass_condition", "failure_condition",
    "what_passing_unlocks", "what_failure_requires", "claims_permitted_after_pass",
    "claims_still_forbidden_after_pass", "relevant_assumptions", "experiment_config",
    "evidence_run", "decision_status", "adjudication",
}
GENERATOR_FIELDS = {
    "GENERATOR_ID", "probability_interpretation", "underlying_process_or_random_variable",
    "sampling_procedure", "conditioning_procedure", "density_reconstruction",
    "regularization", "parameters", "known_bias", "intended_scientific_role",
    "allowed_for_engineering_tests", "allowed_for_training", "allowed_for_validation",
    "allowed_for_final_evaluation", "representativeness_status",
}


def render_state(state):
    return ("# Operator-learning current state\n\n"
            "Updated: 2026-10-05. Canonical encoding: state.json; this exact mirror is checked.\n"
            "Historical interpretation: DECISIONS.md. FEM method status is separate.\n\n"
            "```json\n" + json.dumps(state, indent=2) + "\n```\n")


def render_gates(gates):
    header = ("# Operator-learning scientific gates\n\n"
              "Canonical schema: gates.json. This exact readable rendering is checked.\n"
              "All downstream qualification is blocked by G00. Cheap historical development\n"
              "studies do not pass gates. Unspecified thresholds remain non-executable.\n"
              "Each pass unlocks only the next gated study; DA/production need explicit approval.\n\n")
    sections = []
    for gate in gates:
        lines = [f"- **{key}**: {value if isinstance(value, str) else json.dumps(value)}"
                 for key, value in gate.items()]
        sections.append(f"## {gate['id']}\n\n" + "\n".join(lines))
    return header + "\n\n".join(sections) + "\n"


def validate_programme(state, gates, generators):
    errors = []
    ids = [g.get("id") for g in gates]
    if len(ids) != 18 or len(set(ids)) != 18:
        errors.append("exactly 18 unique ordered gates required")
    if set(state.get("gates", {})) != set(ids):
        errors.append("state gate IDs do not match catalogue")
    if state.get("programme") != "OPERATOR_LEARNING_QUALIFICATION":
        errors.append("wrong programme stage")
    unfinished = []
    for index, gate in enumerate(gates):
        if set(gate) != GATE_FIELDS:
            errors.append(f"gate {index}: incomplete schema")
        expected_prefix = f"OL-G{index:02d}_"
        if not str(gate.get("id", "")).startswith(expected_prefix):
            errors.append(f"gate {index}: order/ID mismatch")
        status = gate.get("decision_status")
        if status not in {"OPEN", "LOCKED", "PASSED", "FAILED"}:
            errors.append(f"gate {index}: invalid status")
        if state.get("gates", {}).get(gate.get("id")) != status:
            errors.append(f"gate {index}: status contradiction")
        prerequisites = ids[index-1:index] if index else []
        if gate.get("prerequisites") != prerequisites:
            errors.append(f"gate {index}: prerequisite chain mismatch")
        if index and any(state.get("gates", {}).get(p) != "PASSED" for p in prerequisites):
            if status != "LOCKED":
                errors.append(f"gate {index}: prerequisite not passed")
        if index == 0 and status == "LOCKED":
            errors.append("G00 must be open, failed or passed")
        if status == "PASSED":
            decision = gate.get("adjudication")
            needed = {"approver", "reviewer", "date", "config_sha256", "evidence_sha256",
                      "predeclaration_commit", "decision_record", "limitations"}
            if not isinstance(decision, dict) or not needed <= decision.keys():
                errors.append(f"gate {index}: passed without signed adjudication")
            elif any(not decision[key] for key in needed):
                errors.append(f"gate {index}: blank adjudication fields")
            else:
                for key, length in (("config_sha256", 64), ("evidence_sha256", 64),
                                    ("predeclaration_commit", 40)):
                    if not re.fullmatch(r"[0-9a-f]{" + str(length) + r"}", str(decision[key])):
                        errors.append(f"gate {index}: invalid adjudication {key}")
            if not gate.get("evidence_run") or UNDECLARED in str(gate.get("experiment_config")):
                errors.append(f"gate {index}: passed without experiment/evidence")
            if UNDECLARED in str(gate.get("predeclared_thresholds")):
                errors.append(f"gate {index}: passed with undeclared thresholds")
        else:
            unfinished.append(gate.get("id"))
    expected_next = unfinished[0] if unfinished else "SEPARATE_DA_PROGRAMME_APPROVAL"
    if state.get("next_required_gate") != expected_next:
        errors.append("NEXT_REQUIRED_GATE inconsistent")
    if unfinished and any(state.get(k) is not False for k in (
        "current_model_scientifically_qualified", "operator_surrogate_authorized_for_da",
        "operator_production_authorized",
    )):
        errors.append("authorization before qualification gates")
    for generator in generators:
        if set(generator) != GENERATOR_FIELDS:
            errors.append("generator schema incomplete")
        permissions = [k for k in GENERATOR_FIELDS if k.startswith("allowed_")]
        if any(type(generator.get(k)) is not bool for k in permissions):
            errors.append("generator permissions must be explicit booleans")
        if generator.get("representativeness_status") != "accepted_scoped":
            if any(generator.get(k) for k in permissions if k != "allowed_for_engineering_tests"):
                errors.append("unverified generator granted scientific dataset permission")
    return errors


def validate_predeclaration(config):
    needed = {"id", "gate_id", "kind", "status", "question", "hypotheses",
              "metrics", "thresholds", "seeds", "inputs", "command",
              "runtime_versions", "hardware", "required_evidence", "pass_consequences",
              "failure_consequences", "assumptions", "review_requirements"}
    if not needed <= config.keys():
        raise ValueError("incomplete executable predeclaration")
    if config["status"] != "PREDECLARED" or UNDECLARED in json.dumps(config):
        raise ValueError("draft/undeclared scientific experiments cannot execute")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", config["id"]):
        raise ValueError("unsafe experiment identifier")
    if not isinstance(config["inputs"], dict) or not isinstance(config["command"], list):
        raise ValueError("inputs must be path/hash mapping and command an argv list")
    if not config["command"] or not config["thresholds"]:
        raise ValueError("empty command or criteria")
    if any(not isinstance(arg, str) or not arg for arg in config["command"]):
        raise ValueError("argv must contain nonempty strings")
    if any(not re.fullmatch(r"[0-9a-f]{64}", str(h)) for h in config['inputs'].values()):
        raise ValueError("invalid input SHA-256")


def validate_provenance(record):
    needed = {"experiment_id", "gate_id", "kind", "config_sha256", "git_commit",
              "git_dirty", "git_status", "command", "runtime_versions", "hardware",
              "seeds", "input_hashes", "output_hashes", "checkpoint_hashes",
              "diagnostics", "status"}
    if not needed <= record.keys():
        raise ValueError("missing provenance fields")
    if not re.fullmatch(r"[0-9a-f]{40}", record["git_commit"]):
        raise ValueError("full Git commit required")
    if type(record["git_dirty"]) is not bool:
        raise ValueError("dirty flag must be boolean")
    for digest in [record["config_sha256"], *record["input_hashes"].values(),
                   *record["output_hashes"].values(), *record["checkpoint_hashes"].values()]:
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("invalid SHA-256")
    if record["status"] == "COMPLETED" and not record["output_hashes"]:
        raise ValueError("completed evidence must have output hashes")


def check_repository(root):
    root = Path(root)
    base = root / "docs/operator_learning"
    state = json.loads((base / "state.json").read_text())
    gates = json.loads((base / "gates.json").read_text())
    generators = json.loads((base / "generators.json").read_text())
    errors = validate_programme(state, gates, generators)
    for path, expected in [("PROJECT_STATE.md", render_state(state)),
                           ("GATES.md", render_gates(gates))]:
        if (base / path).read_text() != expected:
            errors.append(f"stale canonical mirror: {path}")
    for path in ("README.md", "docs/PROJECT_STATE.md", "docs/RESEARCH_DIRECTIONS.md"):
        if "docs/operator_learning" not in (root / path).read_text():
            errors.append(f"missing OL authority pointer: {path}")
    top_state = (root / "docs/PROJECT_STATE.md").read_text()
    if f"NEXT_REQUIRED_GATE = {state['next_required_gate']}" not in top_state:
        errors.append("top-level NEXT_REQUIRED_GATE contradicts OL authority")
    if "OPERATOR_SURROGATE_AUTHORIZED_FOR_DA = false" not in top_state:
        errors.append("top-level DA authorization contradicts current programme")
    for gate in gates:
        path = gate["experiment_config"]
        if path != UNDECLARED and not (root / path).is_file():
            errors.append(f"missing experiment: {path}")
    for path in base.glob("*.md"):
        for match in re.findall(r"OL-G\d{2}_[A-Z_]+", path.read_text()):
            if match not in state["gates"]:
                errors.append(f"unknown gate reference {match}: {path.name}")
    return errors
