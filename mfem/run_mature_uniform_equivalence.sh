#!/usr/bin/env bash
set -euo pipefail

repo_dir=$(cd "$(dirname "$0")/.." && pwd)
env_prefix=/home/adam/.local/share/mamba/envs/mfem-lorenz
pde_prefix=/home/adam/.local/share/mamba/envs/pde
stamp=$(date -u +%Y%m%dT%H%M%SZ)
run_dir="$repo_dir/runs/mfem-mature-uniform-equivalence/$stamp"
reference="$repo_dir/runs/local-q2-cn-full-spd-mature-bimodal/20260913T185157Z/mature_bimodal_q2_local_qp_30x36x36"
mixture="$repo_dir/runs/local-q2-cn-full-spd-mature-bimodal/20260913T185157Z/reference/mature_mixture.json"
mkdir -p "$run_dir/shared_initial" "$run_dir/mfem" "$repo_dir/build/mfem-physical-equivalence"
on_exit() {
  code=$?
  if [[ $code -ne 0 ]]; then
    printf '{"status":"FAILED_MFEM_MATURE_RUN","exit_code":%d}\n' "$code" > "$run_dir/status.json"
  fi
}
trap on_exit EXIT
cp "$repo_dir/experiments/mfem-mature-uniform-equivalence.yaml" "$run_dir/config.yaml"
git -C "$repo_dir" rev-parse HEAD > "$run_dir/git_commit.txt"
git -C "$repo_dir" status --short > "$run_dir/git_status.txt"
sha256sum "$mixture" "$reference/final_q2_subcell_averages.npy" > "$run_dir/input_sha256.txt"
printf '{"status":"CREATING_SHARED_INITIAL_STATE"}\n' > "$run_dir/status.json"

cd "$repo_dir"
./scripts/run-in-env mpiexec -n 8 python mfem/export_mature_initial.py \
  "$mixture" "$run_dir/shared_initial"

export PATH="$env_prefix/bin:$PATH"
"$env_prefix/bin/mpicxx" -std=c++17 -O2 \
  -I"$env_prefix/include" -I"$pde_prefix/include/osqp" \
  "$repo_dir/mfem/mfem_physical_equivalence.cpp" \
  -L"$env_prefix/lib" -L"$pde_prefix/lib" \
  -Wl,-rpath,"$env_prefix/lib" -Wl,-rpath,"$pde_prefix/lib" \
  -lmfem -lHYPRE -losqp \
  -o "$repo_dir/build/mfem-physical-equivalence/mfem_physical_equivalence"

printf '{"status":"RUNNING_MFEM_MATURE_TRAJECTORY","steps":320}\n' > "$run_dir/status.json"
"$env_prefix/bin/mpiexec" -n 8 \
  "$repo_dir/build/mfem-physical-equivalence/mfem_physical_equivalence" \
  mature 30 36 36 "$run_dir/shared_initial/initial_nodal_q2.bin" "$run_dir/mfem"

set +e
./scripts/run-in-env python mfem/compare_mature_equivalence.py "$run_dir" "$reference"
code=$?
set -e
if [[ $code -eq 0 ]]; then
  printf '{"status":"PASSED_PREDECLARED_MATURE_EQUIVALENCE_GATES"}\n' > "$run_dir/status.json"
else
  printf '{"status":"FAILED_PREDECLARED_MATURE_EQUIVALENCE_GATES","exit_code":%d}\n' "$code" > "$run_dir/status.json"
fi
printf '%s\n' "$run_dir"
exit "$code"
