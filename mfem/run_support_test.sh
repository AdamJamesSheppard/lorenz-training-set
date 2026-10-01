#!/usr/bin/env bash
set -euo pipefail
repo_dir=$(cd "$(dirname "$0")/.." && pwd)
env_prefix=/home/adam/.local/share/mamba/envs/mfem-lorenz
pde_prefix=/home/adam/.local/share/mamba/envs/pde
stamp=$(date -u +%Y%m%dT%H%M%SZ)
run_dir="$repo_dir/runs/mfem-support-sensitivity/$stamp"
first="$repo_dir/runs/mfem-static-amr-reproduction/20260916T221235Z"
mkdir -p "$run_dir/design" "$run_dir/mfem"
on_exit() {
  code=$?
  if [[ $code -ne 0 && ! -f "$run_dir/support_comparison.json" ]]; then
    printf '{"status":"FAILED_SUPPORT_PIPELINE","exit_code":%d}\n' "$code" > "$run_dir/status.json"
  fi
}
trap on_exit EXIT
cp "$repo_dir/experiments/mfem-support-sensitivity.yaml" "$run_dir/config.yaml"
git -C "$repo_dir" rev-parse HEAD > "$run_dir/git_commit.txt"
git -C "$repo_dir" status --short > "$run_dir/git_status.txt"
sha256sum "$repo_dir/mfem/prepare_support_test.py" "$repo_dir/mfem/compare_support_test.py" \
  "$repo_dir/build/mfem-physical-equivalence/mfem_physical_equivalence" \
  "$repo_dir/runs/mfem-static-amr-level2/20260922T231219Z/mfem/final_q2_subcell_averages.bin" \
  "$repo_dir/runs/mfem-static-amr-level3/20260923T181337Z/mfem/final_q2_subcell_averages.bin" \
  "$first/design/mixture_parameters.bin" > "$run_dir/input_sha256.txt"
printf '{"status":"PREPARING_SUPPORT_TEST"}\n' > "$run_dir/status.json"
"$pde_prefix/bin/python" -B "$repo_dir/mfem/prepare_support_test.py" "$repo_dir" "$run_dir/design"
export PATH="$env_prefix/bin:$PATH"
printf '{"status":"RUNNING_SUPPORT_TEST","steps":320}\n' > "$run_dir/status.json"
"$env_prefix/bin/mpiexec" -n 8 "$repo_dir/build/mfem-physical-equivalence/mfem_physical_equivalence" \
  amr2 45 54 54 "$run_dir/design/base_cell_marks.bin" "$run_dir/design/child_cell_marks.bin" \
  "$first/design/mixture_parameters.bin" "$run_dir/mfem"
set +e
"$pde_prefix/bin/python" -B "$repo_dir/mfem/compare_support_test.py" "$repo_dir" "$run_dir"
code=$?
set -e
if [[ $code -eq 0 ]]; then
  printf '{"status":"PASSED_SUPPORT_REPRODUCTION_GATES"}\n' > "$run_dir/status.json"
else
  printf '{"status":"FAILED_SUPPORT_REPRODUCTION_GATES","exit_code":%d}\n' "$code" > "$run_dir/status.json"
fi
printf '%s\n' "$run_dir"
exit "$code"
