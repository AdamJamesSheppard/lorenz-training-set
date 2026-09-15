#!/usr/bin/env bash
set -euo pipefail

repo_dir=$(cd "$(dirname "$0")/.." && pwd)
stamp=$(date -u +%Y%m%dT%H%M%SZ)
run_dir="$repo_dir/runs/mfem-uniform-equivalence-gate/$stamp"
mkdir -p "$run_dir"

git -C "$repo_dir" rev-parse HEAD > "$run_dir/git_commit.txt"
cp "$repo_dir/experiments/mfem-uniform-equivalence-gate.yaml" "$run_dir/config.yaml"
{
  printf '{\n  "stage": "production_scale_operator_probe_running",\n'
  printf '  "cells": [30, 36, 36],\n  "mpi_ranks": 8,\n'
  printf '  "started_utc": "%s"\n}\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$run_dir/status.json"

if "$repo_dir/mfem/run_uniform_equivalence_probe.sh" 30 36 36 \
   > "$run_dir/operator_probe.log" 2>&1; then
  {
    printf '{\n  "stage": "production_scale_operator_probe_complete",\n'
    printf '  "cells": [30, 36, 36],\n  "mpi_ranks": 8,\n'
    printf '  "completed_utc": "%s"\n}\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } > "$run_dir/status.json"
else
  code=$?
  {
    printf '{\n  "stage": "production_scale_operator_probe_failed",\n'
    printf '  "exit_code": %d,\n  "completed_utc": "%s"\n}\n' \
      "$code" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } > "$run_dir/status.json"
  exit "$code"
fi
